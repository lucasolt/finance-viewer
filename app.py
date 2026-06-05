import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from ofxparse import OfxParser
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

/* Slider neutro */
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
    # iFood
    # Vicios
    "tabarcaria": "Vícios & Conveniência",
    "trinca tabarcaria": "Vícios & Conveniência",
    "tabacariacapri" : "Vícios & Conveniência",
    "tabacaria" : "Vícios & Conveniência",
    "havana revistaria e ta" : "Vícios & Conveniência",
    "cameron" : "Vícios & Conveniência",
    "banca cafe" : "Vícios & Conveniência",
    "posto" : "Vícios & Conveniência",
    "combust" : "Vícios & Conveniência",
    # Alimentação — estabelecimentos
    "alimentos" : "Alimentação & Mercado",
    "super apolo" :  "Alimentação & Mercado",
    "zaffari": "Alimentação & Mercado",
    "mini mercado" : "Alimentação & Mercado",
    "companhiazaffari": "Alimentação & Mercado",
    "la brescia": "Alimentação & Mercado",
    "armazem e fruteira": "Alimentação & Mercado",
    "themis restaurante": "Alimentação & Mercado",
    "rappi": "Alimentação & Mercado",
    "mcdonalds": "Alimentação & Mercado",
    "burger": "Alimentação & Mercado",
    "subway": "Alimentação & Mercado",
    "padaria": "Alimentação & Mercado",
    "supermercado": "Alimentação & Mercado",
    "carrefour": "Alimentação & Mercado",
    "restaurante": "Alimentação & Mercado",
    "lanche": "Alimentação & Mercado",
    "pizza": "Alimentação & Mercado",
    "pão de açúcar": "Alimentação & Mercado",
    "hot dog" : "Alimentação & Mercado",
    # Transporte
    "99": "Transporte",
    "cabify": "Transporte",
    #"shell": "Transporte",
    #"posto": "Transporte",
    "estacionamento": "Transporte",
    "onibus": "Transporte",
    "metro": "Transporte",
    "passagem": "Transporte",
    "veppo cia": "Transporte",
    # Saúde
    "panvel": "Saúde",
    "sao joao farmacias": "Saúde",
    "farmaciaosaojoao": "Saúde",
    "drogaria achutti": "Saúde",
    "rd saude": "Saúde",
    "bioterapica": "Saúde",
    "m e pa clinica": "Saúde",
    "dr. central": "Saúde",
    "rafael ramos amaral": "Saúde",
    "farmacia": "Saúde",
    "drogaria": "Saúde",
    "drogasil": "Saúde",
    "ultrafarma": "Saúde",
    "consulta": "Saúde",
    "medico": "Saúde",
    "clinica": "Saúde",
    "academia": "Saúde",
    "raia" : "Saúde",
    "pague menos" : "Saúde",
    # Streaming
    "netflix": "Assinaturas",
    "amazon prime": "Assinaturas",
    "hbo": "Assinaturas",
    "disney": "Assinaturas",
    "globoplay": "Assinaturas",
    "tinder" : "Assinaturas",
    #"claude" : "Assinaturas",
    "subscription" : "Assinaturas",
    
    # Telecom
    "telefonica brasil": "Telecom",
    "conta vivo": "Telecom",
    "vivo": "Telecom",
    "claro": "Telecom",
    "tim": "Telecom",
    "oi": "Telecom",
    # Compras
    "casa do papel" : "Compras",
    "amazon": "Compras",
    "mercado pago": "Compras",
    "mercado livre": "Compras",
    "magalupay": "Compras",
    "pichau": "Compras",
    "pagali": "Compras",
    "pagseguro international": "Compras",
    "pay2all": "Compras",
    "nuvei do brasil": "Compras",
    "americanas": "Compras",
    "magazine": "Compras",
    "shopee": "Compras",
    "aliexpress": "Compras",
    "pagseguro tecnologia" : "Compras",
    # Vestuário
    "h&m": "Vestuário",
    "lupo": "Vestuário",
    "hering": "Vestuário",
    "renner": "Vestuário",
    "riachuelo": "Vestuário",
    "zara": "Vestuário",
    # Lazer
    "cucko" : "Lazer",
    "ingresso com": "Lazer",
    "steam": "Lazer",
    "cinema": "Lazer",
    "bar": "Lazer",
    "cerveja": "Lazer",
    "territoriopub" : "Lazer",
    "plano pixel" : "Lazer",
    # Casa
    #"aluguel": "Casa",
    #"condominio": "Casa",
    #"luz": "Casa",
    #"agua": "Casa",
    #"internet": "Casa",
    # Investimento
    "aplicação rdb": "Investimento",
    "aplicacao rdb": "Investimento",
    "rdb": "Investimento",
    "cdb": "Investimento",
    "tesouro": "Investimento",
    # Profissional
    "conselho regional de psicologia": "Profissional",
    "crp": "Profissional",
    # Impostos
    "municipio de porto alegre": "Impostos",
    "receita federal": "Impostos",
    "iptu": "Impostos",
    "ipva": "Impostos",
    # Pagamento de Fatura
    "pagamento de fatura": "Pagamento de Fatura",
    "pagamento recebido": "Crédito de Fatura",
    # Transferência Pessoal (pessoas físicas — fallback via lógica abaixo)
}

# ── Helpers ───────────────────────────────────────────────────────────────────
def fmt_brl(val: float) -> str:
    return f"R$ {abs(val):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def fmt_brl_signed(val: float) -> str:
    sign = "- " if val < 0 else ""
    return f"{sign}R$ {abs(val):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def df_to_xlsx(df: pd.DataFrame) -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)
    return buf.getvalue()

