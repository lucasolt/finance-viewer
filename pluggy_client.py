"""
pluggy_client.py — wrapper mínimo da Pluggy Data API para uso pessoal.

Fluxo: client_id/secret -> API key (2h) -> fetch accounts/transactions por itemId.
Não usa connect token (só necessário pro widget frontend).
"""
from __future__ import annotations
import requests
import pandas as pd

BASE = "https://api.pluggy.ai"


class PluggyClient:
    def __init__(self, client_id: str, client_secret: str, timeout: int = 30):
        self.client_id = client_id
        self.client_secret = client_secret
        self.timeout = timeout
        self._api_key: str | None = None

    # ---- auth ----
    def authenticate(self) -> str:
        r = requests.post(
            f"{BASE}/auth",
            json={"clientId": self.client_id, "clientSecret": self.client_secret},
            timeout=self.timeout,
        )
        r.raise_for_status()
        self._api_key = r.json()["apiKey"]
        return self._api_key

    @property
    def _headers(self) -> dict:
        if not self._api_key:
            self.authenticate()
        return {"X-API-KEY": self._api_key, "Accept": "application/json"}

    def _get(self, path: str, params: dict | None = None) -> dict:
        r = requests.get(f"{BASE}{path}", params=params or {},
                         headers=self._headers, timeout=self.timeout)
        # API key expira em 2h -> reautentica uma vez em 403/401
        if r.status_code in (401, 403):
            self.authenticate()
            r = requests.get(f"{BASE}{path}", params=params or {},
                             headers=self._headers, timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    # ---- item / accounts ----
    def get_item(self, item_id: str) -> dict:
        return self._get(f"/items/{item_id}")

    def get_accounts(self, item_id: str) -> list[dict]:
        return self._get("/accounts", {"itemId": item_id}).get("results", [])

   
    # ---- transactions (v2, cursor-based) ----
    def get_transactions(self, account_id: str, **filters):
        params = {"accountId": account_id}
        params.update(filters)

        out = []
        while True:
            data = self._get("/v2/transactions", params)
            out.extend(data.get("results", []))

            nxt = data.get("next")
            if not nxt:
                break
        # "next" vem como query string: "?accountId=xxx&after=yyy"
        # extrai só o valor do "after"
            from urllib.parse import parse_qs, urlparse
            parsed = parse_qs(urlparse(nxt).query if "?" in nxt else nxt.lstrip("?"))
            params["after"] = parsed["after"][0]

        return out


    def all_transactions(self, item_id: str, **filters) -> list[dict]:
        """Todas as transações de todas as contas do item."""
        txns = []
        for acc in self.get_accounts(item_id):
            for t in self.get_transactions(acc["id"], **filters):
                t["accountId"] = acc["id"]
                t["accountName"] = acc.get("name") or acc.get("marketingName")
                txns.append(t)
        return txns


# ---- helpers de DataFrame ----
def transactions_to_df(txns: list[dict]) -> pd.DataFrame:
    if not txns:
        return pd.DataFrame()
    df = pd.json_normalize(txns)
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
    keep = [c for c in ["id", "date", "description", "amount", "currencyCode",
                        "category", "type", "accountName", "accountId"]
            if c in df.columns]
    df = df[keep]
    return df.sort_values("date") if "date" in keep else df
