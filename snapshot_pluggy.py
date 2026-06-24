"""
snapshot_pluggy.py — job batch (GitHub Actions) que puxa os saldos do dia
via Pluggy e grava nas tabelas de histórico do Supabase.

Replica a lógica de load_saldo_pluggy() do app.py, mas sem Streamlit:
- conta corrente  -> tabela `saldos`            (on_conflict="data,origem")
- caixinha (CDB)  -> tabela `caixinha_historico` (on_conflict="data")
- fatura cartão   -> tabela `fatura_historico`   (on_conflict="data")

Lê credenciais de variáveis de ambiente (GitHub Secrets), NÃO de st.secrets.
Idempotente: rodar 2x no mesmo dia só sobrescreve a linha do dia.
"""
from __future__ import annotations
import os
import sys
import json
import datetime

from supabase import create_client
from pluggy_client import PluggyClient


def _env(name: str) -> str:
    v = os.environ.get(name)
    if not v:
        sys.exit(f"[erro] variável de ambiente ausente: {name}")
    return v


def coletar_saldos(client: PluggyClient, item_ids: list[str]) -> dict:
    """Mesma lógica de load_saldo_pluggy() — sem cache, sem Streamlit."""
    resultado = {
        "conta": None,
        "caixinha": 0.0,
        "fatura_cartao": None,
        "atualizado_em": None,
    }

    for item_id in item_ids:
        for acc in client.get_accounts(item_id):
            acc_type = acc.get("type", "")
            subtype = acc.get("subtype", "")
            balance = acc.get("balance")
            updated = acc.get("updatedAt")

            if acc_type == "BANK" and subtype == "CHECKING_ACCOUNT":
                resultado["conta"] = balance
                if updated:
                    resultado["atualizado_em"] = updated
            elif acc_type == "CREDIT" and subtype == "CREDIT_CARD":
                resultado["fatura_cartao"] = balance

        investments = client._get("/investments", {"itemId": item_id}).get("results", [])
        for inv in investments:
            if inv.get("status") != "ACTIVE":
                continue
            valor = inv.get("amountWithdrawal") or inv.get("balance") or 0.0
            resultado["caixinha"] += valor

    return resultado


def main() -> None:
    client_id = _env("PLUGGY_CLIENT_ID")
    client_secret = _env("PLUGGY_CLIENT_SECRET")
    item_ids_raw = _env("PLUGGY_ITEM_ID")
    supabase_url = _env("SUPABASE_URL")
    supabase_key = _env("SUPABASE_KEY")

    # PLUGGY_ITEM_ID pode ser um id só ou um JSON array '["id1","id2"]'
    item_ids_raw = item_ids_raw.strip()
    if item_ids_raw.startswith("["):
        item_ids = json.loads(item_ids_raw)
    else:
        item_ids = [item_ids_raw]

    client = PluggyClient(client_id, client_secret)
    client.authenticate()

    saldos = coletar_saldos(client, item_ids)
    hoje = datetime.date.today().isoformat()

    sb = create_client(supabase_url, supabase_key)
    gravados = []

    # Conta corrente -> saldos
    if saldos["conta"] is not None:
        sb.table("saldos").upsert(
            {"data": hoje, "origem": "pluggy", "balamt": saldos["conta"]},
            on_conflict="data,origem",
        ).execute()
        gravados.append(f"conta={saldos['conta']:.2f}")

    # Caixinha -> caixinha_historico
    if saldos["caixinha"]:
        sb.table("caixinha_historico").upsert(
            {"data": hoje, "valor": saldos["caixinha"]},
            on_conflict="data",
        ).execute()
        gravados.append(f"caixinha={saldos['caixinha']:.2f}")

    # Fatura -> fatura_historico
    if saldos["fatura_cartao"] is not None:
        sb.table("fatura_historico").upsert(
            {"data": hoje, "valor": saldos["fatura_cartao"]},
            on_conflict="data",
        ).execute()
        gravados.append(f"fatura={saldos['fatura_cartao']:.2f}")

    if gravados:
        print(f"[ok] {hoje} — {', '.join(gravados)}")
    else:
        # Não é necessariamente erro (ex: API devolveu vazio), mas sinaliza
        print(f"[aviso] {hoje} — nenhum saldo coletado; verifique o item no Pluggy")


if __name__ == "__main__":
    main()