def guess_category(desc: str, valor: float = 0.0) -> str:
    import re
    d = desc.lower()

    if "pagamento de fatura" in d:
        return "Pagamento de Fatura"

    # Bolsa residência: transferência recebida de Lucas Oltramari com valor próximo de 4750
    if ("transferência recebida" in d or "transferencia recebida" in d) and        "lucas oltramari" in d and 4500 <= abs(valor) <= 5000:
        return "Bolsa Residência"

    # Regex priority rules — checados antes do mapa geral
    REGEX_MAP = [
        (r"^ifd\*",           "iFood"),
        (r"ifood",            "iFood"),
        (r"\buber\b",         "Transporte"),
        (r"uberride",     "Transporte"),
        (r"^dm \*",           "Assinaturas"),
        (r"\*spotify",        "Assinaturas"),
        #(r"\*appgas",         "Casa"),
        (r"\bpub\b", "Lazer"),
        (r"^pagamento recebido$", "Crédito de Fatura"),
    ]
    for pattern, cat in REGEX_MAP:
        if re.search(pattern, d):
            return cat

    # Keyword map — longer keywords checked first to avoid partial matches
    for kw, cat in sorted(CATEGORY_MAP.items(), key=lambda x: -len(x[0])):
        if kw in d:
            return cat
    if re.search(r"•{3}\.\d{3}\.\d{3}-•{2}", desc):
        return "Transferência Pessoal"
    return "Outros"

def parse_ofx(file_bytes: bytes, origem: str = "extrato") -> tuple:
    """Returns (transactions_df, balamt_dict) where balamt_dict = {date: amount}"""
    ofx = OfxParser.parse(io.BytesIO(file_bytes))
    rows = []
    saldos = {}
    for account in ofx.accounts:
        for txn in account.statement.transactions:
            rows.append({
                "data": txn.date.date() if hasattr(txn.date, "date") else txn.date,
                "descricao": txn.memo or txn.payee or "",
                "valor": float(txn.amount),
            })
        # Extract BALAMT e RENDIMENTO — só pra extrato da conta, não fatura
        if origem == "extrato":
            try:
                stmt = account.statement
                if hasattr(stmt, 'balance') and stmt.balance is not None:
                    bal_date = stmt.balance_date
                    if hasattr(bal_date, 'date'):
                        bal_date = bal_date.date()
                    saldos[str(bal_date)] = {"balamt": float(stmt.balance), "rendimento_conta": None}
            except Exception:
                pass

    # Parse RENDIMENTO LIQUIDO from raw BAL tags (ofxparse doesn't read these)
    if origem == "extrato":
        try:
            from bs4 import BeautifulSoup as _BS
            raw_text = file_bytes.decode("utf-8", errors="ignore")
            soup = _BS(raw_text, "html.parser")
            for bal_tag in soup.find_all("bal"):
                name_tag = bal_tag.find("name")
                val_tag = bal_tag.find("value")
                dtasof_tag = bal_tag.find("dtasof")
                if name_tag and val_tag and "rendimento" in name_tag.get_text().lower():
                    val = float(val_tag.get_text().strip())
                    if dtasof_tag:
                        from ofxparse import OfxParser as _OP
                        try:
                            d = _OP.parseOfxDateTime(dtasof_tag.get_text().strip()).date()
                        except:
                            d = list(saldos.keys())[-1] if saldos else None
                    else:
                        d = list(saldos.keys())[-1] if saldos else None
                    if d:
                        key = str(d)
                        if key in saldos:
                            saldos[key]["rendimento_conta"] = val
                        else:
                            saldos[key] = {"balamt": None, "rendimento_conta": val}
        except Exception:
            pass
    df = pd.DataFrame(rows)
    if df.empty:
        return df, saldos
    df["data"] = pd.to_datetime(df["data"])
    df["mes"] = df["data"].dt.to_period("M").astype(str)
    df["categoria"] = df.apply(lambda r: guess_category(r["descricao"], r["valor"]), axis=1)
    return df, saldos

def detectar_reembolsos(df: pd.DataFrame, janela_dias: int = 90) -> pd.DataFrame:
    """Marca pares (reembolso recebido <-> transferência enviada) com mesmo
    CNPJ/CPF e valor absoluto, dentro de uma janela de tempo. Adiciona coluna
    'reembolsado' (bool). Pares casados são neutralizados nos cálculos."""
    import re as _re
    df = df.copy()
    df["reembolsado"] = False
    if df.empty:
        return df

    def extrai_doc(desc):
        # captura CNPJ (xx.xxx.xxx/xxxx-xx) ou CPF mascarado
        m = _re.search(r"\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}", str(desc))
        if m:
            return m.group(0)
        m = _re.search(r"•{3}\.\d{3}\.\d{3}-•{2}", str(desc))
        return m.group(0) if m else None

    df["_doc"] = df["descricao"].apply(extrai_doc)
    df["_eh_reembolso"] = df["descricao"].str.lower().str.startswith("reembolso recebido")
    df["_eh_envio"] = df["descricao"].str.lower().str.startswith("transferência enviada")

    reembolsos = df[df["_eh_reembolso"] & df["_doc"].notna()]
    usados = set()
    for idx_r, reemb in reembolsos.iterrows():
        valor_abs = abs(reemb["valor"])
        doc = reemb["_doc"]
        data_r = reemb["data"]
        # candidatos: envios com mesmo doc, mesmo valor abs, dentro da janela
        cand = df[
            df["_eh_envio"] & (df["_doc"] == doc) &
            (df["valor"].abs().round(2) == round(valor_abs, 2)) &
            (abs((df["data"] - data_r).dt.days) <= janela_dias) &
            (~df.index.isin(usados))
        ]
        if not cand.empty:
            idx_envio = cand.index[0]
            df.at[idx_r, "reembolsado"] = True
            df.at[idx_envio, "reembolsado"] = True
            usados.add(idx_r)
            usados.add(idx_envio)

    return df.drop(columns=["_doc", "_eh_reembolso", "_eh_envio"])

