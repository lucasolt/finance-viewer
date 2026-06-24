import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from supabase import create_client
import io
import json

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="Gastos", page_icon="💸", layout="wide")

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@300;400;600&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }

[data-baseweb="slider"] [role="slider"] {
    background-color: #555 !important;
    border-color: #555 !important;
    box-shadow: none !important;
}
[data-baseweb="slider"] div[class*="Track"] > div:nth-child(2) {
    background-color: #444 !important;
}
[data-baseweb="slider"] div[class*="InnerTrack"] {
    background-color: #444 !important;
}
div[data-testid="stSlider"] div[class*="track"] {
    background: #444 !important;
}
.stApp { background-color: #0f0f0f; color: #e8e8e0; }
header[data-testid="stHeader"] { background: transparent; }
h1 { font-family: 'DM Mono', monospace !important; font-size: 1.6rem !important; color: #c8f060 !important; letter-spacing: -0.03em; margin-bottom: 0 !important; }
h2, h3 { font-family: 'DM Mono', monospace !important; color: #e8e8e0 !important; font-size: 0.95rem !important; text-transform: uppercase; letter-spacing: 0.08em; }
[data-testid="metric-container"] { background: #1a1a1a; border: 1px solid #2a2a2a; border-radius: 8px; padding: 1rem 1.2rem; }
[data-testid="metric-container"] label { color: #666 !important; font-size: 0.72rem !important; text-transform: uppercase; letter-spacing: 0.1em; font-family: 'DM Mono', monospace !important; }
[data-testid="metric-container"] [data-testid="stMetricValue"] { color: #c8f060 !important; font-family: 'DM Mono', monospace !important; font-size: 1.5rem !important; }
[data-testid="stFileUploadDropzone"] { background: #1a1a1a !important; border: 1px dashed #333 !important; border-radius: 8px !important; }
[data-testid="stFileUploadDropzone"]:hover { border-color: #c8f060 !important; }
[data-testid="stSelectbox"] > div > div, [data-testid="stMultiSelect"] > div > div { background: #1a1a1a !important; border-color: #2a2a2a !important; color: #e8e8e0 !important; }
[data-testid="stDataFrame"] { border: 1px solid #2a2a2a; border-radius: 8px; }
hr { border-color: #222 !important; }
[data-testid="stTabs"] button { font-family: 'DM Mono', monospace !important; font-size: 0.75rem !important; text-transform: uppercase; letter-spacing: 0.07em; color: #555 !important; }
[data-testid="stTabs"] button[aria-selected="true"] { color: #c8f060 !important; border-bottom-color: #c8f060 !important; }
[data-testid="stSidebar"] { background: #111 !important; border-right: 1px solid #1e1e1e; }
.upload-hint { color: #444; font-size: 0.8rem; font-family: 'DM Mono', monospace; margin-top: 0.5rem; }
.login-wrap { max-width: 360px; margin: 8rem auto; padding: 2.5rem; background: #1a1a1a; border: 1px solid #2a2a2a; border-radius: 12px; }
</style>
""", unsafe_allow_html=True)

# ── Color schemes ─────────────────────────────────────────────────────────────
COLOR_SCHEMES = {
    "Lima 🟢":      ["#c8f060","#60c8f0","#f060c8","#f0c860","#60f0c8","#c860f0","#f09060","#9060f0",
                     "#a8d040","#40a8d0","#d040a8","#d0a840","#40d0a8","#a840d0","#d07040","#7040d0"],
    "Lima Escuro 🌑": ["#8aaa20","#208aaa","#aa2088","#aaa820","#20aa88","#8820aa","#aa5020","#5020aa",
                     "#6a8a10","#106a8a","#8a1068","#8a8a10","#108a68","#681088","#8a3010","#301088"],
    "Neon 🔵":      ["#00f5ff","#ff006e","#ffbe0b","#8338ec","#3a86ff","#fb5607","#06d6a0","#ef476f",
                     "#00c8d4","#d4006e","#d4a000","#6a28cc","#2a66df","#db3500","#00b680","#cf274f"],
    "Pastel 🌸":    ["#ffb3c6","#bde0fe","#caffbf","#ffd6a5","#fdffb6","#c8b6ff","#a8dadc","#f4a261",
                     "#ff8fab","#90c2fd","#aff09f","#ffbb77","#fcff85","#a99bff","#80c8cc","#f08040"],
    "Mono ⬜":      ["#ffffff","#cccccc","#999999","#666666","#eeeeee","#bbbbbb","#888888","#555555",
                     "#dddddd","#aaaaaa","#777777","#444444","#f0f0f0","#c0c0c0","#909090","#606060"],
    "Fogo 🔴":      ["#ff4d4d","#ff8c00","#ffd700","#ff6b6b","#ff9a3c","#ffcc02","#e63946","#f4a261",
                     "#cc2222","#cc6a00","#ccaa00","#cc4444","#cc7820","#ccaa00","#b41824","#d07840"],
    "Oceano 🌊":    ["#0096c7","#00b4d8","#48cae4","#90e0ef","#ade8f4","#023e8a","#0077b6","#caf0f8",
                     "#007aaa","#0097b8","#28aace","#60c8d8","#8dd4e8","#012060","#005090","#aadcf0"],
    "Ardósia 🩶":   ["#94a3b8","#7c8fa3","#64748b","#a8b8c8","#b0bec5","#78909c","#90a4ae","#607d8b",
                     "#b4c4d8","#8ca0b8","#748498","#c0d0e0","#c8d4da","#90a8b0","#a8bcc4","#708898"],
    "Terra 🤎":     ["#a87c5a","#c4a882","#8b6347","#d4b896","#7a5c3e","#b89068","#967055","#c8a87a",
                     "#c89060","#dfc09a","#a07040","#e8caa8","#906840","#caa878","#b08060","#dab888"],
    "Sage 🌿":      ["#7a9e7e","#9ab89e","#5a8060","#b4c8b4","#6b8f6e","#88a88a","#4e7252","#a0b8a0",
                     "#8ab88e","#aacaae","#6a9070","#c4d8c4","#7ba07e","#98b89a","#5e8262","#b0c8b0"],
    "Chumbo 🌑":    ["#8892a0","#6e7a88","#a4aeb8","#545e6a","#b8c0c8","#404850","#7a8490","#c0c8d0",
                     "#98a2b0","#7e8e98","#b4bec8","#646e7a","#c8d0d8","#505860","#8a949e","#d0d8e0"],
}

CATEGORY_COLORS = {
    "iFood":                 "#cc2222",
    "Alimentação & Mercado": "#7a9e3e",
    "Telecom":               "#4a6fa5",
    "Compras":               "#b05ca0",
    "Serviços":              "#5b7a8c",
    "Outros":                "#6b6b6b",
    "Saúde":                 "#3f9e7a",
    "Assinaturas":           "#8a5fc4",
    "Transporte":            "#3f8fb5",
    "Vícios & Conveniência": "#c4923f",
    "Vestuário":             "#c46a8a",
    "Lazer":                 "#c46a3f",
    "Impostos":              "#9e3f3f",
    "Transferências":        "#7a8a99",
    "Profissional":          "#4a8a6a",
    "Investimento":          "#6a9e3f",
    "Bolsa Residência":      "#3f9e5c",
    "Pagamento de Fatura":   "#454545",
    "Crédito de Fatura":     "#555f55",
}

_FALLBACK_CYCLE = ["#8899aa", "#aa8899", "#99aa88", "#aa9988", "#8899cc", "#cc9988"]

def cat_color(categoria: str) -> str:
    if categoria in CATEGORY_COLORS:
        return CATEGORY_COLORS[categoria]
    return _FALLBACK_CYCLE[abs(hash(categoria)) % len(_FALLBACK_CYCLE)]

def cat_colors_list(categorias: list) -> list:
    return [cat_color(c) for c in categorias]


from pluggy_client import PluggyClient, transactions_to_df

@st.cache_resource
def get_pluggy():
    c = PluggyClient(st.secrets["pluggy"]["client_id"],
                     st.secrets["pluggy"]["client_secret"])
    c.authenticate()
    return c

def get_colors() -> list:
    return COLOR_SCHEMES.get(st.session_state.get("color_scheme", "Lima 🟢"), COLOR_SCHEMES["Lima 🟢"])

def get_accent() -> str:
    return get_colors()[0]

def build_plotly_theme() -> dict:
    return dict(
        paper_bgcolor="#0f0f0f", plot_bgcolor="#0f0f0f",
        font=dict(family="DM Sans", color="#e8e8e0", size=12),
        xaxis=dict(gridcolor="#1e1e1e", linecolor="#2a2a2a"),
        yaxis=dict(gridcolor="#1e1e1e", linecolor="#2a2a2a"),
        colorway=get_colors(),
    )

CATEGORY_MAP = {
    "ifd *zamp":"iFood","tabarcaria":"Vícios & Conveniência","trinca tabarcaria":"Vícios & Conveniência",
    "tabacariacapri":"Vícios & Conveniência","tabacaria":"Vícios & Conveniência",
    "havana revistaria e ta":"Vícios & Conveniência","cameron":"Vícios & Conveniência",
    "banca cafe":"Vícios & Conveniência","posto":"Vícios & Conveniência","combust":"Vícios & Conveniência",
    "alimentos":"Alimentação & Mercado","super apolo":"Alimentação & Mercado","zaffari":"Alimentação & Mercado",
    "mini mercado":"Alimentação & Mercado","companhiazaffari":"Alimentação & Mercado",
    "la brescia":"Alimentação & Mercado","armazem e fruteira":"Alimentação & Mercado",
    "themis restaurante":"Alimentação & Mercado","rappi":"Alimentação & Mercado",
    "mcdonalds":"Alimentação & Mercado","burger":"Alimentação & Mercado","subway":"Alimentação & Mercado",
    "padaria":"Alimentação & Mercado","supermercado":"Alimentação & Mercado","carrefour":"Alimentação & Mercado",
    "restaurante":"Alimentação & Mercado","lanche":"Alimentação & Mercado","pizza":"Alimentação & Mercado",
    "pão de açúcar":"Alimentação & Mercado","hot dog":"Alimentação & Mercado",
    "99":"Transporte","cabify":"Transporte","estacionamento":"Transporte","onibus":"Transporte",
    "metro":"Transporte","passagem":"Transporte","veppo cia":"Transporte",
    "panvel":"Saúde","sao joao farmacias":"Saúde","farmaciaosaojoao":"Saúde",
    "drogaria achutti":"Saúde","rd saude":"Saúde","bioterapica":"Saúde","m e pa clinica":"Saúde",
    "dr. central":"Saúde","rafael ramos amaral":"Saúde","farmacia":"Saúde","drogaria":"Saúde",
    "drogasil":"Saúde","ultrafarma":"Saúde","consulta":"Saúde","medico":"Saúde","clinica":"Saúde",
    "academia":"Saúde","raia":"Saúde","pague menos":"Saúde",
    "netflix":"Assinaturas","amazon prime":"Assinaturas","hbo":"Assinaturas","disney":"Assinaturas",
    "globoplay":"Assinaturas","tinder":"Assinaturas","claude":"Assinaturas","subscription":"Assinaturas",
    "telefonica brasil":"Telecom","conta vivo":"Telecom","vivo":"Telecom","claro":"Telecom","tim":"Telecom","oi":"Telecom",
    "casa do papel":"Compras","amazon":"Compras","mercado pago":"Compras","mercado livre":"Compras",
    "magalupay":"Compras","pichau":"Compras","pagali":"Compras","pagseguro international":"Compras",
    "pay2all":"Compras","nuvei do brasil":"Compras","americanas":"Compras","magazine":"Compras",
    "shopee":"Compras","aliexpress":"Compras","pagseguro tecnologia":"Compras",
    "h&m":"Vestuário","lupo":"Vestuário","hering":"Vestuário","renner":"Vestuário","riachuelo":"Vestuário","zara":"Vestuário",
    "cucko":"Lazer","ingresso com":"Lazer","steam":"Lazer","cinema":"Lazer","bar":"Lazer",
    "cerveja":"Lazer","territoriopub":"Lazer","plano pixel":"Lazer",
    "aplicação rdb":"Investimento","aplicacao rdb":"Investimento","rdb":"Investimento","cdb":"Investimento","tesouro":"Investimento",
    "conselho regional de psicologia":"Profissional","crp":"Profissional",
    "municipio de porto alegre":"Impostos","receita federal":"Impostos","iptu":"Impostos","ipva":"Impostos",
    "pagamento de fatura":"Pagamento de Fatura","pagamento recebido":"Crédito de Fatura",
}

PLUGGY_CAT_FALLBACK = {
    "Tax on financial operations":"Impostos","Transfers":"Transferências","Same person transfer":"Transferências",
    "Investments":"Investimento","Services":"Serviços","Digital services":"Assinaturas","Travel":"Lazer",
    "Hospital clinics and labs":"Saúde","Office supplies":"Compras","Electronics":"Compras","Clothing":"Vestuário",
    "Gas stations":"Vícios & Conveniência","Cinema, theater and concerts":"Lazer","Shopping":"Compras","Leisure":"Lazer",
}

@st.cache_data(ttl=60)
def load_date_overrides() -> pd.DataFrame:
    res = get_supabase().table("date_override").select("*").execute()
    if not res.data:
        return pd.DataFrame(columns=["descricao", "data_original", "data_corrigida", "motivo"])
    df = pd.DataFrame(res.data)
    df["data_original"]  = pd.to_datetime(df["data_original"]).dt.date
    df["data_corrigida"] = pd.to_datetime(df["data_corrigida"]).dt.date
    return df

def apply_date_overrides(df: pd.DataFrame, overrides: pd.DataFrame) -> pd.DataFrame:
    if overrides.empty or df.empty:
        return df
    df = df.copy()
    lookup = {
        (row["descricao"], row["data_original"]): row["data_corrigida"]
        for _, row in overrides.iterrows()
    }
    def resolve(row):
        key = (row["descricao"], row["data"].date())
        return pd.Timestamp(lookup[key]) if key in lookup else row["data"]
    df["data"] = df.apply(resolve, axis=1)
    df["mes"] = df["data"].dt.to_period("M").astype(str)  # <-- recalcula aqui
    return df

def fmt_brl(val: float) -> str:
    return f"R$ {abs(val):,.2f}".replace(",","X").replace(".",",").replace("X",".")

def fmt_brl_signed(val: float) -> str:
    sign = "- " if val < 0 else ""
    return f"{sign}R$ {abs(val):,.2f}".replace(",","X").replace(".",",").replace("X",".")

def df_to_xlsx(df: pd.DataFrame) -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)
    return buf.getvalue()

def guess_category(desc: str, valor: float = 0.0, pluggy_cat: str = None) -> str:
    import re
    d = desc.lower()
    if "pagamento de fatura" in d:
        return "Pagamento de Fatura"
    if ("transferência recebida" in d or "transferencia recebida" in d) and \
       "lucas oltramari" in d and 4500 <= abs(valor) <= 5000:
        return "Bolsa Residência"
    REGEX_MAP = [
        (r"^ifd\*","iFood"),(r"ifood","iFood"),(r"\buber\b","Transporte"),(r"uberride","Transporte"),
        (r"^dm \*","Assinaturas"),(r"\*spotify","Assinaturas"),(r"\bpub\b","Lazer"),
        (r"^pagamento recebido$","Crédito de Fatura"),
    ]
    for pattern, cat in REGEX_MAP:
        if re.search(pattern, d):
            return cat
    for kw, cat in sorted(CATEGORY_MAP.items(), key=lambda x: -len(x[0])):
        if kw in d:
            return cat
    if re.search(r"•{3}\.\d{3}\.\d{3}-•{2}", desc):
        return "Transferências"
    if pluggy_cat and pluggy_cat in PLUGGY_CAT_FALLBACK:
        return PLUGGY_CAT_FALLBACK[pluggy_cat]
    return "Outros"

def detectar_reembolsos(df: pd.DataFrame, janela_dias: int = 90) -> pd.DataFrame:
    import re as _re
    df = df.copy()
    df["reembolsado"] = False
    if df.empty:
        return df
    def extrai_doc(desc):
        m = _re.search(r"\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}", str(desc))
        if m: return m.group(0)
        m = _re.search(r"•{3}\.\d{3}\.\d{3}-•{2}", str(desc))
        return m.group(0) if m else None
    df["_doc"] = df["descricao"].apply(extrai_doc)
    df["_eh_reembolso"] = df["descricao"].str.lower().str.startswith("reembolso recebido")
    df["_eh_envio"] = df["descricao"].str.lower().str.startswith("transferência enviada")
    reembolsos = df[df["_eh_reembolso"] & df["_doc"].notna()]
    usados = set()
    for idx_r, reemb in reembolsos.iterrows():
        valor_abs = abs(reemb["valor"]); doc = reemb["_doc"]; data_r = reemb["data"]
        cand = df[df["_eh_envio"] & (df["_doc"]==doc) &
                  (df["valor"].abs().round(2)==round(valor_abs,2)) &
                  (abs((df["data"]-data_r).dt.days)<=janela_dias) &
                  (~df.index.isin(usados))]
        if not cand.empty:
            idx_envio = cand.index[0]
            df.at[idx_r,"reembolsado"] = True; df.at[idx_envio,"reembolsado"] = True
            usados.add(idx_r); usados.add(idx_envio)
    return df.drop(columns=["_doc","_eh_reembolso","_eh_envio"])

@st.cache_resource
def get_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

@st.cache_data(ttl=300)
def load_from_pluggy() -> pd.DataFrame:
    item_ids = st.secrets["pluggy"]["item_id"]
    if isinstance(item_ids, str): item_ids = [item_ids]
    client = get_pluggy()
    frames = []
    for item_id in item_ids:
        raw_txns = client.all_transactions(item_id)
        if raw_txns: frames.append(transactions_to_df(raw_txns))
    if not frames: return pd.DataFrame()
    df_raw = pd.concat(frames, ignore_index=True).drop_duplicates(subset=["id"])
    df = pd.DataFrame()
    df["data"] = pd.to_datetime(df_raw["date"], utc=True).dt.tz_localize(None)
    df["descricao"] = df_raw["description"]
    valor_brl = df_raw["amountInAccountCurrency"].fillna(df_raw["amount"]) if "amountInAccountCurrency" in df_raw.columns else df_raw["amount"]
    is_cartao = df_raw["accountName"].str.lower() == "platinum"
    df["valor"] = valor_brl.where(~is_cartao, -valor_brl)
    df["origem"] = is_cartao.map({True:"fatura",False:"extrato"})
    df["mes"] = df["data"].dt.to_period("M").astype(str)
    df["categoria"] = [guess_category(desc,val,pcat) for desc,val,pcat in zip(df["descricao"],df["valor"],df_raw["category"])]
    df["pluggy_id"] = df_raw["id"]; df["accountName"] = df_raw["accountName"]
    df = df.sort_values("data").reset_index(drop=True); df["id"] = df.index
    return df

@st.cache_data(ttl=300)
def load_from_supabase_historico(antes_de: pd.Timestamp) -> pd.DataFrame:
    sb = get_supabase(); corte = antes_de.strftime("%Y-%m-%d")
    all_rows = []; page_size = 1000; offset = 0
    while True:
        res = sb.table("transacoes").select("*").lt("data",corte).range(offset, offset+page_size-1).execute()
        if not res.data: break
        all_rows.extend(res.data)
        if len(res.data) < page_size: break
        offset += page_size
    if not all_rows: return pd.DataFrame()
    df = pd.DataFrame(all_rows)
    df["data"] = pd.to_datetime(df["data"]); df["mes"] = df["data"].dt.to_period("M").astype(str)
    df["categoria"] = df.apply(lambda r: guess_category(r["descricao"],r["valor"]), axis=1)
    if "reembolsado" not in df.columns: df["reembolsado"] = False
    df["fonte"] = "supabase"
    return df

def load_transactions():
    df_pluggy = load_from_pluggy()
    if df_pluggy.empty:
        df_hist = load_from_supabase_historico(pd.Timestamp("2100-01-01"))
        if df_hist.empty: return pd.DataFrame()
        df_hist["fonte"] = "supabase"
        return detectar_reembolsos(df_hist)
    pluggy_inicio = df_pluggy["data"].min(); df_pluggy["fonte"] = "pluggy"
    df_hist = load_from_supabase_historico(pluggy_inicio)
    if df_hist.empty:
        return detectar_reembolsos(df_pluggy)
    cols = ["data","descricao","valor","categoria","mes","origem","fonte"]
    df_hist_c = df_hist[[c for c in cols if c in df_hist.columns]].copy()
    df_plug_c = df_pluggy[[c for c in cols if c in df_pluggy.columns]].copy()
    df_combined = pd.concat([df_hist_c, df_plug_c], ignore_index=True).sort_values("data").reset_index(drop=True)
    return detectar_reembolsos(df_combined), pluggy_inicio, len(df_hist_c), len(df_plug_c)

@st.cache_data(ttl=300)
def load_saldo_pluggy() -> dict:
    item_ids = st.secrets["pluggy"]["item_id"]
    if isinstance(item_ids, str): item_ids = [item_ids]
    resultado = {"conta":None,"caixinha":0.0,"fatura_cartao":None,"atualizado_em":None,"caixinha_detalhe":[]}
    for item_id in item_ids:
        client = get_pluggy()
        for acc in client.get_accounts(item_id):
            t = acc.get("type",""); s = acc.get("subtype",""); b = acc.get("balance"); u = acc.get("updatedAt")
            if t=="BANK" and s=="CHECKING_ACCOUNT": resultado["conta"]=b; resultado["atualizado_em"]=resultado["atualizado_em"] or u
            elif t=="CREDIT" and s=="CREDIT_CARD": resultado["fatura_cartao"]=b
        for inv in client._get("/investments",{"itemId":item_id}).get("results",[]):
            if inv.get("status")!="ACTIVE": continue
            v = inv.get("amountWithdrawal") or inv.get("balance") or 0.0
            resultado["caixinha"] += v
            resultado["caixinha_detalhe"].append({"nome":inv.get("name","Investimento"),"tipo":inv.get("subtype",inv.get("type","")),"valor":v})
    return resultado

def save_saldo(data: str, info: dict, origem: str = "extrato"):
    row = {"data":data,"origem":origem}
    if info.get("balamt") is not None: row["balamt"] = info["balamt"]
    if info.get("rendimento_conta") is not None: row["rendimento_conta"] = info["rendimento_conta"]
    get_supabase().table("saldos").upsert(row, on_conflict="data,origem").execute()
    load_saldos.clear()

@st.cache_data(ttl=60)
def load_saldos() -> pd.DataFrame:
    res = get_supabase().table("saldos").select("*").execute()
    if not res.data: return pd.DataFrame(columns=["data","balamt","rendimento_conta","origem"])
    df = pd.DataFrame(res.data); df["data"] = pd.to_datetime(df["data"])
    if "rendimento_conta" not in df.columns: df["rendimento_conta"] = None
    if "rendimento_caixinha" not in df.columns: df["rendimento_caixinha"] = None
    return df.sort_values("data")

def load_prefs() -> dict:
    res = get_supabase().table("preferencias").select("*").execute()
    return {r["chave"]:r["valor"] for r in res.data} if res.data else {}

def save_pref(chave: str, valor: str):
    get_supabase().table("preferencias").upsert({"chave":chave,"valor":valor}, on_conflict="chave").execute()

_SENTINELA = "0001-01-01"

@st.cache_data(ttl=60)
def load_categoria_overrides() -> pd.DataFrame:
    res = get_supabase().table("categoria_overrides").select("*").execute()
    if not res.data: return pd.DataFrame(columns=["descricao","data","categoria"])
    df = pd.DataFrame(res.data); df["data"] = df["data"].astype(str)
    return df

def save_categoria_override(descricao: str, categoria: str, data_str=None):
    row = {"descricao":descricao,"categoria":categoria,"data":data_str if data_str else _SENTINELA}
    get_supabase().table("categoria_overrides").upsert(row, on_conflict="descricao,data").execute()
    load_categoria_overrides.clear()

def apply_categoria_overrides(df: pd.DataFrame, overrides: pd.DataFrame) -> pd.DataFrame:
    if overrides.empty or df.empty: return df
    df = df.copy(); df["_data_str"] = df["data"].dt.strftime("%Y-%m-%d")
    gerais = overrides[overrides["data"]==_SENTINELA].set_index("descricao")["categoria"].to_dict()
    especificos = {(r["descricao"],r["data"]):r["categoria"] for _,r in overrides[overrides["data"]!=_SENTINELA].iterrows()}
    def resolve(row):
        k = (row["descricao"],row["_data_str"])
        if k in especificos: return especificos[k]
        if row["descricao"] in gerais: return gerais[row["descricao"]]
        return row["categoria"]
    df["categoria"] = df.apply(resolve, axis=1)
    return df.drop(columns=["_data_str"])

# ── Login ─────────────────────────────────────────────────────────────────────
if "authed" not in st.session_state: st.session_state.authed = False
if not st.session_state.authed:
    st.markdown("<div class='login-wrap'>", unsafe_allow_html=True)
    st.title("💸 gastos")
    pwd = st.text_input("senha", type="password", label_visibility="collapsed", placeholder="senha")
    if st.button("entrar", width='stretch'):
        if pwd == st.secrets["APP_PASSWORD"]: st.session_state.authed = True; st.rerun()
        else: st.error("senha incorreta")
    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# ── Load data ─────────────────────────────────────────────────────────────────
try:
    result = load_transactions()
    if isinstance(result, tuple):
        df, _pluggy_inicio, _n_hist, _n_pluggy = result
        _load_debug = {"pluggy_inicio":_pluggy_inicio,"n_supabase":_n_hist,"n_pluggy":_n_pluggy,"n_total":len(df)}
    else:
        df = result; _load_debug = None
except Exception as e:
    st.error(f"Erro ao buscar dados: {e}"); import traceback; st.code(traceback.format_exc()); st.stop()

df_saldos = load_saldos(); saldo_pluggy = load_saldo_pluggy()
prefs = load_prefs(); df_cat_overrides = load_categoria_overrides()
df = apply_categoria_overrides(df, df_cat_overrides)

df_date_overrides = load_date_overrides()
df = apply_date_overrides(df, df_date_overrides)

def save_caixinha(data,valor): get_supabase().table("caixinha_historico").upsert({"data":data,"valor":valor},on_conflict="data").execute()
def save_fatura(data,valor): get_supabase().table("fatura_historico").upsert({"data":data,"valor":valor},on_conflict="data").execute()

@st.cache_data(ttl=300)
def load_caixinha_historico() -> pd.DataFrame:
    res = get_supabase().table("caixinha_historico").select("*").order("data").execute()
    if not res.data: return pd.DataFrame(columns=["data","valor"])
    df = pd.DataFrame(res.data); df["data"] = pd.to_datetime(df["data"]); return df

@st.cache_data(ttl=300)
def load_fatura_historico() -> pd.DataFrame:
    res = get_supabase().table("fatura_historico").select("*").order("data").execute()
    if not res.data: return pd.DataFrame(columns=["data","valor"])
    df = pd.DataFrame(res.data); df["data"] = pd.to_datetime(df["data"]); return df

if saldo_pluggy.get("conta") is not None and "saldo_pluggy_salvo" not in st.session_state:
    import datetime as _dt
    _hoje = _dt.date.today().isoformat()
    try:
        save_saldo(_hoje,{"balamt":saldo_pluggy["conta"]},"pluggy"); load_saldos.clear(); df_saldos = load_saldos()
        if saldo_pluggy.get("caixinha"): save_caixinha(_hoje,saldo_pluggy["caixinha"]); load_caixinha_historico.clear()
        if saldo_pluggy.get("fatura_cartao") is not None: save_fatura(_hoje,saldo_pluggy["fatura_cartao"]); load_fatura_historico.clear()
    except Exception: pass
    st.session_state["saldo_pluggy_salvo"] = True

df_caixinha_hist = load_caixinha_historico(); df_fatura_hist = load_fatura_historico()

# ── Prefs (first run) ─────────────────────────────────────────────────────────
if "prefs_loaded" not in st.session_state:
    if "color_scheme" in prefs: st.session_state["color_scheme"] = prefs["color_scheme"]
    if "cat_state" in prefs: st.session_state["cat_state"] = json.loads(prefs["cat_state"])
    if "tipo" in prefs: st.session_state["tipo_radio"] = prefs["tipo"]
    if "proj_base_range" in prefs:
        try: st.session_state["proj_base_range"] = tuple(json.loads(prefs["proj_base_range"]))
        except Exception: pass
    if "proj_ate_date" in prefs:
        try:
            import datetime as _dtp
            st.session_state["proj_ate_date"] = _dtp.date.fromisoformat(prefs["proj_ate_date"])
        except Exception: pass
    if "proj_saldo_ajuste" in prefs:
        try: st.session_state["proj_saldo_ajuste"] = float(prefs["proj_saldo_ajuste"])
        except Exception: pass
    # proj_nw_input NÃO é restaurado — sempre recalcula do início do mês
    st.session_state["prefs_loaded"] = True

# ── Header ────────────────────────────────────────────────────────────────────
col_h1, col_h2 = st.columns([5,1])
with col_h1:
    st.title("💸 controle de gastos")
    st.markdown("<p class='upload-hint'>dados sincronizados via Pluggy (Open Finance)</p>", unsafe_allow_html=True)
with col_h2:
    if st.button("🔄 atualizar", width='stretch'):
        load_from_pluggy.clear(); load_from_supabase_historico.clear()
        load_saldo_pluggy.clear(); load_caixinha_historico.clear(); load_fatura_historico.clear()
        st.rerun()
st.divider()

with st.expander("🔍 diagnóstico de fontes", expanded=False):
    if _load_debug:
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("Pluggy início",str(_load_debug["pluggy_inicio"].date()))
        c2.metric("Supabase (histórico)",_load_debug["n_supabase"])
        c3.metric("Pluggy (recente)",_load_debug["n_pluggy"])
        c4.metric("Total combinado",_load_debug["n_total"])
    else: st.info("Apenas uma fonte ativa.")
    if not df.empty and "fonte" in df.columns:
        pivot = df.groupby(["mes","fonte"]).size().unstack(fill_value=0).sort_index()
        st.dataframe(pivot, use_container_width=True)
        extremos = df.groupby("fonte")["data"].agg(["min","max"]).reset_index()
        extremos.columns = ["fonte","mais antiga","mais recente"]
        extremos["mais antiga"] = extremos["mais antiga"].dt.date
        extremos["mais recente"] = extremos["mais recente"].dt.date
        st.dataframe(extremos, use_container_width=True)

if df.empty:
    st.markdown("<div style='text-align:center;padding:4rem 0;color:#333;'><div style='font-size:3rem;'>📂</div><div style='font-family:DM Mono,monospace;font-size:0.85rem;margin-top:1rem;'>nenhum dado retornado pelo Pluggy ainda</div></div>", unsafe_allow_html=True)
    st.stop()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Aparência")
    scheme = st.selectbox("Esquema de cores", list(COLOR_SCHEMES.keys()), key="color_scheme")
    save_pref("color_scheme", scheme)
    st.divider()
    st.markdown("### Filtros")
    import datetime
    _min_date = df["data"].min().date(); _max_date = df["data"].max().date()
    PRESET_OPTS = ["Tudo","Últimos 12 meses","Este ano (YTD)","Este mês","Personalizado","Barra deslizante"]
    preset = st.selectbox("Período", PRESET_OPTS, index=5, key="date_preset")
    _meses_disp = sorted(df["mes"].unique())
    if preset=="Tudo": d_start,d_end = _min_date,_max_date
    elif preset=="Últimos 12 meses":
        d_end=_max_date
        try: d_start=d_end.replace(year=d_end.year-1)
        except ValueError: d_start=d_end.replace(year=d_end.year-1,day=28)
        d_start=max(d_start,_min_date)
    elif preset=="Este ano (YTD)": d_start=max(datetime.date(_max_date.year,1,1),_min_date); d_end=_max_date
    elif preset=="Este mês": d_start=max(datetime.date(_max_date.year,_max_date.month,1),_min_date); d_end=_max_date
    elif preset=="Barra deslizante":
        _sel=st.session_state.get("range_slider",(_meses_disp[0],_meses_disp[-1]))
        d_start=max(pd.Period(_sel[0],freq="M").start_time.date(),_min_date)
        d_end=min(pd.Period(_sel[-1],freq="M").end_time.date(),_max_date)
        st.caption("↓ use a barra abaixo do gráfico")
    else:
        c_ini,c_fim = st.columns(2)
        d_start=c_ini.date_input("De",value=_min_date,min_value=_min_date,max_value=_max_date,key="date_custom_start")
        d_end=c_fim.date_input("Até",value=_max_date,min_value=_min_date,max_value=_max_date,key="date_custom_end")
        if d_start>d_end: d_start,d_end=d_end,d_start
    _tipo_opts=["Gastos","Receitas","Tudo"]
    _tipo_idx=_tipo_opts.index(st.session_state.get("tipo_radio","Gastos")) if st.session_state.get("tipo_radio") in _tipo_opts else 0
    tipo=st.radio("Tipo",_tipo_opts,index=_tipo_idx); save_pref("tipo",tipo)
    st.markdown("### Categorias")
    cats=sorted(df["categoria"].unique())
    EXCLUDED_BY_DEFAULT={"Pagamento de Fatura","Crédito de Fatura","Investimento"}
    if "cat_state" not in st.session_state: st.session_state.cat_state={}
    for c in cats:
        if c not in st.session_state.cat_state: st.session_state.cat_state[c]=c not in EXCLUDED_BY_DEFAULT
    col_a,col_b,col_c=st.columns(3)
    if col_a.button("✓ Tudo",width='stretch'):
        for c in cats: st.session_state[f"cat_{c}"]=True; st.session_state.cat_state[c]=True
        save_pref("cat_state",json.dumps(st.session_state.cat_state)); st.rerun()
    if col_b.button("◎ Padrão",width='stretch'):
        for c in cats: v=c not in EXCLUDED_BY_DEFAULT; st.session_state[f"cat_{c}"]=v; st.session_state.cat_state[c]=v
        save_pref("cat_state",json.dumps(st.session_state.cat_state)); st.rerun()
    if col_c.button("✗ Nada",width='stretch'):
        for c in cats: st.session_state[f"cat_{c}"]=False; st.session_state.cat_state[c]=False
        save_pref("cat_state",json.dumps(st.session_state.cat_state)); st.rerun()
    cats_sel=[]
    for c in cats:
        checked=st.checkbox(c,value=st.session_state.cat_state[c],key=f"cat_{c}")
        st.session_state.cat_state[c]=checked
        if checked: cats_sel.append(c)
    save_pref("cat_state",json.dumps({k:v for k,v in st.session_state.cat_state.items()}))
    st.divider()
    if "confirm_delete" not in st.session_state: st.session_state.confirm_delete=False
    if not st.session_state.confirm_delete:
        if st.button("🗑 Apagar dados de saldo"): st.session_state.confirm_delete=True; st.rerun()
    else:
        st.warning("Tem certeza? Isso apaga os saldos (transações vêm do Pluggy).")
        col_c,col_d=st.columns(2)
        if col_c.button("✓ Sim",width='stretch'):
            get_supabase().table("saldos").delete().neq("id",0).execute()
            load_saldos.clear(); st.session_state.confirm_delete=False; st.rerun()
        if col_d.button("✗ Não",width='stretch'): st.session_state.confirm_delete=False; st.rerun()
    if st.button("🚪 Sair"): st.session_state.authed=False; st.rerun()

# ── Filter ────────────────────────────────────────────────────────────────────
import datetime as _dt
mask_data=(df["data"].dt.date>=d_start)&(df["data"].dt.date<=d_end)
dff_tabela=df[mask_data&df["categoria"].isin(cats_sel)].copy()
dff=dff_tabela[~dff_tabela["reembolsado"]].copy()
if tipo=="Gastos": dff=dff[dff["valor"]<0]
elif tipo=="Receitas": dff=dff[dff["valor"]>0]
dff["valor_abs"]=dff["valor"].abs()
dff_total=dff_tabela[~dff_tabela["reembolsado"]].copy()

# ── KPIs ──────────────────────────────────────────────────────────────────────
gastos=dff_total[dff_total["valor"]<0]["valor"].sum()
receitas=dff_total[dff_total["valor"]>0]["valor"].sum()
saldo=gastos+receitas
_pluggy_conta=saldo_pluggy.get("conta"); _pluggy_caixinha=saldo_pluggy.get("caixinha",0.0)
_pluggy_fatura=saldo_pluggy.get("fatura_cartao"); _pluggy_updated=saldo_pluggy.get("atualizado_em")
caixinha_mask=df["descricao"].str.lower().str.contains("aplicação rdb|aplicacao rdb|resgate rdb",na=False)
saldo_caixinha_txns=-df[caixinha_mask]["valor"].sum()
if _pluggy_conta is not None:
    balamt_recente=_pluggy_conta; saldo_caixinha=_pluggy_caixinha
    networth=balamt_recente+saldo_caixinha-(_pluggy_fatura or 0); networth_label=fmt_brl(networth); _saldo_fonte="pluggy"
elif not df_saldos.empty:
    balamt_recente=float(df_saldos.sort_values("data").iloc[-1]["balamt"]); saldo_caixinha=saldo_caixinha_txns
    networth=balamt_recente+saldo_caixinha; networth_label=fmt_brl(networth); _saldo_fonte="supabase"
else:
    balamt_recente=None; saldo_caixinha=saldo_caixinha_txns; networth_label="—"; _saldo_fonte=None

c1,c2,c3=st.columns(3)
c1.metric("Networth aprox.",networth_label)
c2.metric("Conta",fmt_brl(balamt_recente) if balamt_recente is not None else "—")
c3.metric("Caixinha",fmt_brl(saldo_caixinha))
st.markdown(f"""<div style='display:flex;gap:1.5rem;margin:0.3rem 0 0.2rem;flex-wrap:wrap;'>
<div style='color:#555;font-size:0.78rem;font-family:DM Mono,monospace;'>gasto no período: <span style='color:#ff8a8a'>{fmt_brl(gastos)}</span></div>
<div style='color:#555;font-size:0.78rem;font-family:DM Mono,monospace;'>recebido no período: <span style='color:#a8e063'>{fmt_brl(receitas)}</span></div>
<div style='color:#555;font-size:0.78rem;font-family:DM Mono,monospace;'>saldo período: <span style='color:#e8e8e0'>{fmt_brl_signed(saldo)}</span></div>
<div style='color:#555;font-size:0.78rem;font-family:DM Mono,monospace;'>{len(dff_total)} transações</div></div>""", unsafe_allow_html=True)
if _saldo_fonte or _pluggy_fatura is not None:
    _at=f"<div style='color:#555;font-size:0.75rem;font-family:DM Mono,monospace;'>🕐 atualizado: <span style='color:#e8e8e0'>{str(_pluggy_updated)[:10]}</span></div>" if _pluggy_updated else (f"<div style='color:#555;font-size:0.75rem;font-family:DM Mono,monospace;'>📅 saldo em: <span style='color:#e8e8e0'>{str(df_saldos.sort_values('data').iloc[-1]['data'].date())}</span></div>" if not df_saldos.empty else "")
    _ft=f"<div style='color:#555;font-size:0.75rem;font-family:DM Mono,monospace;'>💳 fatura: <span style='color:#ff6b6b'>{fmt_brl(_pluggy_fatura)}</span></div>" if _pluggy_fatura is not None else ""
    st.markdown(f"<div style='display:flex;gap:1.5rem;margin:0.5rem 0 0.2rem;flex-wrap:wrap;'>{_ft}{_at}</div>", unsafe_allow_html=True)
st.divider()

# ── Tabs principais ───────────────────────────────────────────────────────────
tab1,tab2,tab3,tab4=st.tabs(["Por mês","Por categoria","Evolução","Transações"])

with tab1:
    if dff.empty: st.info("Nenhum dado no período.")
    elif tipo=="Tudo":
        # Substitui o bloco inteiro dentro de `elif tipo == "Tudo":` no tab1
        meses_u = sorted(dff["mes"].unique())
        rec_mes = dff[dff["valor"] > 0].groupby("mes")["valor"].sum().reindex(meses_u, fill_value=0)
        gas_mes = dff[dff["valor"] < 0].groupby("mes")["valor"].sum().abs().reindex(meses_u, fill_value=0)
        sal_mes = rec_mes - gas_mes  # saldo real (positivo = sobrou, negativo = gastou mais)

        colors = get_colors()
        fig = go.Figure()

        # Receitas — barra verde sólida
        fig.add_bar(
            x=meses_u, y=rec_mes.values, name="Receitas",
            marker_color=colors[0], marker_line_width=0,
            hovertemplate="<b>%{x}</b><br>Receita: R$ %{y:,.2f}<extra></extra>",
        )    

    # Gastos — barra vermelha hachurrada, sobreposta (valor absoluto)
        fig.add_bar(
            x=meses_u, y=gas_mes.values, name="Gastos",
            marker=dict(
                color="rgba(220, 50, 50, 0.5)",
                line=dict(color="#ff4444", width=1.5),
                #color="rgba(180, 40, 40, 0.9)",
                #pattern=dict(shape="/", fgcolor="#ff4444", fgopacity=0.9, size=12, solidity=0.2),
                #line=dict(color="#cc3333", width=1.5),
        ),
        hovertemplate="<b>%{x}</b><br>Gasto: R$ %{y:,.2f}<extra></extra>",
        )

        # Linha de saldo
        fig.add_scatter(
        x=meses_u, y=sal_mes.values, name="Saldo",
        mode="lines+markers", line=dict(color=colors[1], width=2),
        marker=dict(size=6),
        hovertemplate="<b>%{x}</b><br>Saldo: R$ %{y:,.2f}<extra></extra>",
        )

        fig.add_hline(y=0, line_color="#333", line_width=1)
        fig.update_layout(
        **build_plotly_theme(), height=420, bargap=0.25, barmode="overlay",
        xaxis_title=None, yaxis_title="R$",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, font=dict(size=11)),
        )
        st.plotly_chart(fig, width='stretch')

        _tbl = pd.DataFrame({
            "Mês": meses_u,
            "Receitas": rec_mes.values,
            "Gastos": gas_mes.values,
            "Saldo": sal_mes.values,
        })
        st.download_button("⬇ baixar tabela (.xlsx)", df_to_xlsx(_tbl), "por_mes.xlsx",
                   "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                   use_container_width=True)
    else:
        bar_color = "#cc2222" if tipo == "Gastos" else get_accent()
        por_mes=dff.groupby("mes")["valor_abs"].sum().reset_index().sort_values("mes")
        fig=go.Figure()
        fig.add_bar(x=por_mes["mes"],y=por_mes["valor_abs"],marker_color=bar_color,marker_line_width=0,hovertemplate="<b>%{x}</b><br>R$ %{y:,.2f}<extra></extra>")
        fig.update_layout(**build_plotly_theme(),height=380,bargap=0.3,xaxis_title=None,yaxis_title="R$",showlegend=False)
        st.plotly_chart(fig,width='stretch')
        st.download_button("⬇ baixar tabela (.xlsx)",df_to_xlsx(por_mes.rename(columns={"mes":"Mês","valor_abs":"Valor"})),"por_mes.xlsx","application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",use_container_width=True)
        st.markdown(f"<p style='color:#555;font-size:0.8rem;font-family:DM Mono,monospace;'>média mensal: <span style='color:{get_accent()}'>{fmt_brl(por_mes['valor_abs'].mean())}</span></p>",unsafe_allow_html=True)

with tab2:
    if dff.empty: st.info("Nenhum dado no período.")
    elif tipo=="Tudo":
        rec_cat=dff[dff["valor"]>0].groupby("categoria")["valor"].sum().rename("Receita")
        gas_cat=dff[dff["valor"]<0].groupby("categoria")["valor"].sum().abs().rename("Gasto")
        por_cat_tudo=pd.concat([rec_cat,gas_cat],axis=1).fillna(0).reset_index().sort_values("Gasto",ascending=False)
        colors=get_colors(); fig_bar=go.Figure()
        fig_bar.add_bar(y=por_cat_tudo["categoria"],x=por_cat_tudo["Gasto"],name="Gastos",orientation="h",marker_color=colors[2],hovertemplate="<b>%{y}</b><br>Gasto: R$ %{x:,.2f}<extra></extra>")
        fig_bar.add_bar(y=por_cat_tudo["categoria"],x=por_cat_tudo["Receita"],name="Receitas",orientation="h",marker_color=colors[0],hovertemplate="<b>%{y}</b><br>Receita: R$ %{x:,.2f}<extra></extra>")
        fig_bar.update_layout(**build_plotly_theme(),height=420,barmode="group",xaxis_title="R$",yaxis_title=None,legend=dict(orientation="h",yanchor="bottom",y=1.02,font=dict(size=11)))
        st.plotly_chart(fig_bar,width='stretch')
    else:
        por_cat=dff.groupby("categoria")["valor_abs"].sum().reset_index().sort_values("valor_abs",ascending=False)
        col_a,col_b=st.columns(2)
        with col_a:
            fig_bar=go.Figure()
            fig_bar.add_bar(x=por_cat["valor_abs"],y=por_cat["categoria"],orientation="h",marker_color=cat_colors_list(por_cat["categoria"].tolist()),marker_line_width=0,hovertemplate="<b>%{y}</b><br>R$ %{x:,.2f}<extra></extra>")
            fig_bar.update_layout(**build_plotly_theme(),height=380,xaxis_title="R$",yaxis_title=None,showlegend=False)
            st.plotly_chart(fig_bar,width='stretch')
        with col_b:
            fig_pie=px.pie(por_cat,values="valor_abs",names="categoria",hole=0.55,color="categoria",color_discrete_map=CATEGORY_COLORS)
            fig_pie.update_traces(textfont_size=11,hovertemplate="<b>%{label}</b><br>R$ %{value:,.2f}<br>%{percent}<extra></extra>")
            fig_pie.update_layout(**build_plotly_theme(),height=380,showlegend=True,legend=dict(font=dict(size=11)))
            st.plotly_chart(fig_pie,width='stretch')

with tab3:
    if dff.empty: st.info("Nenhum dado no período.")
    elif tipo=="Tudo":
        meses_u=sorted(dff["mes"].unique())
        gas_cat=dff[dff["valor"]<0].groupby(["mes","categoria"])["valor"].sum().reset_index().sort_values("mes")
        gas_cat["valor_abs"]=gas_cat["valor"].abs()
        rec_cat=dff[dff["valor"]>0].groupby(["mes","categoria"])["valor"].sum().reset_index().sort_values("mes")
        gas_order=gas_cat.groupby("categoria")["valor_abs"].median().sort_values(ascending=False).index.tolist()
        fig_ev=go.Figure()
        for cat in gas_order:
            sub=gas_cat[gas_cat["categoria"]==cat]
            fig_ev.add_bar(x=sub["mes"],y=-sub["valor_abs"],name=f"↓ {cat}",marker_color=cat_color(cat),opacity=0.85,hovertemplate=f"<b>%{{x}}</b><br>{cat}<br>R$ %{{customdata:,.2f}}<extra></extra>",customdata=sub["valor_abs"])
        for cat in rec_cat["categoria"].unique():
            sub=rec_cat[rec_cat["categoria"]==cat]
            fig_ev.add_bar(x=sub["mes"],y=sub["valor"],name=f"↑ {cat}",marker_color=cat_color(cat),opacity=0.6,hovertemplate=f"<b>%{{x}}</b><br>{cat}<br>R$ %{{y:,.2f}}<extra></extra>")
        fig_ev.add_hline(y=0,line_color="#444",line_width=1)
        fig_ev.update_layout(**build_plotly_theme(),height=460,bargap=0.2,barmode="relative",legend=dict(orientation="h",yanchor="bottom",y=1.02,font=dict(size=10)))
        st.plotly_chart(fig_ev,width='stretch')
    else:
        por_mes_cat=dff.groupby(["mes","categoria"])["valor_abs"].sum().reset_index().sort_values("mes")
        meses_u=sorted(por_mes_cat["mes"].unique())
        cat_order=por_mes_cat.groupby("categoria")["valor_abs"].median().sort_values(ascending=False).index.tolist()
        fig_ev=go.Figure()
        for cat in cat_order:
            sub=pd.DataFrame({"mes":meses_u}).merge(por_mes_cat[por_mes_cat["categoria"]==cat][["mes","valor_abs"]],on="mes",how="left").fillna(0)
            fig_ev.add_bar(x=sub["mes"],y=sub["valor_abs"],name=cat,marker_color=cat_color(cat),hovertemplate=f"<b>%{{x}}</b><br>{cat}<br>R$ %{{y:,.2f}}<extra></extra>")
        fig_ev.update_layout(**build_plotly_theme(),height=420,bargap=0.25,barmode="stack",legend=dict(orientation="h",yanchor="bottom",y=1.02,font=dict(size=11)))
        st.plotly_chart(fig_ev,width='stretch')

with tab4:
    if tipo=="Gastos": show_raw=dff_tabela[dff_tabela["valor"]<0].copy()
    elif tipo=="Receitas": show_raw=dff_tabela[dff_tabela["valor"]>0].copy()
    else: show_raw=dff_tabela.copy()
    _cols_raw=["data","descricao","categoria","valor","origem","reembolsado"]
    if "fonte" in show_raw.columns: _cols_raw=["data","descricao","categoria","valor","origem","fonte","reembolsado"]
    show_raw=show_raw[_cols_raw].sort_values("data",ascending=False).reset_index(drop=True)
    show=show_raw.copy(); show["valor_fmt"]=show["valor"].map(fmt_brl_signed)
    show_display=show.drop(columns=["valor"]).rename(columns={"data":"Data","descricao":"Descrição","categoria":"Categoria","valor_fmt":"Valor","origem":"Origem"})
    def style_row(row):
        if row["reembolsado"]: return ["color: #555"]*len(row)
        styles=[""]*len(row); val_idx=list(row.index).index("Valor")
        styles[val_idx]="color: #ff6b6b" if str(row["Valor"]).startswith("- ") else "color: #a8e063"
        return styles
    styled=show_display.style.apply(style_row,axis=1).hide(axis="columns",subset=["reembolsado"])
    st.dataframe(styled,width='stretch',height=400)
    n_reemb=show_raw["reembolsado"].sum()
    if n_reemb>0: st.markdown(f"<p style='color:#555;font-size:0.75rem;font-family:DM Mono,monospace;'>{n_reemb} transação(ões) em cinza = reembolso casado, neutralizado dos cálculos</p>",unsafe_allow_html=True)
    st.download_button("⬇ baixar transações (.xlsx)",df_to_xlsx(show_raw.rename(columns={"data":"Data","descricao":"Descrição","categoria":"Categoria","valor":"Valor","origem":"Origem","fonte":"Fonte","reembolsado":"Reembolsado"})),"transacoes.xlsx","application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",use_container_width=True)
    st.markdown("---"); st.markdown("### ✏️ editar categoria")
    todas_cats=sorted(CATEGORY_COLORS.keys())
    if show_raw.empty: st.info("Nenhuma transação para exibir.")
    else:
        def _row_label(i,row):
            data_str=row["data"].strftime("%d/%m/%y") if hasattr(row["data"],"strftime") else str(row["data"])[:10]
            return f"{data_str} · {str(row['descricao'])[:40]} · {fmt_brl_signed(row['valor'])} · [{row['categoria']}]"
        opcoes_labels=[_row_label(i,r) for i,r in show_raw.iterrows()]
        opcoes_map={lbl:i for i,lbl in enumerate(opcoes_labels)}
        sel_label=st.selectbox("selecione a transação",options=opcoes_labels,index=0,key="tab4_sel_txn",label_visibility="collapsed")
        sel_idx=opcoes_map[sel_label]; sel_row=show_raw.iloc[sel_idx]
        desc_sel=sel_row["descricao"]; data_sel=sel_row["data"].strftime("%Y-%m-%d")
        cat_atual=sel_row["categoria"]; n_iguais=(show_raw["descricao"]==desc_sel).sum()
        col_cat,col_b1,col_b2=st.columns([3,1,1])
        with col_cat:
            nova_cat=st.selectbox("nova categoria",options=todas_cats,index=todas_cats.index(cat_atual) if cat_atual in todas_cats else 0,key="tab4_nova_cat",label_visibility="collapsed")
        with col_b1: btn_esta=st.button("✅ só esta",use_container_width=True,key="btn_esta_txn")
        with col_b2:
            lbl_todas=f"🔁 todas ({n_iguais})" if n_iguais>1 else "🔁 todas"
            btn_todas=st.button(lbl_todas,use_container_width=True,key="btn_todas_txn",disabled=(nova_cat==cat_atual))
        if btn_esta:
            if nova_cat==cat_atual: st.info("Categoria já é essa.")
            else:
                try: save_categoria_override(desc_sel,nova_cat,data_str=data_sel); st.success(f"Categoria desta transação → **{nova_cat}**"); load_categoria_overrides.clear(); st.rerun()
                except Exception as _e: st.error(f"Erro ao salvar: {_e}")
        if btn_todas:
            try: save_categoria_override(desc_sel,nova_cat,data_str=None); st.success(f"Todas as transações '{desc_sel[:40]}' → **{nova_cat}**"); load_categoria_overrides.clear(); st.rerun()
            except Exception as _e: st.error(f"Erro ao salvar: {_e}")
        if not df_cat_overrides.empty:
            ov_desc=df_cat_overrides[df_cat_overrides["descricao"]==desc_sel]
            if not ov_desc.empty:
                with st.expander(f"overrides ativos para '{desc_sel[:40]}'",expanded=False):
                    for _,ov in ov_desc.iterrows():
                        escopo=f"data {ov['data']}" if ov["data"]!=_SENTINELA else "todas"
                        st.markdown(f"<span style='color:#888;font-size:0.8rem;font-family:DM Mono,monospace'>{escopo} → <b style='color:#c8f060'>{ov['categoria']}</b></span>",unsafe_allow_html=True)
        with st.expander("🔍 debug overrides",expanded=False):
            st.dataframe(df_cat_overrides); st.write(f"`{desc_sel}` / sentinela `{_SENTINELA}`")
            if not df_cat_overrides.empty: st.write("match sentinela:",(df_cat_overrides["data"]==_SENTINELA).tolist())
            st.dataframe(df[df["descricao"]==desc_sel][["data","descricao","categoria"]].head(10))

# ── Barra deslizante ──────────────────────────────────────────────────────────
if preset=="Barra deslizante" and len(_meses_disp)>1:
    st.select_slider("Arraste para definir o período",options=_meses_disp,value=st.session_state.get("range_slider",(_meses_disp[0],_meses_disp[-1])),key="range_slider")

# ── Patrimônio ────────────────────────────────────────────────────────────────
st.divider()
st.markdown("<p style='color:#555;font-size:0.75rem;font-family:DM Mono,monospace;text-transform:uppercase;letter-spacing:0.08em;'>Evolução do patrimônio</p>",unsafe_allow_html=True)

if df_saldos.empty:
    st.info("Nenhum dado de saldo ainda.")
else:
    colors=get_colors()
    saldos_sorted=df_saldos.sort_values("data").copy()
    if not df_caixinha_hist.empty:
        saldos_sorted=saldos_sorted.merge(df_caixinha_hist[["data","valor"]].rename(columns={"valor":"caixinha"}),on="data",how="left")
        saldos_sorted["caixinha"]=saldos_sorted["caixinha"].fillna(0.0)
    else:
        cx_txns=df[df["descricao"].str.lower().str.contains("aplicação rdb|aplicacao rdb|resgate rdb",na=False)].sort_values("data").copy()
        if not cx_txns.empty:
            cx_txns["caixinha_acum"]=(-cx_txns["valor"]).cumsum()
            def caixinha_em(d): antes=cx_txns[cx_txns["data"]<=d]; return float(antes["caixinha_acum"].iloc[-1]) if not antes.empty else 0.0
            saldos_sorted["caixinha"]=saldos_sorted["data"].apply(caixinha_em)
        else: saldos_sorted["caixinha"]=0.0
    if not df_fatura_hist.empty:
        saldos_sorted=saldos_sorted.merge(df_fatura_hist[["data","valor"]].rename(columns={"valor":"fatura"}),on="data",how="left")
        saldos_sorted["fatura"]=saldos_sorted["fatura"].fillna(0.0)
    else: saldos_sorted["fatura"]=0.0
    saldos_sorted["networth"]=saldos_sorted["balamt"]+saldos_sorted["caixinha"]-saldos_sorted["fatura"]

    if _pluggy_conta is not None:
        import datetime as _dt2
        _hoje_ts=pd.Timestamp(_dt2.date.today())
        _ponto_atual=pd.DataFrame([{"data":_hoje_ts,"balamt":_pluggy_conta,"caixinha":_pluggy_caixinha,
                                     "fatura":_pluggy_fatura or 0.0,"networth":_pluggy_conta+_pluggy_caixinha-(_pluggy_fatura or 0),
                                     "rendimento_conta":None,"origem":"pluggy"}])
        saldos_sorted=pd.concat([saldos_sorted,_ponto_atual],ignore_index=True)
        saldos_sorted=saldos_sorted.drop_duplicates(subset=["data"],keep="last").sort_values("data")

    # Networth no início do mês atual — ponto de partida da projeção
    import datetime as _dt3
    _hoje_d=_dt3.date.today(); _inicio_mes=pd.Timestamp(_hoje_d.replace(day=1))
    _antes_mes=saldos_sorted[saldos_sorted["data"]<_inicio_mes]
    if not _antes_mes.empty and _antes_mes["networth"].notna().any():
        _nw_inicio_mes=float(_antes_mes["networth"].dropna().iloc[-1])
        _nw_inicio_label=f"01/{_hoje_d.strftime('%m/%Y')}"
    else:
        _nw_inicio_mes=float(saldos_sorted["networth"].dropna().iloc[-1]) if saldos_sorted["networth"].notna().any() else 0.0
        _nw_inicio_label="networth atual (sem dado anterior ao mês)"

    nw_tab1,nw_tab2,nw_tab3=st.tabs(["Evolução","Projeção","Rendimento acumulado"])

    # ── Evolução histórica ────────────────────────────────────────────────────
    with nw_tab1:
        fig_nw=go.Figure()
        fig_nw.add_scatter(x=saldos_sorted["data"],y=saldos_sorted["networth"],name="Networth",mode="lines+markers",
                           line=dict(color=colors[0],width=2),marker=dict(size=6),
                           hovertemplate="<b>%{x|%Y-%m-%d}</b><br>Networth: R$ %{y:,.2f}<extra></extra>",
                           fill="tozeroy",fillcolor="rgba(200,240,96,0.15)")
        fig_nw.add_scatter(x=saldos_sorted["data"],y=saldos_sorted["balamt"],name="Conta",mode="lines+markers",
                           line=dict(color=colors[1],width=2,dash="dot"),marker=dict(size=5),
                           hovertemplate="<b>%{x|%Y-%m-%d}</b><br>Conta: R$ %{y:,.2f}<extra></extra>")
        if saldos_sorted["caixinha"].sum()!=0:
            fig_nw.add_scatter(x=saldos_sorted["data"],y=saldos_sorted["caixinha"],name="Caixinha",mode="lines+markers",
                               line=dict(color=colors[2],width=2,dash="dash"),marker=dict(size=5),
                               hovertemplate="<b>%{x|%Y-%m-%d}</b><br>Caixinha: R$ %{y:,.2f}<extra></extra>")
        if saldos_sorted["fatura"].sum()!=0:
            fig_nw.add_scatter(x=saldos_sorted["data"],y=saldos_sorted["fatura"],name="Fatura cartão",mode="lines+markers",
                               line=dict(color="#ff4444",width=2,dash="dashdot"),marker=dict(size=5,symbol="x",color="#ff4444"),
                               hovertemplate="<b>%{x|%Y-%m-%d}</b><br>Fatura: R$ %{y:,.2f}<extra></extra>")
        fig_nw.update_layout(**build_plotly_theme(),height=420,xaxis_title=None,yaxis_title="R$",
                             legend=dict(orientation="h",yanchor="bottom",y=1.02,font=dict(size=11)))
        st.plotly_chart(fig_nw,width='stretch')
        tbl=saldos_sorted[["data","balamt","caixinha","fatura","networth"]].copy()
        tbl.columns=["Data","Conta","Caixinha","Fatura","Networth"]; tbl["Data"]=tbl["Data"].dt.date
        for col in ["Conta","Caixinha","Fatura","Networth"]: tbl[col]=tbl[col].map(fmt_brl)
        st.dataframe(tbl.sort_values("Data",ascending=False).reset_index(drop=True),width='stretch',height=280)

    # ── Projeção ──────────────────────────────────────────────────────────────
    with nw_tab2:
        import datetime as _dt5
        st.markdown("<p style='color:#555;font-size:0.75rem;font-family:DM Mono,monospace;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:0.8rem'>saldo líquido mensal e projeção linear</p>",unsafe_allow_html=True)

        df_proj_base=df[df["categoria"].isin(cats_sel)&~df["reembolsado"]].copy()
        meses_todos_proj=sorted(df_proj_base["mes"].unique())

        if not meses_todos_proj:
            st.info("Nenhum dado disponível.")
        else:
            col_ctrl1,col_ctrl2=st.columns([3,1])
            with col_ctrl1:
                st.markdown("<p style='color:#666;font-size:0.72rem;font-family:DM Mono,monospace;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:0.3rem'>período base para cálculo da média</p>",unsafe_allow_html=True)
                if len(meses_todos_proj)>=2:
                    base_range=st.select_slider("base",options=meses_todos_proj,
                        value=st.session_state.get("proj_base_range",(meses_todos_proj[0],meses_todos_proj[-1])),
                        key="proj_base_range",label_visibility="collapsed")
                else: base_range=(meses_todos_proj[0],meses_todos_proj[0])
            with col_ctrl2:
                st.markdown("<p style='color:#666;font-size:0.72rem;font-family:DM Mono,monospace;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:0.3rem'>projetar até</p>",unsafe_allow_html=True)
                _proj_default_date=_dt5.date.today().replace(year=_dt5.date.today().year+1)
                proj_ate=st.date_input("proj_ate",value=st.session_state.get("proj_ate_date",_proj_default_date),key="proj_ate_date",label_visibility="collapsed")

            saldo_mensal=(df_proj_base.groupby("mes")["valor"].sum().reset_index()
                          .rename(columns={"valor":"saldo"}).sort_values("mes").reset_index(drop=True))
            rec_por_mes=df_proj_base[df_proj_base["valor"]>0].groupby("mes")["valor"].sum().rename("receita")
            gas_por_mes=df_proj_base[df_proj_base["valor"]<0].groupby("mes")["valor"].sum().abs().rename("gasto")
            saldo_mensal=saldo_mensal.join(rec_por_mes,on="mes").join(gas_por_mes,on="mes")
            saldo_mensal["receita"]=saldo_mensal["receita"].fillna(0); saldo_mensal["gasto"]=saldo_mensal["gasto"].fillna(0)

            mask_base=(saldo_mensal["mes"]>=base_range[0])&(saldo_mensal["mes"]<=base_range[1])
            saldo_base=saldo_mensal[mask_base]
            media_mensal=saldo_base["saldo"].mean() if not saldo_base.empty else 0.0
            n_meses_base=len(saldo_base)

            ultimo_mes_str=saldo_mensal["mes"].max()
            p_atual=pd.Period(ultimo_mes_str,freq="M"); p_fim=pd.Period(proj_ate.strftime("%Y-%m"),freq="M")
            meses_proj=[]; p=p_atual+1
            while p<=p_fim: meses_proj.append(str(p)); p+=1

            save_pref("proj_base_range",json.dumps(list(base_range)))
            save_pref("proj_ate_date",proj_ate.isoformat())

            _accent=get_accent()
            proj_b, proj_a = st.tabs(["Acumulado projetado", "Saldo mensal"])

            with proj_a:
                fig_s=go.Figure()
                _bar_colors=[colors[0] if v>=0 else "#ff5555" for v in saldo_mensal["saldo"]]
                _bar_opacity=[1.0 if base_range[0]<=m<=base_range[1] else 0.45 for m in saldo_mensal["mes"]]
                fig_s.add_bar(x=saldo_mensal["mes"],y=saldo_mensal["saldo"],name="Saldo histórico",
                              marker=dict(color=_bar_colors,opacity=_bar_opacity,line_width=0),
                              customdata=list(zip(saldo_mensal["receita"],saldo_mensal["gasto"],saldo_mensal["saldo"])),
                              hovertemplate="<b>%{x}</b><br>Receita: R$ %{customdata[0]:,.2f}<br>Gasto: R$ %{customdata[1]:,.2f}<br>Saldo: R$ %{customdata[2]:,.2f}<extra></extra>")
                if meses_proj:
                    fig_s.add_bar(x=meses_proj,y=[media_mensal]*len(meses_proj),name="Projeção (média base)",
                                  marker=dict(color=colors[0] if media_mensal>=0 else "#ff5555",opacity=0.25,
                                              line=dict(color=colors[0] if media_mensal>=0 else "#ff5555",width=1)),
                                  hovertemplate="<b>%{x}</b> (projeção)<br>Estimativa: R$ %{y:,.2f}<extra></extra>")
                _todos_x=list(saldo_mensal["mes"])+meses_proj
                fig_s.add_scatter(x=_todos_x,y=[media_mensal]*len(_todos_x),
                                  name=f"Média base · {fmt_brl_signed(media_mensal)}/mês",mode="lines",
                                  line=dict(color=colors[1],width=2,dash="dot"),
                                  hovertemplate=f"Média: R$ {media_mensal:,.2f}/mês<extra></extra>")
                fig_s.add_hline(y=0,line_color="#333",line_width=1)
                if meses_proj:
                    fig_s.add_vline(x=ultimo_mes_str,line_color="#333",line_width=1,line_dash="dot")
                    fig_s.add_annotation(x=meses_proj[0],y=1,yref="paper",text="projeção →",showarrow=False,font=dict(color="#444",size=10,family="DM Mono"),xanchor="left")
                fig_s.update_layout(**build_plotly_theme(),height=420,bargap=0.25,xaxis_title=None,yaxis_title="R$",
                                    legend=dict(orientation="h",yanchor="bottom",y=1.02,font=dict(size=11)))
                st.plotly_chart(fig_s,width='stretch')
                _melhor=saldo_mensal["saldo"].max(); _pior=saldo_mensal["saldo"].min()
                _proj_acum=media_mensal*len(meses_proj); _meses_pos=(saldo_mensal["saldo"]>=0).sum(); _meses_neg=(saldo_mensal["saldo"]<0).sum()
                k1,k2,k3,k4=st.columns(4)
                k1.metric(f"Média ({n_meses_base} meses base)",fmt_brl_signed(media_mensal))
                k2.metric("Melhor mês",fmt_brl_signed(_melhor)); k3.metric("Pior mês",fmt_brl_signed(_pior))
                k4.metric(f"Projeção acumulada ({len(meses_proj)}m)",fmt_brl_signed(_proj_acum) if meses_proj else "—")
                st.markdown(f"<p style='color:#555;font-size:0.75rem;font-family:DM Mono,monospace;margin-top:0.3rem'>meses no positivo: <span style='color:{colors[0]}'>{_meses_pos}</span> · meses no negativo: <span style='color:#ff5555'>{_meses_neg}</span></p>",unsafe_allow_html=True)
                with st.expander("tabela de saldos mensais",expanded=False):
                    tbl_s=saldo_mensal[["mes","receita","gasto","saldo"]].copy()
                    tbl_s["base"]=tbl_s["mes"].apply(lambda m:"✓" if base_range[0]<=m<=base_range[1] else "")
                    tbl_s.columns=["Mês","Receita","Gasto","Saldo","Base"]
                    for col in ["Receita","Gasto","Saldo"]: tbl_s[col]=tbl_s[col].map(fmt_brl_signed)
                    if meses_proj:
                        tbl_s=pd.concat([tbl_s,pd.DataFrame({"Mês":meses_proj,"Receita":["—"]*len(meses_proj),"Gasto":["—"]*len(meses_proj),"Saldo":[fmt_brl_signed(media_mensal)]*len(meses_proj),"Base":["(proj.)"]*len(meses_proj)})],ignore_index=True)
                    st.dataframe(tbl_s.sort_values("Mês",ascending=False).reset_index(drop=True),width='stretch',height=300)

            with proj_b:
                st.markdown(f"<p style='color:#555;font-size:0.75rem;font-family:DM Mono,monospace;margin-bottom:0.5rem'>patrimônio estimado partindo do networth em {_nw_inicio_label} e aplicando o saldo médio mensal</p>",unsafe_allow_html=True)
                col_nw,col_ajuste=st.columns([1,2])
                with col_nw:
                    st.markdown(f"<p style='color:#666;font-size:0.72rem;font-family:DM Mono,monospace;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:0.2rem'>networth em {_nw_inicio_label}</p>",unsafe_allow_html=True)
                    # Sempre usa o valor do início do mês — não restaura de prefs
                    nw_input=st.number_input("nw",value=_nw_inicio_mes,step=500.0,format="%.2f",
                                             key="proj_nw_input",label_visibility="collapsed",
                                             help="Networth no início do mês. Editável para ajustes manuais, mas sempre reinicia do valor calculado.")
                with col_ajuste:
                    st.markdown("<p style='color:#666;font-size:0.72rem;font-family:DM Mono,monospace;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:0.2rem'>ajuste de saldo mensal projetado (R$/mês)</p>",unsafe_allow_html=True)
                    saldo_ajuste=st.slider("ajuste",min_value=-5000.0,max_value=5000.0,
                                           value=st.session_state.get("proj_saldo_ajuste",0.0),
                                           step=100.0,key="proj_saldo_ajuste",label_visibility="collapsed",
                                           help="Ajuste sobre a média calculada — útil para simular cenários")
                save_pref("proj_saldo_ajuste",str(saldo_ajuste))
                _saldo_proj=media_mensal+saldo_ajuste
                st.markdown(f"<p style='color:#555;font-size:0.75rem;font-family:DM Mono,monospace;'>saldo usado na projeção: <span style='color:{_accent}'>{fmt_brl_signed(_saldo_proj)}/mês</span></p>",unsafe_allow_html=True)
                if not meses_proj:
                    st.info("Defina uma data de projeção futura para ver o acumulado.")
                else:
                    _pts_proj_x=[ultimo_mes_str]+meses_proj; _pts_proj_y=[nw_input]
                    for _ in meses_proj: _pts_proj_y.append(_pts_proj_y[-1]+_saldo_proj)
                    fig_acum=go.Figure()
                    nw_hist_plot=saldos_sorted[["data","networth"]].dropna(subset=["networth"])
                    if not nw_hist_plot.empty:
                        fig_acum.add_scatter(x=nw_hist_plot["data"],y=nw_hist_plot["networth"],name="Networth real",
                                             mode="lines+markers",line=dict(color=colors[0],width=2),marker=dict(size=5),
                                             hovertemplate="<b>%{x|%Y-%m}</b><br>Networth: R$ %{y:,.2f}<extra></extra>",
                                             fill="tozeroy",fillcolor="rgba(200,240,96,0.08)")
                    fig_acum.add_scatter(x=_pts_proj_x,y=_pts_proj_y,name="Projeção",mode="lines+markers",
                                         line=dict(color=colors[1],width=2,dash="dash"),marker=dict(size=6,symbol="circle-open"),
                                         hovertemplate="<b>%{x}</b> (proj.)<br>Estimativa: R$ %{y:,.2f}<extra></extra>")
                    fig_acum.update_layout(**build_plotly_theme(),height=400,xaxis_title=None,yaxis_title="R$",
                                          legend=dict(orientation="h",yanchor="bottom",y=1.02,font=dict(size=11)))
                    st.plotly_chart(fig_acum,width='stretch')
                    _nw_fim=_pts_proj_y[-1]; _variacao=_nw_fim-nw_input; _pct=(_variacao/nw_input*100) if nw_input!=0 else 0.0
                    b1,b2,b3=st.columns(3)
                    b1.metric(f"Networth em {_nw_inicio_label}",fmt_brl(nw_input))
                    b2.metric(f"Estimativa em {proj_ate.strftime('%m/%Y')}",fmt_brl(_nw_fim),delta=f"{'+' if _variacao>=0 else ''}{fmt_brl_signed(_variacao)}")
                    b3.metric("Variação total",f"{_pct:+.1f}%")

    # ── Rendimento acumulado ──────────────────────────────────────────────────
    with nw_tab3:
        rend=saldos_sorted[saldos_sorted["rendimento_conta"].notna()].copy()
        if rend.empty: st.info("Nenhum dado de rendimento ainda.")
        else:
            rend=rend.sort_values("data")
            if "rendimento_caixinha" not in rend.columns: rend["rendimento_caixinha"]=0.0
            rend["rendimento_caixinha"]=rend["rendimento_caixinha"].fillna(0.0)
            rend["acum_conta"]=rend["rendimento_conta"].cumsum()
            rend["acum_caixinha"]=rend["rendimento_caixinha"].cumsum()
            rend["acum_total"]=rend["acum_conta"]+rend["acum_caixinha"]
            fig_acum_r=go.Figure()
            fig_acum_r.add_scatter(x=rend["data"],y=rend["acum_total"],name="Total",mode="lines+markers",
                                   line=dict(color=colors[0],width=2),marker=dict(size=6),
                                   fill="tozeroy",fillcolor="rgba(200,240,96,0.12)",
                                   hovertemplate="<b>%{x|%Y-%m-%d}</b><br>Total: R$ %{y:,.2f}<extra></extra>")
            fig_acum_r.add_scatter(x=rend["data"],y=rend["acum_conta"],name="Conta",mode="lines+markers",
                                   line=dict(color=colors[1],width=2,dash="dot"),marker=dict(size=5),
                                   hovertemplate="<b>%{x|%Y-%m-%d}</b><br>Conta: R$ %{y:,.2f}<extra></extra>")
            if rend["acum_caixinha"].sum()>0:
                fig_acum_r.add_scatter(x=rend["data"],y=rend["acum_caixinha"],name="Caixinha",mode="lines+markers",
                                       line=dict(color=colors[2],width=2,dash="dash"),marker=dict(size=5),
                                       hovertemplate="<b>%{x|%Y-%m-%d}</b><br>Caixinha: R$ %{y:,.2f}<extra></extra>")
            fig_acum_r.update_layout(**build_plotly_theme(),height=380,xaxis_title=None,yaxis_title="R$",
                                     legend=dict(orientation="h",yanchor="bottom",y=1.02,font=dict(size=11)))
            st.plotly_chart(fig_acum_r,width='stretch')
            a1,a2,a3=st.columns(3)
            a1.metric("Acumulado conta",fmt_brl(rend["acum_conta"].iloc[-1]))
            a2.metric("Acumulado caixinha",fmt_brl(rend["acum_caixinha"].iloc[-1]))
            a3.metric("Acumulado total",fmt_brl(rend["acum_total"].iloc[-1]))