@st.cache_resource
def get_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

@st.cache_data(ttl=60)
def load_from_supabase() -> pd.DataFrame:
    sb = get_supabase()
    all_rows = []
    page_size = 1000
    offset = 0
    while True:
        res = sb.table("transacoes").select("*").range(offset, offset + page_size - 1).execute()
        if not res.data:
            break
        all_rows.extend(res.data)
        if len(res.data) < page_size:
            break
        offset += page_size
    if not all_rows:
        return pd.DataFrame()
    df = pd.DataFrame(all_rows)
    df["data"] = pd.to_datetime(df["data"])
    df["mes"] = df["data"].dt.to_period("M").astype(str)
    df["categoria"] = df.apply(lambda r: guess_category(r["descricao"], r["valor"]), axis=1)
    df = detectar_reembolsos(df)
    return df

def save_to_supabase(df: pd.DataFrame):
    sb = get_supabase()
    rows = []
    for _, r in df.iterrows():
        rows.append({
            "data": r["data"].strftime("%Y-%m-%d"),
            "descricao": r["descricao"],
            "valor": float(r["valor"]),
            "categoria": r["categoria"],
            "mes": r["mes"],
            "origem": r["origem"] if "origem" in r.index else "extrato",
        })
    # upsert ignores duplicates via UNIQUE constraint
    sb.table("transacoes").upsert(rows, on_conflict="data,descricao,valor").execute()
    load_from_supabase.clear()

# ── Saldos ───────────────────────────────────────────────────────────────────
def save_saldo(data: str, info: dict, origem: str = "extrato"):
    row = {"data": data, "origem": origem}
    if info.get("balamt") is not None:
        row["balamt"] = info["balamt"]
    if info.get("rendimento_conta") is not None:
        row["rendimento_conta"] = info["rendimento_conta"]
    get_supabase().table("saldos").upsert(row, on_conflict="data,origem").execute()
    load_saldos.clear()

@st.cache_data(ttl=60)
def load_saldos() -> pd.DataFrame:
    sb = get_supabase()
    res = sb.table("saldos").select("*").execute()
    if not res.data:
        return pd.DataFrame(columns=["data","balamt","rendimento_conta","origem"])
    df = pd.DataFrame(res.data)
    df["data"] = pd.to_datetime(df["data"])
    if "rendimento_conta" not in df.columns:
        df["rendimento_conta"] = None
    return df.sort_values("data")

# ── Preferences ──────────────────────────────────────────────────────────────
def load_prefs() -> dict:
    sb = get_supabase()
    res = sb.table("preferencias").select("*").execute()
    return {r["chave"]: r["valor"] for r in res.data} if res.data else {}

def save_pref(chave: str, valor: str):
    get_supabase().table("preferencias").upsert(
        {"chave": chave, "valor": valor}, on_conflict="chave"
    ).execute()

# ── Login ─────────────────────────────────────────────────────────────────────
if "authed" not in st.session_state:
    st.session_state.authed = False

if not st.session_state.authed:
    st.markdown("<div class='login-wrap'>", unsafe_allow_html=True)
    st.title("💸 gastos")
    pwd = st.text_input("senha", type="password", label_visibility="collapsed",
                        placeholder="senha")
    if st.button("entrar", width='stretch'):
        if pwd == st.secrets["APP_PASSWORD"]:
            st.session_state.authed = True
            st.rerun()
        else:
            st.error("senha incorreta")
    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# ── Load data + prefs ────────────────────────────────────────────────────────
if "upload_key" not in st.session_state:
    st.session_state.upload_key = 0
df = load_from_supabase()
df_saldos = load_saldos()
prefs = load_prefs()

# Apply saved prefs to session state (only first run)
if "prefs_loaded" not in st.session_state:
    if "color_scheme" in prefs:
        st.session_state["color_scheme"] = prefs["color_scheme"]
    if "cat_state" in prefs:
        st.session_state["cat_state"] = json.loads(prefs["cat_state"])
    if "tipo" in prefs:
        st.session_state["tipo_radio"] = prefs["tipo"]

    st.session_state["prefs_loaded"] = True

# ── Header ────────────────────────────────────────────────────────────────────
st.title("💸 controle de gastos")
st.markdown("<p class='upload-hint'>upload de extratos OFX — pode enviar vários de uma vez</p>",
            unsafe_allow_html=True)
st.divider()

# ── Upload ────────────────────────────────────────────────────────────────────
col_up1, col_up2 = st.columns(2)

def process_upload(files, origem: str):
    frames, errors = [], []
    all_saldos = {}
    for f in files:
        try:
            parsed, saldos = parse_ofx(f.read(), origem)
            if not parsed.empty:
                parsed["origem"] = origem
                frames.append(parsed)
            all_saldos.update(saldos)
        except Exception as e:
            errors.append(f"{f.name}: {e}")
    if frames:
        new_df = pd.concat(frames, ignore_index=True).drop_duplicates(
            subset=["data", "descricao", "valor", "origem"]
        )
        with st.spinner("salvando no banco..."):
            save_to_supabase(new_df)
            for data, info in all_saldos.items():
                save_saldo(data, info, origem)
        st.session_state.upload_key += 1
        st.success(f"{len(new_df)} transações ({origem}) salvas." +
                   (f" {len(all_saldos)} saldo(s) registrado(s)." if all_saldos else ""))
    for e in errors:
        st.error(e)

with col_up1:
    st.markdown("<p style='color:#555;font-size:0.75rem;font-family:DM Mono,monospace;text-transform:uppercase;letter-spacing:0.08em;'>Extrato da conta</p>", unsafe_allow_html=True)
    up_extrato = st.file_uploader("extrato", type=["ofx"], accept_multiple_files=True,
                                   label_visibility="collapsed", key=f"up_extrato_{st.session_state.upload_key}")
    if up_extrato:
        process_upload(up_extrato, "extrato")
        df = load_from_supabase()

with col_up2:
    st.markdown("<p style='color:#555;font-size:0.75rem;font-family:DM Mono,monospace;text-transform:uppercase;letter-spacing:0.08em;'>Fatura do cartão</p>", unsafe_allow_html=True)
    up_fatura = st.file_uploader("fatura", type=["ofx"], accept_multiple_files=True,
                                  label_visibility="collapsed", key=f"up_fatura_{st.session_state.upload_key}")
    if up_fatura:
        process_upload(up_fatura, "fatura")
        df = load_from_supabase()

if df.empty:
    st.markdown("""
    <div style='text-align:center; padding: 4rem 0; color: #333;'>
        <div style='font-size: 3rem;'>📂</div>
        <div style='font-family: DM Mono, monospace; font-size: 0.85rem; margin-top: 1rem;'>
            nenhum dado ainda — faça upload de um OFX
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Aparência")
    scheme = st.selectbox("Esquema de cores", list(COLOR_SCHEMES.keys()),
                 key="color_scheme")
    save_pref("color_scheme", scheme)
    st.divider()
    st.markdown("### Filtros")
    import datetime
    _min_date = df["data"].min().date()
    _max_date = df["data"].max().date()

    # Dropdown de presets
    PRESET_OPTS = ["Tudo", "Últimos 12 meses", "Este ano (YTD)", "Este mês", "Personalizado", "Barra deslizante"]
    preset = st.selectbox("Período", PRESET_OPTS, index=5, key="date_preset")

    # lista de meses disponíveis (pro slider)
    _meses_disp = sorted(df["mes"].unique())

    # Calcula o range com base no preset
    if preset == "Tudo":
        d_start, d_end = _min_date, _max_date
    elif preset == "Últimos 12 meses":
        d_end = _max_date
        try:
            d_start = d_end.replace(year=d_end.year - 1)
        except ValueError:
            d_start = d_end.replace(year=d_end.year - 1, day=28)
        d_start = max(d_start, _min_date)
    elif preset == "Este ano (YTD)":
        d_start = max(datetime.date(_max_date.year, 1, 1), _min_date)
        d_end = _max_date
    elif preset == "Este mês":
        d_start = max(datetime.date(_max_date.year, _max_date.month, 1), _min_date)
        d_end = _max_date
    elif preset == "Barra deslizante":
        # O range vem do slider renderizado abaixo do gráfico.
        # Lê do session_state; default = range completo.
        _sel = st.session_state.get("range_slider", (_meses_disp[0], _meses_disp[-1]))
        _m_ini, _m_fim = _sel[0], _sel[-1]
        d_start = pd.Period(_m_ini, freq="M").start_time.date()
        d_end = pd.Period(_m_fim, freq="M").end_time.date()
        d_start = max(d_start, _min_date)
        d_end = min(d_end, _max_date)
        st.caption("↓ use a barra abaixo do gráfico")
    else:  # Personalizado — dois date inputs separados
        c_ini, c_fim = st.columns(2)
        d_start = c_ini.date_input("De", value=_min_date,
                                   min_value=_min_date, max_value=_max_date,
                                   key="date_custom_start")
        d_end = c_fim.date_input("Até", value=_max_date,
                                 min_value=_min_date, max_value=_max_date,
                                 key="date_custom_end")
        # garante ordem correta
        if d_start > d_end:
            d_start, d_end = d_end, d_start

    _tipo_opts = ["Gastos", "Receitas", "Tudo"]
    _tipo_idx = _tipo_opts.index(st.session_state.get("tipo_radio", "Gastos")) if st.session_state.get("tipo_radio") in _tipo_opts else 0
    tipo = st.radio("Tipo", _tipo_opts, index=_tipo_idx)
    save_pref("tipo", tipo)

    st.markdown("### Categorias")
    cats = sorted(df["categoria"].unique())
    EXCLUDED_BY_DEFAULT = {"Pagamento de Fatura", "Crédito de Fatura", "Investimento"}

    # Inicializa estado das categorias na primeira vez ou para categorias novas
    if "cat_state" not in st.session_state:
        st.session_state.cat_state = {}
    for c in cats:
        if c not in st.session_state.cat_state:
            st.session_state.cat_state[c] = c not in EXCLUDED_BY_DEFAULT

    col_a, col_b, col_c = st.columns(3)
    if col_a.button("✓ Tudo", width='stretch'):
        for c in cats:
            st.session_state[f"cat_{c}"] = True
            st.session_state.cat_state[c] = True
        save_pref("cat_state", json.dumps(st.session_state.cat_state))
        st.rerun()
    if col_b.button("◎ Padrão", width='stretch'):
        for c in cats:
            val = c not in EXCLUDED_BY_DEFAULT
            st.session_state[f"cat_{c}"] = val
            st.session_state.cat_state[c] = val
        save_pref("cat_state", json.dumps(st.session_state.cat_state))
        st.rerun()
    if col_c.button("✗ Nada", width='stretch'):
        for c in cats:
            st.session_state[f"cat_{c}"] = False
            st.session_state.cat_state[c] = False
        save_pref("cat_state", json.dumps(st.session_state.cat_state))
        st.rerun()

    cats_sel = []
    for c in cats:
        checked = st.checkbox(c, value=st.session_state.cat_state[c], key=f"cat_{c}")
        st.session_state.cat_state[c] = checked
        if checked:
            cats_sel.append(c)
    save_pref("cat_state", json.dumps({k: v for k, v in st.session_state.cat_state.items()}))
    st.divider()
    if "confirm_delete" not in st.session_state:
        st.session_state.confirm_delete = False
    if not st.session_state.confirm_delete:
        if st.button("🗑 Apagar todos os dados"):
            st.session_state.confirm_delete = True
            st.rerun()
    else:
        st.warning("Tem certeza? Isso apaga tudo.")
        col_c, col_d = st.columns(2)
        if col_c.button("✓ Sim", width='stretch'):
            get_supabase().table("transacoes").delete().neq("id", 0).execute()
            get_supabase().table("saldos").delete().neq("id", 0).execute()
            load_from_supabase.clear()
            load_saldos.clear()
            st.session_state.confirm_delete = False
            st.rerun()
        if col_d.button("✗ Não", width='stretch'):
            st.session_state.confirm_delete = False
            st.rerun()
    if st.button("🚪 Sair"):
        st.session_state.authed = False
        st.rerun()

# ── Filter ────────────────────────────────────────────────────────────────────
import datetime as _dt
mask_data = (df["data"].dt.date >= d_start) & (df["data"].dt.date <= d_end)
# dff_tabela: tudo (inclui reembolsados) — pra tabela de transações
dff_tabela = df[mask_data & df["categoria"].isin(cats_sel)].copy()
# dff: exclui reembolsados — pra gráficos e cálculos
dff = dff_tabela[~dff_tabela["reembolsado"]].copy()
if tipo == "Gastos":
    dff = dff[dff["valor"] < 0]
elif tipo == "Receitas":
    dff = dff[dff["valor"] > 0]
dff["valor_abs"] = dff["valor"].abs()

# dff_total: aplica todos os filtros exceto tipo — usado nos KPIs (exclui reembolsados)
dff_total = dff_tabela[~dff_tabela["reembolsado"]].copy()

# ── KPIs ──────────────────────────────────────────────────────────────────────
gastos   = dff_total[dff_total["valor"] < 0]["valor"].sum()
receitas = dff_total[dff_total["valor"] > 0]["valor"].sum()
saldo    = gastos + receitas

# Networth: BALAMT mais recente + saldo líquido da Caixinha
caixinha_mask = df["descricao"].str.lower().str.contains("aplicação rdb|aplicacao rdb|resgate rdb", na=False)
saldo_caixinha = -df[caixinha_mask]["valor"].sum()  # débitos são negativos, inverte
if not df_saldos.empty:
    balamt_recente = float(df_saldos.sort_values("data").iloc[-1]["balamt"])
    networth = balamt_recente + saldo_caixinha
    networth_label = fmt_brl(networth)
else:
    networth_label = "—"

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total gasto",     fmt_brl(gastos))
c2.metric("Total recebido",  fmt_brl(receitas))
c3.metric("Saldo período",   fmt_brl_signed(saldo), delta=f"{'+' if saldo >= 0 else ''}{saldo:.2f}", delta_color="normal")
c4.metric("Transações",      len(dff_total))
c5.metric("Networth aprox.", networth_label)

# Mini-painel de patrimônio
if not df_saldos.empty or saldo_caixinha != 0:
    st.markdown(
        f"""<div style='display:flex;gap:1.5rem;margin:0.5rem 0 0.2rem;'>
        <div style='color:#555;font-size:0.75rem;font-family:DM Mono,monospace;'>
            🏦 conta: <span style='color:#e8e8e0'>{fmt_brl(balamt_recente) if not df_saldos.empty else "—"}</span>
        </div>
        <div style='color:#555;font-size:0.75rem;font-family:DM Mono,monospace;'>
            📦 caixinha: <span style='color:#e8e8e0'>{fmt_brl(saldo_caixinha) if saldo_caixinha != 0 else "—"}</span>
        </div>
        {"<div style='color:#555;font-size:0.75rem;font-family:DM Mono,monospace;'>📅 saldo em: <span style='color:#e8e8e0'>" + str(df_saldos.sort_values('data').iloc[-1]['data'].date()) + "</span></div>" if not df_saldos.empty else ""}
        </div>""",
        unsafe_allow_html=True
    )
st.divider()

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(["Por mês", "Por categoria", "Evolução", "Transações"])

with tab1:
    if dff.empty:
        st.info("Nenhum dado no período.")
    elif tipo == "Tudo":
        # Diverging chart: receitas acima, gastos abaixo, saldo como linha
        meses_u = sorted(dff["mes"].unique())
        rec_mes = dff[dff["valor"] > 0].groupby("mes")["valor"].sum().reindex(meses_u, fill_value=0)
        gas_mes = dff[dff["valor"] < 0].groupby("mes")["valor"].sum().reindex(meses_u, fill_value=0)
        sal_mes = (rec_mes + gas_mes)
        colors = get_colors()
        fig = go.Figure()
        fig.add_bar(x=meses_u, y=rec_mes.values, name="Receitas",
                    marker_color=colors[0], marker_line_width=0,
                    hovertemplate="<b>%{x}</b><br>Receita: R$ %{y:,.2f}<extra></extra>")
        fig.add_bar(x=meses_u, y=gas_mes.values, name="Gastos",
                    marker_color=colors[2], marker_line_width=0,
                    hovertemplate="<b>%{x}</b><br>Gasto: R$ %{y:,.2f}<extra></extra>")
        fig.add_scatter(x=meses_u, y=sal_mes.values, name="Saldo",
                        mode="lines+markers", line=dict(color=colors[1], width=2),
                        marker=dict(size=6),
                        hovertemplate="<b>%{x}</b><br>Saldo: R$ %{y:,.2f}<extra></extra>")
        fig.add_hline(y=0, line_color="#333", line_width=1)
        fig.update_layout(**build_plotly_theme(), height=420, bargap=0.25, barmode="relative",
                          xaxis_title=None, yaxis_title="R$",
                          legend=dict(orientation="h", yanchor="bottom", y=1.02, font=dict(size=11)))
        st.plotly_chart(fig, width='stretch')
        _tbl = pd.DataFrame({"Mês": meses_u, "Receitas": rec_mes.values, "Gastos": gas_mes.abs().values, "Saldo": sal_mes.values})
        st.download_button("⬇ baixar tabela (.xlsx)", df_to_xlsx(_tbl), "por_mes.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
    else:
        por_mes = (dff.groupby("mes")["valor_abs"].sum().reset_index().sort_values("mes"))
        fig = go.Figure()
        fig.add_bar(x=por_mes["mes"], y=por_mes["valor_abs"],
                    marker_color=get_accent(), marker_line_width=0,
                    hovertemplate="<b>%{x}</b><br>R$ %{y:,.2f}<extra></extra>")
        fig.update_layout(**build_plotly_theme(), height=380, bargap=0.3,
                          xaxis_title=None, yaxis_title="R$", showlegend=False)
        st.plotly_chart(fig, width='stretch')
        st.download_button("⬇ baixar tabela (.xlsx)", df_to_xlsx(por_mes.rename(columns={"mes":"Mês","valor_abs":"Valor"})), "por_mes.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
        media = por_mes["valor_abs"].mean()
        st.markdown(f"<p style='color:#555;font-size:0.8rem;font-family:DM Mono,monospace;'>média mensal: <span style='color:{get_accent()}'>{fmt_brl(media)}</span></p>",
                    unsafe_allow_html=True)

with tab2:
    if dff.empty:
        st.info("Nenhum dado no período.")
    elif tipo == "Tudo":
        # Side-by-side: receitas vs gastos por categoria
        rec_cat = dff[dff["valor"] > 0].groupby("categoria")["valor"].sum().rename("Receita")
        gas_cat = dff[dff["valor"] < 0].groupby("categoria")["valor"].sum().abs().rename("Gasto")
        por_cat_tudo = pd.concat([rec_cat, gas_cat], axis=1).fillna(0)
        por_cat_tudo.index.name = "categoria"
        por_cat_tudo = por_cat_tudo.reset_index().rename(columns={0: "categoria"}) if "categoria" not in por_cat_tudo.reset_index().columns else por_cat_tudo.reset_index()
        por_cat_tudo = por_cat_tudo.sort_values("Gasto", ascending=False)
        colors = get_colors()
        fig_bar = go.Figure()
        fig_bar.add_bar(y=por_cat_tudo["categoria"], x=por_cat_tudo["Gasto"],
                        name="Gastos", orientation="h", marker_color=colors[2],
                        hovertemplate="<b>%{y}</b><br>Gasto: R$ %{x:,.2f}<extra></extra>")
        fig_bar.add_bar(y=por_cat_tudo["categoria"], x=por_cat_tudo["Receita"],
                        name="Receitas", orientation="h", marker_color=colors[0],
                        hovertemplate="<b>%{y}</b><br>Receita: R$ %{x:,.2f}<extra></extra>")
        fig_bar.update_layout(**build_plotly_theme(), height=420, barmode="group",
                              xaxis_title="R$", yaxis_title=None,
                              legend=dict(orientation="h", yanchor="bottom", y=1.02, font=dict(size=11)))
        st.plotly_chart(fig_bar, width='stretch')
    else:
        por_cat = (dff.groupby("categoria")["valor_abs"]
                   .sum().reset_index().sort_values("valor_abs", ascending=False))
        col_a, col_b = st.columns(2)
        with col_a:
            fig_bar = go.Figure()
            fig_bar.add_bar(x=por_cat["valor_abs"], y=por_cat["categoria"],
                            orientation="h", marker_color=get_accent(), marker_line_width=0,
                            hovertemplate="<b>%{y}</b><br>R$ %{x:,.2f}<extra></extra>")
            fig_bar.update_layout(**build_plotly_theme(), height=380,
                                  xaxis_title="R$", yaxis_title=None, showlegend=False)
            st.plotly_chart(fig_bar, width='stretch')
        with col_b:
            fig_pie = px.pie(por_cat, values="valor_abs", names="categoria",
                             hole=0.55, color_discrete_sequence=get_colors())
            fig_pie.update_traces(textfont_size=11,
                hovertemplate="<b>%{label}</b><br>R$ %{value:,.2f}<br>%{percent}<extra></extra>")
            fig_pie.update_layout(**build_plotly_theme(), height=380,
                                  showlegend=True, legend=dict(font=dict(size=11)))
            st.plotly_chart(fig_pie, width='stretch')

with tab3:
    if dff.empty:
        st.info("Nenhum dado no período.")
    elif tipo == "Tudo":
        meses_u = sorted(dff["mes"].unique())
        rec_mes = dff[dff["valor"] > 0].groupby("mes")["valor"].sum().reindex(meses_u, fill_value=0)
        gas_mes = dff[dff["valor"] < 0].groupby("categoria")
        # stacked gastos abaixo, stacked receitas acima
        gas_cat = (dff[dff["valor"] < 0].groupby(["mes","categoria"])["valor"]
                   .sum().reset_index().sort_values("mes"))
        gas_cat["valor_abs"] = gas_cat["valor"].abs()
        rec_cat = (dff[dff["valor"] > 0].groupby(["mes","categoria"])["valor"]
                   .sum().reset_index().sort_values("mes"))
        # order gastos categories by mean — largest at bottom
        gas_order = (gas_cat.groupby("categoria")["valor_abs"]
                     .median().sort_values(ascending=False).index.tolist())
        colors = get_colors()
        fig_ev = go.Figure()
        # gastos (negative stack) — largest mean at bottom = first added
        for i, cat in enumerate(gas_order):
            sub = gas_cat[gas_cat["categoria"] == cat]
            fig_ev.add_bar(x=sub["mes"], y=-sub["valor_abs"], name=f"↓ {cat}",
                           marker_color=colors[i % len(colors)], opacity=0.85,
                           hovertemplate=f"<b>%{{x}}</b><br>{cat}<br>R$ %{{customdata:,.2f}}<extra></extra>",
                           customdata=sub["valor_abs"])
        # receitas (positive stack)
        for i, cat in enumerate(rec_cat["categoria"].unique()):
            sub = rec_cat[rec_cat["categoria"] == cat]
            fig_ev.add_bar(x=sub["mes"], y=sub["valor"], name=f"↑ {cat}",
                           marker_color=colors[(i + 4) % len(colors)], opacity=0.6,
                           hovertemplate=f"<b>%{{x}}</b><br>{cat}<br>R$ %{{y:,.2f}}<extra></extra>")
        fig_ev.add_hline(y=0, line_color="#444", line_width=1)
        fig_ev.update_layout(**build_plotly_theme(), height=460, bargap=0.2, barmode="relative",
                             legend=dict(orientation="h", yanchor="bottom", y=1.02, font=dict(size=10)))
        st.plotly_chart(fig_ev, width='stretch')
    else:
        por_mes_cat = (dff.groupby(["mes","categoria"])["valor_abs"]
                       .sum().reset_index().sort_values("mes"))
        meses_u = sorted(por_mes_cat["mes"].unique())
        # largest mean at bottom = added first
        cat_order = (por_mes_cat.groupby("categoria")["valor_abs"]
                     .median().sort_values(ascending=False).index.tolist())
        colors = get_colors()
        fig_ev = go.Figure()
        for i, cat in enumerate(cat_order):
            sub = por_mes_cat[por_mes_cat["categoria"] == cat]
            # fill missing months with 0
            sub = (pd.DataFrame({"mes": meses_u})
                   .merge(sub[["mes","valor_abs"]], on="mes", how="left")
                   .fillna(0))
            fig_ev.add_bar(x=sub["mes"], y=sub["valor_abs"], name=cat,
                           marker_color=colors[i % len(colors)],
                           hovertemplate=f"<b>%{{x}}</b><br>{cat}<br>R$ %{{y:,.2f}}<extra></extra>")
        fig_ev.update_layout(**build_plotly_theme(), height=420, bargap=0.25,
                             barmode="stack",
                             legend=dict(orientation="h", yanchor="bottom", y=1.02, font=dict(size=11)))
        st.plotly_chart(fig_ev, width='stretch')

# ── Barra deslizante de período (quando ativada no dropdown) ───────────────────
if preset == "Barra deslizante" and len(_meses_disp) > 1:
    st.select_slider(
        "Arraste para definir o período",
        options=_meses_disp,
        value=st.session_state.get("range_slider", (_meses_disp[0], _meses_disp[-1])),
        key="range_slider",
    )

# ── Networth ──────────────────────────────────────────────────────────────────
st.divider()
st.markdown("<p style='color:#555;font-size:0.75rem;font-family:DM Mono,monospace;text-transform:uppercase;letter-spacing:0.08em;'>Evolução do patrimônio</p>", unsafe_allow_html=True)
if df_saldos.empty:
    st.info("Nenhum dado de saldo ainda — faça upload dos extratos.")
else:
    colors = get_colors()

    # Caixinha acumulada
    caixinha_txns = df[df["descricao"].str.lower().str.contains(
        "aplicação rdb|aplicacao rdb|resgate rdb", na=False
    )].sort_values("data").copy()
    caixinha_txns["caixinha_acum"] = (-caixinha_txns["valor"]).cumsum()

    saldos_sorted = df_saldos.sort_values("data").copy()
    saldos_sorted["networth"] = saldos_sorted["balamt"]

    if not caixinha_txns.empty:
        def caixinha_em(data):
            antes = caixinha_txns[caixinha_txns["data"] <= data]
            return float(antes["caixinha_acum"].iloc[-1]) if not antes.empty else 0.0
        saldos_sorted["caixinha"] = saldos_sorted["data"].apply(caixinha_em)
        saldos_sorted["networth"] = saldos_sorted["balamt"] + saldos_sorted["caixinha"]
    else:
        saldos_sorted["caixinha"] = 0.0

    nw_tab1, nw_tab2, nw_tab3 = st.tabs(["Evolução do patrimônio", "Rendimento mensal", "Rendimento acumulado"])

    with nw_tab1:
        fig_nw = go.Figure()
        fig_nw.add_scatter(
            x=saldos_sorted["data"], y=saldos_sorted["networth"],
            name="Networth", mode="lines+markers",
            line=dict(color=colors[0], width=2), marker=dict(size=6),
            hovertemplate="<b>%{x|%Y-%m-%d}</b><br>Networth: R$ %{y:,.2f}<extra></extra>",
            fill="tozeroy", fillcolor="rgba(200,240,96,0.15)",
        )
        fig_nw.add_scatter(
            x=saldos_sorted["data"], y=saldos_sorted["balamt"],
            name="Conta", mode="lines+markers",
            line=dict(color=colors[1], width=2, dash="dot"), marker=dict(size=5),
            hovertemplate="<b>%{x|%Y-%m-%d}</b><br>Conta: R$ %{y:,.2f}<extra></extra>",
        )
        if saldos_sorted["caixinha"].sum() != 0:
            fig_nw.add_scatter(
                x=saldos_sorted["data"], y=saldos_sorted["caixinha"],
                name="Caixinha (aprox.)", mode="lines+markers",
                line=dict(color=colors[2], width=2, dash="dash"), marker=dict(size=5),
                hovertemplate="<b>%{x|%Y-%m-%d}</b><br>Caixinha: R$ %{y:,.2f}<extra></extra>",
            )
        fig_nw.update_layout(
            **build_plotly_theme(), height=420,
            xaxis_title=None, yaxis_title="R$",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, font=dict(size=11)),
        )
        st.plotly_chart(fig_nw, width='stretch')

        tbl = saldos_sorted[["data","balamt","caixinha","networth"]].copy()
        tbl.columns = ["Data","Conta","Caixinha","Networth"]
        tbl["Data"] = tbl["Data"].dt.date
        for col in ["Conta","Caixinha","Networth"]:
            tbl[col] = tbl[col].map(fmt_brl)
        st.dataframe(tbl.sort_values("Data", ascending=False).reset_index(drop=True),
                     width='stretch', height=280)

    with nw_tab2:
        rend = saldos_sorted[saldos_sorted["rendimento_conta"].notna()].copy()
        if rend.empty:
            st.info("Nenhum dado de rendimento ainda — re-faça o upload dos extratos para popular.")
        else:
            fig_rend = go.Figure()
            fig_rend.add_bar(
                x=rend["data"], y=rend["rendimento_conta"],
                marker_color=colors[0], marker_line_width=0,
                hovertemplate="<b>%{x|%Y-%m-%d}</b><br>Rendimento: R$ %{y:,.2f}<extra></extra>",
            )
            fig_rend.update_layout(
                **build_plotly_theme(), height=380, bargap=0.3,
                xaxis_title=None, yaxis_title="R$", showlegend=False,
            )
            st.plotly_chart(fig_rend, width='stretch')

            total_rend = rend["rendimento_conta"].sum()
            media_rend = rend["rendimento_conta"].mean()
            rc1, rc2 = st.columns(2)
            rc1.metric("Total rendido (conta)", fmt_brl(total_rend))
            rc2.metric("Média mensal", fmt_brl(media_rend))

            tbl_r = rend[["data","rendimento_conta"]].copy()
            tbl_r.columns = ["Data","Rendimento"]
            tbl_r["Data"] = tbl_r["Data"].dt.date
            tbl_r["Rendimento"] = tbl_r["Rendimento"].map(fmt_brl)
            st.dataframe(tbl_r.sort_values("Data", ascending=False).reset_index(drop=True),
                         width='stretch', height=280)

    with nw_tab3:
        rend = saldos_sorted[saldos_sorted["rendimento_conta"].notna()].copy()
        if rend.empty:
            st.info("Nenhum dado de rendimento ainda — re-faça o upload dos extratos para popular.")
        else:
            rend = rend.sort_values("data")
            rend["rendimento_acum"] = rend["rendimento_conta"].cumsum()
            fig_acum = go.Figure()
            fig_acum.add_scatter(
                x=rend["data"], y=rend["rendimento_acum"],
                name="Rendimento acumulado", mode="lines+markers",
                line=dict(color=colors[0], width=2), marker=dict(size=6),
                fill="tozeroy", fillcolor="rgba(200,240,96,0.12)",
                hovertemplate="<b>%{x|%Y-%m-%d}</b><br>Acumulado: R$ %{y:,.2f}<extra></extra>",
            )
            fig_acum.update_layout(
                **build_plotly_theme(), height=380,
                xaxis_title=None, yaxis_title="R$", showlegend=False,
            )
            st.plotly_chart(fig_acum, width='stretch')
            st.metric("Total acumulado", fmt_brl(rend["rendimento_acum"].iloc[-1]))

with tab4:
    # aplica filtro de tipo mas mantém reembolsados visíveis
    if tipo == "Gastos":
        show_raw = dff_tabela[dff_tabela["valor"] < 0].copy()
    elif tipo == "Receitas":
        show_raw = dff_tabela[dff_tabela["valor"] > 0].copy()
    else:
        show_raw = dff_tabela.copy()
    show_raw = show_raw[["data","descricao","categoria","valor","origem","reembolsado"]].sort_values("data", ascending=False).reset_index(drop=True)
    show = show_raw.copy()
    show["valor_fmt"] = show["valor"].map(fmt_brl_signed)
    show_display = show.drop(columns=["valor"]).rename(columns={
        "data":"Data","descricao":"Descrição","categoria":"Categoria",
        "valor_fmt":"Valor","origem":"Origem"
    })

    def style_row(row):
        # reembolsados ficam cinza fraco em toda a linha
        if row["reembolsado"]:
            return ["color: #555"] * len(row)
        styles = [""] * len(row)
        # cor no valor
        val_idx = list(row.index).index("Valor")
        if str(row["Valor"]).startswith("- "):
            styles[val_idx] = "color: #ff6b6b"
        else:
            styles[val_idx] = "color: #a8e063"
        return styles

    styled = show_display.style.apply(style_row, axis=1)
    # esconde a coluna auxiliar reembolsado
    styled = styled.hide(axis="columns", subset=["reembolsado"])

    st.dataframe(styled, width='stretch', height=480)
    n_reemb = show_raw["reembolsado"].sum()
    if n_reemb > 0:
        st.markdown(f"<p style='color:#555;font-size:0.75rem;font-family:DM Mono,monospace;'>{n_reemb} transação(ões) em cinza = reembolso casado, neutralizado dos cálculos</p>", unsafe_allow_html=True)
    st.download_button("⬇ baixar transações (.xlsx)",
                       df_to_xlsx(show_raw.rename(columns={"data":"Data","descricao":"Descrição","categoria":"Categoria","valor":"Valor","origem":"Origem","reembolsado":"Reembolsado"})),
                       "transacoes.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
