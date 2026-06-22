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

# ── Cores fixas por categoria (baseado no tema Lima Escuro) ───────────────────
# ── Cores fixas por categoria (paleta escurecida/dessaturada, hues espaçados) ──
# Critério: cada categoria tem um hue temático próprio, dessaturado pra combinar
# com o tema dark. iFood mantido no vermelho assinatura da marca.
CATEGORY_COLORS = {
    "iFood":                 "#cc2222",  # vermelho iFood (marca)
    "Alimentação & Mercado": "#7a9e3e",  # verde-oliva (comida/mercado)
    "Telecom":               "#4a6fa5",  # azul-acinzentado (comunicação)
    "Compras":               "#b05ca0",  # magenta acinzentado
    "Serviços":              "#5b7a8c",  # azul-petróleo neutro
    "Outros":                "#6b6b6b",  # cinza neutro (categoria "lixo")
    "Saúde":                 "#3f9e7a",  # verde-água (saúde/farmácia)
    "Assinaturas":           "#8a5fc4",  # roxo (digital/streaming)
    "Transporte":            "#3f8fb5",  # azul (mobilidade)
    "Vícios & Conveniência": "#c4923f",  # âmbar/tabaco
    "Vestuário":             "#c46a8a",  # rosa-queimado (moda)
    "Lazer":                 "#c46a3f",  # laranja-terracota (diversão)
    "Impostos":              "#9e3f3f",  # vermelho-tijolo (obrigação)
    "Transferências":        "#7a8a99",  # cinza-azulado (neutro/movimento)
    "Profissional":          "#4a8a6a",  # verde-musgo (trabalho)
    "Investimento":          "#6a9e3f",  # verde-limão escurecido (crescimento)
    "Bolsa Residência":      "#3f9e5c",  # verde-esmeralda
    "Pagamento de Fatura":   "#454545",  # cinza escuro neutro
    "Crédito de Fatura":     "#555f55",  # cinza esverdeado
}

# Fallback cíclico pra categorias não mapeadas — evita que tudo caia
# no mesmo cinza quando surgir uma categoria nova no futuro.
_FALLBACK_CYCLE = ["#8899aa", "#aa8899", "#99aa88", "#aa9988", "#8899cc", "#cc9988"]

def cat_color(categoria: str) -> str:
    if categoria in CATEGORY_COLORS:
        return CATEGORY_COLORS[categoria]
    idx = abs(hash(categoria)) % len(_FALLBACK_CYCLE)
    return _FALLBACK_CYCLE[idx]

def cat_colors_list(categorias: list) -> list:
    return [cat_color(c) for c in categorias]


from pluggy_client import PluggyClient, transactions_to_df

@st.cache_resource
def get_pluggy():
    c = PluggyClient(st.secrets["pluggy"]["client_id"],
                     st.secrets["pluggy"]["client_secret"])
    c.authenticate()
    return c


# ─────────────────────────────────────────────────────────────────────────────────────

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
    "ifd *zamp" : "iFood",
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
    "claude" : "Assinaturas",
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

# Fallback: quando guess_category() não reconhece a descrição ("Outros"),
# usa a categoria do Pluggy traduzida como aproximação.
PLUGGY_CAT_FALLBACK = {
    "Tax on financial operations": "Impostos",
    "Transfers": "Transferências",
    "Same person transfer": "Transferências",
    "Investments": "Investimento",
    "Services": "Serviços",
    "Digital services": "Assinaturas",
    "Travel": "Lazer",
    "Hospital clinics and labs": "Saúde",
    "Office supplies": "Compras",
    "Electronics": "Compras",
    "Clothing": "Vestuário",
    "Gas stations": "Vícios & Conveniência",
    "Cinema, theater and concerts": "Lazer",
    "Shopping": "Compras",
    "Leisure": "Lazer",
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

def guess_category(desc: str, valor: float = 0.0, pluggy_cat: str = None) -> str:
    import re
    d = desc.lower()

    if "pagamento de fatura" in d:
        return "Pagamento de Fatura"

    # Bolsa residência: transferência recebida de Lucas Oltramari com valor próximo de 4750
    if ("transferência recebida" in d or "transferencia recebida" in d) and \
       "lucas oltramari" in d and 4500 <= abs(valor) <= 5000:
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
        return "Transferências"

    # Fallback: usa categoria do Pluggy traduzida, se disponível
    if pluggy_cat and pluggy_cat in PLUGGY_CAT_FALLBACK:
        return PLUGGY_CAT_FALLBACK[pluggy_cat]

    return "Outros"

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

@st.cache_data(ttl=300)
def load_from_pluggy() -> pd.DataFrame:
    """Carrega transações via Pluggy e mapeia pro schema interno
    (data, descricao, valor, categoria, mes, origem)."""
    item_ids = st.secrets["pluggy"]["item_id"]
    if isinstance(item_ids, str):
        item_ids = [item_ids]

    client = get_pluggy()
    frames = []
    for item_id in item_ids:
        raw_txns = client.all_transactions(item_id)
        if raw_txns:
            frames.append(transactions_to_df(raw_txns))
    if not frames:
        return pd.DataFrame()

    df_raw = pd.concat(frames, ignore_index=True).drop_duplicates(subset=["id"])

    df = pd.DataFrame()
    df["data"] = pd.to_datetime(df_raw["date"], utc=True).dt.tz_localize(None)
    df["descricao"] = df_raw["description"]
    # Valor real em BRL: usa amountInAccountCurrency quando disponível (cobre
    # transações em moeda estrangeira, ex. assinaturas em USD, onde "amount"
    # vem na moeda original e não reflete o valor cobrado). Cai pra "amount"
    # quando o campo não existe ou vem nulo (transações já em BRL).
    if "amountInAccountCurrency" in df_raw.columns:
        valor_brl = df_raw["amountInAccountCurrency"].fillna(df_raw["amount"])
    else:
        valor_brl = df_raw["amount"]
    # Sinal: na conta (Nu Pagamentos) o sinal do Pluggy já segue a convenção
    # (CREDIT positivo = receita, DEBIT negativo = gasto). No cartão
    # (platinum) é o inverso (DEBIT positivo = gasto, CREDIT negativo =
    # pagamento/crédito de fatura), então invertemos.
    is_cartao = df_raw["accountName"].str.lower() == "platinum"
    df["valor"] = valor_brl.where(~is_cartao, -valor_brl)
    df["origem"] = is_cartao.map({True: "fatura", False: "extrato"})
    df["mes"] = df["data"].dt.to_period("M").astype(str)
    df["categoria"] = [
        guess_category(desc, val, pcat)
        for desc, val, pcat in zip(df["descricao"], df["valor"], df_raw["category"])
    ]
    df["pluggy_id"] = df_raw["id"]
    df["accountName"] = df_raw["accountName"]

    df = df.sort_values("data").reset_index(drop=True)
    df["id"] = df.index
    return df

@st.cache_data(ttl=300)
def load_from_supabase_historico(antes_de: pd.Timestamp) -> pd.DataFrame:
    """Carrega do Supabase apenas as transações anteriores ao início do range
    do Pluggy, evitando sobreposição."""
    sb = get_supabase()
    corte = antes_de.strftime("%Y-%m-%d")
    all_rows = []
    page_size = 1000
    offset = 0
    while True:
        res = (
            sb.table("transacoes")
            .select("*")
            .lt("data", corte)
            .range(offset, offset + page_size - 1)
            .execute()
        )
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
    df["categoria"] = df.apply(
        lambda r: guess_category(r["descricao"], r["valor"]), axis=1
    )
    if "reembolsado" not in df.columns:
        df["reembolsado"] = False
    df["fonte"] = "supabase"
    return df

def load_transactions() -> pd.DataFrame:
    """Fonte combinada: Supabase (histórico) + Pluggy (recente).
    Retorna df com coluna 'fonte' = 'supabase' | 'pluggy'."""
    df_pluggy = load_from_pluggy()

    if df_pluggy.empty:
        df_hist = load_from_supabase_historico(pd.Timestamp("2100-01-01"))
        if df_hist.empty:
            return pd.DataFrame()
        df_hist["fonte"] = "supabase"
        df_hist = detectar_reembolsos(df_hist)
        return df_hist

    pluggy_inicio = df_pluggy["data"].min()
    df_pluggy["fonte"] = "pluggy"

    df_hist = load_from_supabase_historico(pluggy_inicio)

    if df_hist.empty:
        df_pluggy = detectar_reembolsos(df_pluggy)
        return df_pluggy

    cols_comuns = ["data", "descricao", "valor", "categoria", "mes", "origem", "fonte"]
    df_hist_clean = df_hist[[c for c in cols_comuns if c in df_hist.columns]].copy()
    df_pluggy_clean = df_pluggy[[c for c in cols_comuns if c in df_pluggy.columns]].copy()

    df_combined = pd.concat([df_hist_clean, df_pluggy_clean], ignore_index=True)
    df_combined = df_combined.sort_values("data").reset_index(drop=True)
    df_combined = detectar_reembolsos(df_combined)
    return df_combined, pluggy_inicio, len(df_hist_clean), len(df_pluggy_clean)


@st.cache_data(ttl=300)
def load_saldo_pluggy() -> dict:
    """Lê saldo atual das contas e investimentos via Pluggy.
    Retorna dict com: conta, investimentos, fatura_cartao, atualizado_em."""
    item_ids = st.secrets["pluggy"]["item_id"]
    if isinstance(item_ids, str):
        item_ids = [item_ids]

    resultado = {
        "conta": None,
        "caixinha": 0.0,        # amountWithdrawal do CDB (líquido de IR)
        "fatura_cartao": None,
        "atualizado_em": None,
        "caixinha_detalhe": [],  # lista de {nome, valor} pra mini-painel
    }

    for item_id in item_ids:
        client = get_pluggy()

        for acc in client.get_accounts(item_id):
            acc_type = acc.get("type", "")
            subtype  = acc.get("subtype", "")
            balance  = acc.get("balance")
            updated  = acc.get("updatedAt")

            if acc_type == "BANK" and subtype == "CHECKING_ACCOUNT":
                resultado["conta"] = balance
                if updated:
                    resultado["atualizado_em"] = updated

            elif acc_type == "CREDIT" and subtype == "CREDIT_CARD":
                resultado["fatura_cartao"] = balance

        # Investimentos: usa amountWithdrawal (líquido de IR) quando disponível
        investments_raw = client._get("/investments", {"itemId": item_id}).get("results", [])
        for inv in investments_raw:
            if inv.get("status") != "ACTIVE":
                continue
            valor = inv.get("amountWithdrawal") or inv.get("balance") or 0.0
            resultado["caixinha"] += valor
            resultado["caixinha_detalhe"].append({
                "nome": inv.get("name", "Investimento"),
                "tipo": inv.get("subtype", inv.get("type", "")),
                "valor": valor,
            })

    return resultado


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
    if "rendimento_caixinha" not in df.columns:
        df["rendimento_caixinha"] = None
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

# ── Categoria overrides ───────────────────────────────────────────────────────
# Tabela Supabase: categoria_overrides
#   descricao TEXT NOT NULL
#   data      DATE NOT NULL DEFAULT '0001-01-01'  ← sentinela = "todas"
#   categoria TEXT NOT NULL
#   PRIMARY KEY (descricao, data)
#
# DDL:
#   create table categoria_overrides (
#     descricao text not null,
#     data      date not null default '0001-01-01',
#     categoria text not null,
#     primary key (descricao, data)
#   );

_SENTINELA = "0001-01-01"  # data especial = override geral ("todas")

@st.cache_data(ttl=60)
def load_categoria_overrides() -> pd.DataFrame:
    sb = get_supabase()
    res = sb.table("categoria_overrides").select("*").execute()
    if not res.data:
        return pd.DataFrame(columns=["descricao", "data", "categoria"])
    df = pd.DataFrame(res.data)
    # Mantém data como string pura — evita conversão datetime que quebraria a sentinela
    df["data"] = df["data"].astype(str)
    return df

def save_categoria_override(descricao: str, categoria: str, data_str=None):
    """data_str = 'YYYY-MM-DD' pra override individual, None pra todas."""
    row = {
        "descricao": descricao,
        "categoria": categoria,
        "data": data_str if data_str else _SENTINELA,
    }
    get_supabase().table("categoria_overrides").upsert(
        row, on_conflict="descricao,data"
    ).execute()
    load_categoria_overrides.clear()

def apply_categoria_overrides(df: pd.DataFrame, overrides: pd.DataFrame) -> pd.DataFrame:
    """Aplica overrides ao df. Override específico (com data) tem precedência sobre geral."""
    if overrides.empty or df.empty:
        return df
    df = df.copy()
    df["_data_str"] = df["data"].dt.strftime("%Y-%m-%d")

    # Overrides gerais (data == sentinela)
    gerais = overrides[overrides["data"] == _SENTINELA].set_index("descricao")["categoria"].to_dict()
    # Overrides específicos (data != sentinela)
    especificos = {}
    for _, row in overrides[overrides["data"] != _SENTINELA].iterrows():
        especificos[(row["descricao"], row["data"])] = row["categoria"]

    def resolve(row):
        key_esp = (row["descricao"], row["_data_str"])
        if key_esp in especificos:
            return especificos[key_esp]
        if row["descricao"] in gerais:
            return gerais[row["descricao"]]
        return row["categoria"]

    df["categoria"] = df.apply(resolve, axis=1)
    return df.drop(columns=["_data_str"])

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
try:
    result = load_transactions()
    if isinstance(result, tuple):
        df, _pluggy_inicio, _n_hist, _n_pluggy = result
        _load_debug = {
            "pluggy_inicio": _pluggy_inicio,
            "n_supabase": _n_hist,
            "n_pluggy": _n_pluggy,
            "n_total": len(df),
        }
    else:
        df = result
        _load_debug = None
except Exception as e:
    st.error(f"Erro ao buscar dados: {e}")
    import traceback
    st.code(traceback.format_exc())
    st.stop()

df_saldos = load_saldos()
saldo_pluggy = load_saldo_pluggy()
prefs = load_prefs()
df_cat_overrides = load_categoria_overrides()
df = apply_categoria_overrides(df, df_cat_overrides)

# ── Persistência diária do Pluggy no Supabase ─────────────────────────────────
def save_caixinha(data: str, valor: float):
    get_supabase().table("caixinha_historico").upsert(
        {"data": data, "valor": valor}, on_conflict="data"
    ).execute()

def save_fatura(data: str, valor: float):
    get_supabase().table("fatura_historico").upsert(
        {"data": data, "valor": valor}, on_conflict="data"
    ).execute()

@st.cache_data(ttl=300)
def load_caixinha_historico() -> pd.DataFrame:
    res = get_supabase().table("caixinha_historico").select("*").order("data").execute()
    if not res.data:
        return pd.DataFrame(columns=["data", "valor"])
    df = pd.DataFrame(res.data)
    df["data"] = pd.to_datetime(df["data"])
    return df

@st.cache_data(ttl=300)
def load_fatura_historico() -> pd.DataFrame:
    res = get_supabase().table("fatura_historico").select("*").order("data").execute()
    if not res.data:
        return pd.DataFrame(columns=["data", "valor"])
    df = pd.DataFrame(res.data)
    df["data"] = pd.to_datetime(df["data"])
    return df

# Roda uma vez por sessão
if saldo_pluggy.get("conta") is not None and "saldo_pluggy_salvo" not in st.session_state:
    import datetime as _dt
    _hoje = _dt.date.today().isoformat()
    try:
        # Conta corrente → tabela saldos (existente)
        save_saldo(_hoje, {"balamt": saldo_pluggy["conta"]}, "pluggy")
        load_saldos.clear()
        df_saldos = load_saldos()
        # Caixinha (CDB) → tabela nova
        if saldo_pluggy.get("caixinha"):
            save_caixinha(_hoje, saldo_pluggy["caixinha"])
            load_caixinha_historico.clear()
        # Fatura do cartão → tabela nova
        if saldo_pluggy.get("fatura_cartao") is not None:
            save_fatura(_hoje, saldo_pluggy["fatura_cartao"])
            load_fatura_historico.clear()
    except Exception:
        pass
    st.session_state["saldo_pluggy_salvo"] = True

df_caixinha_hist = load_caixinha_historico()
df_fatura_hist   = load_fatura_historico()


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
col_h1, col_h2 = st.columns([5, 1])
with col_h1:
    st.title("💸 controle de gastos")
    st.markdown("<p class='upload-hint'>dados sincronizados via Pluggy (Open Finance)</p>",
                unsafe_allow_html=True)
with col_h2:
    if st.button("🔄 atualizar", width='stretch'):
        load_from_pluggy.clear()
        load_from_supabase_historico.clear()
        load_saldo_pluggy.clear()
        load_caixinha_historico.clear()
        load_fatura_historico.clear()
        st.rerun()
st.divider()

# ── Debug de fontes ───────────────────────────────────────────────────────────
with st.expander("🔍 diagnóstico de fontes", expanded=False):
    if _load_debug:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Pluggy início", str(_load_debug["pluggy_inicio"].date()))
        c2.metric("Supabase (histórico)", _load_debug["n_supabase"])
        c3.metric("Pluggy (recente)", _load_debug["n_pluggy"])
        c4.metric("Total combinado", _load_debug["n_total"])
    else:
        st.info("Apenas uma fonte ativa (sem combinação).")

    if not df.empty and "fonte" in df.columns:
        st.markdown("**Distribuição por fonte e mês:**")
        pivot = (
            df.groupby(["mes", "fonte"])
            .size()
            .unstack(fill_value=0)
            .sort_index()
        )
        st.dataframe(pivot, use_container_width=True)

        st.markdown("**Datas extremas por fonte:**")
        extremos = df.groupby("fonte")["data"].agg(["min", "max"]).reset_index()
        extremos.columns = ["fonte", "mais antiga", "mais recente"]
        extremos["mais antiga"] = extremos["mais antiga"].dt.date
        extremos["mais recente"] = extremos["mais recente"].dt.date
        st.dataframe(extremos, use_container_width=True)

if df.empty:
    st.markdown("""
    <div style='text-align:center; padding: 4rem 0; color: #333;'>
        <div style='font-size: 3rem;'>📂</div>
        <div style='font-family: DM Mono, monospace; font-size: 0.85rem; margin-top: 1rem;'>
            nenhum dado retornado pelo Pluggy ainda
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
        if st.button("🗑 Apagar dados de saldo"):
            st.session_state.confirm_delete = True
            st.rerun()
    else:
        st.warning("Tem certeza? Isso apaga os saldos registrados (transações vêm do Pluggy e não são afetadas).")
        col_c, col_d = st.columns(2)
        if col_c.button("✓ Sim", width='stretch'):
            get_supabase().table("saldos").delete().neq("id", 0).execute()
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

_pluggy_conta   = saldo_pluggy.get("conta")
_pluggy_caixinha = saldo_pluggy.get("caixinha", 0.0)
_pluggy_cx_det  = saldo_pluggy.get("caixinha_detalhe", [])
_pluggy_fatura  = saldo_pluggy.get("fatura_cartao")
_pluggy_updated = saldo_pluggy.get("atualizado_em")

# Fallback legacy: caixinha calculada pelas transações de RDB
caixinha_mask = df["descricao"].str.lower().str.contains("aplicação rdb|aplicacao rdb|resgate rdb", na=False)
saldo_caixinha_txns = -df[caixinha_mask]["valor"].sum()

if _pluggy_conta is not None:
    balamt_recente   = _pluggy_conta
    saldo_caixinha   = _pluggy_caixinha
    networth         = balamt_recente + saldo_caixinha - (_pluggy_fatura or 0)
    networth_label   = fmt_brl(networth)
    _saldo_fonte     = "pluggy"
elif not df_saldos.empty:
    balamt_recente   = float(df_saldos.sort_values("data").iloc[-1]["balamt"])
    saldo_caixinha   = saldo_caixinha_txns
    networth         = balamt_recente + saldo_caixinha
    networth_label   = fmt_brl(networth)
    _saldo_fonte     = "supabase"
else:
    balamt_recente   = None
    saldo_caixinha   = saldo_caixinha_txns
    networth_label   = "—"
    _saldo_fonte     = None

c1, c2, c3 = st.columns(3)
c1.metric("Networth aprox.", networth_label)
c2.metric("Conta",           fmt_brl(balamt_recente) if balamt_recente is not None else "—")
c3.metric("Caixinha",        fmt_brl(saldo_caixinha))

# Linha discreta: gasto/recebido/saldo do período + transações (menos proeminentes, só do período)
st.markdown(
    f"""<div style='display:flex;gap:1.5rem;margin:0.3rem 0 0.2rem;flex-wrap:wrap;'>
    <div style='color:#555;font-size:0.78rem;font-family:DM Mono,monospace;'>
        gasto no período: <span style='color:#ff8a8a'>{fmt_brl(gastos)}</span>
    </div>
    <div style='color:#555;font-size:0.78rem;font-family:DM Mono,monospace;'>
        recebido no período: <span style='color:#a8e063'>{fmt_brl(receitas)}</span>
    </div>
    <div style='color:#555;font-size:0.78rem;font-family:DM Mono,monospace;'>
        saldo período: <span style='color:#e8e8e0'>{fmt_brl_signed(saldo)}</span>
    </div>
    <div style='color:#555;font-size:0.78rem;font-family:DM Mono,monospace;'>
        {len(dff_total)} transações
    </div>
    </div>""",
    unsafe_allow_html=True
)

# Mini-painel de patrimônio
# Mini-painel: fatura + data de atualização (conta/caixinha já estão em destaque acima)
if _saldo_fonte or _pluggy_fatura is not None:
    _atualizado_str = (
        f"<div style='color:#555;font-size:0.75rem;font-family:DM Mono,monospace;'>🕐 atualizado: <span style='color:#e8e8e0'>{str(_pluggy_updated)[:10]}</span></div>"
        if _pluggy_updated else
        (f"<div style='color:#555;font-size:0.75rem;font-family:DM Mono,monospace;'>📅 saldo em: <span style='color:#e8e8e0'>{str(df_saldos.sort_values('data').iloc[-1]['data'].date())}</span></div>"
         if not df_saldos.empty else "")
    )
    _fatura_str = (
        f"<div style='color:#555;font-size:0.75rem;font-family:DM Mono,monospace;'>💳 fatura: <span style='color:#ff6b6b'>{fmt_brl(_pluggy_fatura)}</span></div>"
        if _pluggy_fatura is not None else ""
    )
    st.markdown(
        f"""<div style='display:flex;gap:1.5rem;margin:0.5rem 0 0.2rem;flex-wrap:wrap;'>
        {_fatura_str}
        {_atualizado_str}
        </div>""",
        unsafe_allow_html=True
    )
st.divider()

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Por mês", "Por categoria", "Evolução", "Transações", "Saldo & Projeção"])

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
                            orientation="h",
                            marker_color=cat_colors_list(por_cat["categoria"].tolist()),
                            marker_line_width=0,
                            hovertemplate="<b>%{y}</b><br>R$ %{x:,.2f}<extra></extra>")
            fig_bar.update_layout(**build_plotly_theme(), height=380,
                                  xaxis_title="R$", yaxis_title=None, showlegend=False)
            st.plotly_chart(fig_bar, width='stretch')
        with col_b:
            fig_pie = px.pie(por_cat, values="valor_abs", names="categoria",
                             hole=0.55,
                             color="categoria",
                             color_discrete_map=CATEGORY_COLORS)
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
        fig_ev = go.Figure()
        # gastos (negative stack) — largest mean at bottom = first added
        for cat in gas_order:
            sub = gas_cat[gas_cat["categoria"] == cat]
            fig_ev.add_bar(x=sub["mes"], y=-sub["valor_abs"], name=f"↓ {cat}",
                           marker_color=cat_color(cat), opacity=0.85,
                           hovertemplate=f"<b>%{{x}}</b><br>{cat}<br>R$ %{{customdata:,.2f}}<extra></extra>",
                           customdata=sub["valor_abs"])
        # receitas (positive stack)
        for cat in rec_cat["categoria"].unique():
            sub = rec_cat[rec_cat["categoria"] == cat]
            fig_ev.add_bar(x=sub["mes"], y=sub["valor"], name=f"↑ {cat}",
                           marker_color=cat_color(cat), opacity=0.6,
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
        fig_ev = go.Figure()
        for cat in cat_order:
            sub = por_mes_cat[por_mes_cat["categoria"] == cat]
            # fill missing months with 0
            sub = (pd.DataFrame({"mes": meses_u})
                   .merge(sub[["mes","valor_abs"]], on="mes", how="left")
                   .fillna(0))
            fig_ev.add_bar(x=sub["mes"], y=sub["valor_abs"], name=cat,
                           marker_color=cat_color(cat),
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
    st.info("Nenhum dado de saldo ainda.")
else:
    colors = get_colors()

    saldos_sorted = df_saldos.sort_values("data").copy()

    # Caixinha: tabela nova tem prioridade; fallback via transações RDB acumuladas
    if not df_caixinha_hist.empty:
        saldos_sorted = saldos_sorted.merge(
            df_caixinha_hist[["data", "valor"]].rename(columns={"valor": "caixinha"}),
            on="data", how="left"
        )
        saldos_sorted["caixinha"] = saldos_sorted["caixinha"].fillna(0.0)
    else:
        caixinha_txns = df[df["descricao"].str.lower().str.contains(
            "aplicação rdb|aplicacao rdb|resgate rdb", na=False
        )].sort_values("data").copy()
        if not caixinha_txns.empty:
            caixinha_txns["caixinha_acum"] = (-caixinha_txns["valor"]).cumsum()
            def caixinha_em(data):
                antes = caixinha_txns[caixinha_txns["data"] <= data]
                return float(antes["caixinha_acum"].iloc[-1]) if not antes.empty else 0.0
            saldos_sorted["caixinha"] = saldos_sorted["data"].apply(caixinha_em)
        else:
            saldos_sorted["caixinha"] = 0.0

    # Fatura
    if not df_fatura_hist.empty:
        saldos_sorted = saldos_sorted.merge(
            df_fatura_hist[["data", "valor"]].rename(columns={"valor": "fatura"}),
            on="data", how="left"
        )
        saldos_sorted["fatura"] = saldos_sorted["fatura"].fillna(0.0)
    else:
        saldos_sorted["fatura"] = 0.0

    saldos_sorted["networth"] = (
        saldos_sorted["balamt"] + saldos_sorted["caixinha"] - saldos_sorted["fatura"]
    )

    # Injeta ponto atual do Pluggy
    if _pluggy_conta is not None:
        import datetime as _dt2
        _hoje_ts = pd.Timestamp(_dt2.date.today())
        _ponto_atual = pd.DataFrame([{
            "data": _hoje_ts,
            "balamt": _pluggy_conta,
            "caixinha": _pluggy_caixinha,
            "fatura": _pluggy_fatura or 0.0,
            "networth": _pluggy_conta + _pluggy_caixinha - (_pluggy_fatura or 0),
            "rendimento_conta": None,
            "origem": "pluggy",
        }])
        saldos_sorted = pd.concat([saldos_sorted, _ponto_atual], ignore_index=True)
        saldos_sorted = saldos_sorted.drop_duplicates(subset=["data"], keep="last").sort_values("data")

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
                name="Caixinha", mode="lines+markers",
                line=dict(color=colors[2], width=2, dash="dash"), marker=dict(size=5),
                hovertemplate="<b>%{x|%Y-%m-%d}</b><br>Caixinha: R$ %{y:,.2f}<extra></extra>",
            )
        if saldos_sorted["fatura"].sum() != 0:
            fig_nw.add_scatter(
                x=saldos_sorted["data"], y=saldos_sorted["fatura"],
                name="Fatura cartão", mode="lines+markers",
                line=dict(color="#ff4444", width=2, dash="dashdot"),
                marker=dict(size=5, symbol="x", color="#ff4444"),
                hovertemplate="<b>%{x|%Y-%m-%d}</b><br>Fatura: R$ %{y:,.2f}<extra></extra>",
            )
        fig_nw.update_layout(
            **build_plotly_theme(), height=420,
            xaxis_title=None, yaxis_title="R$",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, font=dict(size=11)),
        )
        st.plotly_chart(fig_nw, width='stretch')

        tbl = saldos_sorted[["data","balamt","caixinha","fatura","networth"]].copy()
        tbl.columns = ["Data","Conta","Caixinha","Fatura","Networth"]
        tbl["Data"] = tbl["Data"].dt.date
        for col in ["Conta","Caixinha","Fatura","Networth"]:
            tbl[col] = tbl[col].map(fmt_brl)
        st.dataframe(tbl.sort_values("Data", ascending=False).reset_index(drop=True),
                     width='stretch', height=280)

    with nw_tab2:
        rend = saldos_sorted[saldos_sorted["rendimento_conta"].notna()].copy()
        if rend.empty:
            st.info("Nenhum dado de rendimento ainda.")
        else:
            # garante coluna caixinha
            if "rendimento_caixinha" not in rend.columns:
                rend["rendimento_caixinha"] = 0.0
            rend["rendimento_caixinha"] = rend["rendimento_caixinha"].fillna(0.0)

            fig_rend = go.Figure()
            fig_rend.add_bar(
                x=rend["data"], y=rend["rendimento_conta"],
                name="Conta", marker_color=colors[0], marker_line_width=0,
                hovertemplate="<b>%{x|%Y-%m-%d}</b><br>Conta: R$ %{y:,.2f}<extra></extra>",
            )
            if rend["rendimento_caixinha"].sum() > 0:
                fig_rend.add_bar(
                    x=rend["data"], y=rend["rendimento_caixinha"],
                    name="Caixinha", marker_color=colors[2], marker_line_width=0,
                    hovertemplate="<b>%{x|%Y-%m-%d}</b><br>Caixinha: R$ %{y:,.2f}<extra></extra>",
                )
            fig_rend.update_layout(
                **build_plotly_theme(), height=380, bargap=0.3, barmode="stack",
                xaxis_title=None, yaxis_title="R$",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, font=dict(size=11)),
            )
            st.plotly_chart(fig_rend, width='stretch')

            total_conta   = rend["rendimento_conta"].sum()
            total_caixinha = rend["rendimento_caixinha"].sum()
            total_geral   = total_conta + total_caixinha
            media_geral   = (rend["rendimento_conta"] + rend["rendimento_caixinha"]).mean()
            rc1, rc2, rc3, rc4 = st.columns(4)
            rc1.metric("Total conta",    fmt_brl(total_conta))
            rc2.metric("Total caixinha", fmt_brl(total_caixinha))
            rc3.metric("Total geral",    fmt_brl(total_geral))
            rc4.metric("Média mensal",   fmt_brl(media_geral))

            tbl_r = rend[["data","rendimento_conta","rendimento_caixinha"]].copy()
            tbl_r["total"] = tbl_r["rendimento_conta"] + tbl_r["rendimento_caixinha"]
            tbl_r.columns = ["Data","Conta","Caixinha","Total"]
            tbl_r["Data"] = tbl_r["Data"].dt.date
            for col in ["Conta","Caixinha","Total"]:
                tbl_r[col] = tbl_r[col].map(fmt_brl)
            st.dataframe(tbl_r.sort_values("Data", ascending=False).reset_index(drop=True),
                         width='stretch', height=280)

    with nw_tab3:
        rend = saldos_sorted[saldos_sorted["rendimento_conta"].notna()].copy()
        if rend.empty:
            st.info("Nenhum dado de rendimento ainda.")
        else:
            rend = rend.sort_values("data")
            if "rendimento_caixinha" not in rend.columns:
                rend["rendimento_caixinha"] = 0.0
            rend["rendimento_caixinha"] = rend["rendimento_caixinha"].fillna(0.0)
            rend["acum_conta"]    = rend["rendimento_conta"].cumsum()
            rend["acum_caixinha"] = rend["rendimento_caixinha"].cumsum()
            rend["acum_total"]    = rend["acum_conta"] + rend["acum_caixinha"]

            fig_acum = go.Figure()
            fig_acum.add_scatter(
                x=rend["data"], y=rend["acum_total"],
                name="Total", mode="lines+markers",
                line=dict(color=colors[0], width=2), marker=dict(size=6),
                fill="tozeroy", fillcolor="rgba(200,240,96,0.12)",
                hovertemplate="<b>%{x|%Y-%m-%d}</b><br>Total: R$ %{y:,.2f}<extra></extra>",
            )
            fig_acum.add_scatter(
                x=rend["data"], y=rend["acum_conta"],
                name="Conta", mode="lines+markers",
                line=dict(color=colors[1], width=2, dash="dot"), marker=dict(size=5),
                hovertemplate="<b>%{x|%Y-%m-%d}</b><br>Conta: R$ %{y:,.2f}<extra></extra>",
            )
            if rend["acum_caixinha"].sum() > 0:
                fig_acum.add_scatter(
                    x=rend["data"], y=rend["acum_caixinha"],
                    name="Caixinha", mode="lines+markers",
                    line=dict(color=colors[2], width=2, dash="dash"), marker=dict(size=5),
                    hovertemplate="<b>%{x|%Y-%m-%d}</b><br>Caixinha: R$ %{y:,.2f}<extra></extra>",
                )
            fig_acum.update_layout(
                **build_plotly_theme(), height=380,
                xaxis_title=None, yaxis_title="R$",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, font=dict(size=11)),
            )
            st.plotly_chart(fig_acum, width='stretch')

            a1, a2, a3 = st.columns(3)
            a1.metric("Acumulado conta",    fmt_brl(rend["acum_conta"].iloc[-1]))
            a2.metric("Acumulado caixinha", fmt_brl(rend["acum_caixinha"].iloc[-1]))
            a3.metric("Acumulado total",    fmt_brl(rend["acum_total"].iloc[-1]))

with tab4:
    # aplica filtro de tipo mas mantém reembolsados visíveis
    if tipo == "Gastos":
        show_raw = dff_tabela[dff_tabela["valor"] < 0].copy()
    elif tipo == "Receitas":
        show_raw = dff_tabela[dff_tabela["valor"] > 0].copy()
    else:
        show_raw = dff_tabela.copy()
    _cols_raw = ["data","descricao","categoria","valor","origem","reembolsado"]
    if "fonte" in show_raw.columns:
        _cols_raw = ["data","descricao","categoria","valor","origem","fonte","reembolsado"]
    show_raw = show_raw[_cols_raw].sort_values("data", ascending=False).reset_index(drop=True)
    show = show_raw.copy()
    show["valor_fmt"] = show["valor"].map(fmt_brl_signed)
    show_display = show.drop(columns=["valor"]).rename(columns={
        "data":"Data","descricao":"Descrição","categoria":"Categoria",
        "valor_fmt":"Valor","origem":"Origem"
    })

    def style_row(row):
        if row["reembolsado"]:
            return ["color: #555"] * len(row)
        styles = [""] * len(row)
        val_idx = list(row.index).index("Valor")
        if str(row["Valor"]).startswith("- "):
            styles[val_idx] = "color: #ff6b6b"
        else:
            styles[val_idx] = "color: #a8e063"
        return styles

    styled = show_display.style.apply(style_row, axis=1)
    styled = styled.hide(axis="columns", subset=["reembolsado"])

    st.dataframe(styled, width='stretch', height=400)
    n_reemb = show_raw["reembolsado"].sum()
    if n_reemb > 0:
        st.markdown(f"<p style='color:#555;font-size:0.75rem;font-family:DM Mono,monospace;'>{n_reemb} transação(ões) em cinza = reembolso casado, neutralizado dos cálculos</p>", unsafe_allow_html=True)
    st.download_button("⬇ baixar transações (.xlsx)",
                       df_to_xlsx(show_raw.rename(columns={"data":"Data","descricao":"Descrição","categoria":"Categoria","valor":"Valor","origem":"Origem","fonte":"Fonte","reembolsado":"Reembolsado"})),
                       "transacoes.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)

    # ─────────────────────────────────────────────────────────────────────────────
# PATCH — cole no app.py em dois lugares:
#
# 1) Troque a linha dos tabs:
#    DE:  tab1, tab2, tab3, tab4 = st.tabs(["Por mês", "Por categoria", "Evolução", "Transações"])
#    PRA: tab1, tab2, tab3, tab4, tab5 = st.tabs(["Por mês", "Por categoria", "Evolução", "Transações", "Saldo & Projeção"])
#
# 2) Cole o bloco abaixo DEPOIS do `with tab4:` completo (antes do comentário
#    "── Barra deslizante de período" ou no final das tabs).
# ─────────────────────────────────────────────────────────────────────────────

with tab5:
    import datetime as _dt5
    import math

    st.markdown(
        "<p style='color:#555;font-size:0.75rem;font-family:DM Mono,monospace;"
        "text-transform:uppercase;letter-spacing:0.08em;margin-bottom:0.8rem'>"
        "saldo líquido mensal (receitas − gastos) e projeção linear</p>",
        unsafe_allow_html=True,
    )

    # ── Dataset base: todas as categorias selecionadas, sem reembolsados, sem filtro de tipo
    df_proj_base = df[df["categoria"].isin(cats_sel) & ~df["reembolsado"]].copy()
    meses_todos_proj = sorted(df_proj_base["mes"].unique())

    if not meses_todos_proj:
        st.info("Nenhum dado disponível.")
    else:
        # ── Controles ─────────────────────────────────────────────────────────
        col_ctrl1, col_ctrl2 = st.columns([3, 1])

        with col_ctrl1:
            st.markdown(
                "<p style='color:#666;font-size:0.72rem;font-family:DM Mono,monospace;"
                "text-transform:uppercase;letter-spacing:0.08em;margin-bottom:0.3rem'>"
                "período base para cálculo da média</p>",
                unsafe_allow_html=True,
            )
            if len(meses_todos_proj) >= 2:
                base_range = st.select_slider(
                    "base",
                    options=meses_todos_proj,
                    value=(meses_todos_proj[0], meses_todos_proj[-1]),
                    key="proj_base_range",
                    label_visibility="collapsed",
                )
            else:
                base_range = (meses_todos_proj[0], meses_todos_proj[0])

        with col_ctrl2:
            st.markdown(
                "<p style='color:#666;font-size:0.72rem;font-family:DM Mono,monospace;"
                "text-transform:uppercase;letter-spacing:0.08em;margin-bottom:0.3rem'>"
                "projetar até</p>",
                unsafe_allow_html=True,
            )
            _proj_default_date = (_dt5.date.today().replace(year=_dt5.date.today().year + 1))
            proj_ate = st.date_input(
                "proj_ate",
                value=_proj_default_date,
                key="proj_ate_date",
                label_visibility="collapsed",
            )

        # ── Cálculo do saldo mensal histórico ─────────────────────────────────
        saldo_mensal = (
            df_proj_base.groupby("mes")["valor"]
            .sum()
            .reset_index()
            .rename(columns={"valor": "saldo"})
            .sort_values("mes")
            .reset_index(drop=True)
        )

        # Detalhes: receita e gasto por mês (para hover)
        rec_por_mes = (
            df_proj_base[df_proj_base["valor"] > 0]
            .groupby("mes")["valor"].sum()
            .rename("receita")
        )
        gas_por_mes = (
            df_proj_base[df_proj_base["valor"] < 0]
            .groupby("mes")["valor"].sum().abs()
            .rename("gasto")
        )
        saldo_mensal = (
            saldo_mensal
            .join(rec_por_mes, on="mes")
            .join(gas_por_mes, on="mes")
        )
        saldo_mensal["receita"] = saldo_mensal["receita"].fillna(0)
        saldo_mensal["gasto"]   = saldo_mensal["gasto"].fillna(0)

        # ── Média do período base ──────────────────────────────────────────────
        mask_base = (
            (saldo_mensal["mes"] >= base_range[0]) &
            (saldo_mensal["mes"] <= base_range[1])
        )
        saldo_base = saldo_mensal[mask_base]
        media_mensal = saldo_base["saldo"].mean() if not saldo_base.empty else 0.0
        n_meses_base = len(saldo_base)

        # ── Meses de projeção ─────────────────────────────────────────────────
        ultimo_mes_str = saldo_mensal["mes"].max()
        p_atual = pd.Period(ultimo_mes_str, freq="M")
        p_fim   = pd.Period(proj_ate.strftime("%Y-%m"), freq="M")

        meses_proj = []
        p = p_atual + 1
        while p <= p_fim:
            meses_proj.append(str(p))
            p += 1

        colors = get_colors()
        _accent = get_accent()

        # ── Sub-tabs ──────────────────────────────────────────────────────────
        st5_a, st5_b = st.tabs(["Saldo mensal", "Acumulado projetado"])

        # ─── Sub-tab A: Saldo mensal + projeção ───────────────────────────────
        with st5_a:
            fig_s = go.Figure()

            # Barras históricas — verde se positivo, vermelho se negativo
            _bar_colors = [
                colors[0] if v >= 0 else "#ff5555"
                for v in saldo_mensal["saldo"]
            ]
            # Marca período base com opacidade cheia; fora do base, mais apagado
            _bar_opacity = [
                1.0 if (base_range[0] <= m <= base_range[1]) else 0.45
                for m in saldo_mensal["mes"]
            ]

            fig_s.add_bar(
                x=saldo_mensal["mes"],
                y=saldo_mensal["saldo"],
                name="Saldo histórico",
                marker=dict(
                    color=_bar_colors,
                    opacity=_bar_opacity,
                    line_width=0,
                ),
                customdata=list(zip(
                    saldo_mensal["receita"],
                    saldo_mensal["gasto"],
                    saldo_mensal["saldo"],
                )),
                hovertemplate=(
                    "<b>%{x}</b><br>"
                    "Receita: R$ %{customdata[0]:,.2f}<br>"
                    "Gasto:   R$ %{customdata[1]:,.2f}<br>"
                    "Saldo:   R$ %{customdata[2]:,.2f}"
                    "<extra></extra>"
                ),
            )

            # Barras de projeção (translúcidas)
            if meses_proj:
                fig_s.add_bar(
                    x=meses_proj,
                    y=[media_mensal] * len(meses_proj),
                    name="Projeção (média base)",
                    marker=dict(
                        color=colors[0] if media_mensal >= 0 else "#ff5555",
                        opacity=0.25,
                        line=dict(
                            color=colors[0] if media_mensal >= 0 else "#ff5555",
                            width=1,
                        ),
                    ),
                    hovertemplate=(
                        "<b>%{x}</b> (projeção)<br>"
                        "Estimativa: R$ %{y:,.2f}<extra></extra>"
                    ),
                )

            # Linha de média (atravessa histórico + projeção)
            _todos_x = list(saldo_mensal["mes"]) + meses_proj
            fig_s.add_scatter(
                x=_todos_x,
                y=[media_mensal] * len(_todos_x),
                name=f"Média base · {fmt_brl_signed(media_mensal)}/mês",
                mode="lines",
                line=dict(color=colors[1], width=2, dash="dot"),
                hovertemplate=f"Média: R$ {media_mensal:,.2f}/mês<extra></extra>",
            )

            fig_s.add_hline(y=0, line_color="#333", line_width=1)

            # Anotação separando histórico de projeção
            if meses_proj:
                fig_s.add_vline(
                    x=ultimo_mes_str,
                    line_color="#333",
                    line_width=1,
                    line_dash="dot",
                )
                fig_s.add_annotation(
                    x=meses_proj[0],
                    y=1,
                    yref="paper",
                    text="projeção →",
                    showarrow=False,
                    font=dict(color="#444", size=10, family="DM Mono"),
                    xanchor="left",
                )

            fig_s.update_layout(
                **build_plotly_theme(),
                height=440,
                bargap=0.25,
                xaxis_title=None,
                yaxis_title="R$",
                legend=dict(
                    orientation="h", yanchor="bottom", y=1.02, font=dict(size=11)
                ),
            )
            st.plotly_chart(fig_s, width='stretch')

            # ── KPIs ──────────────────────────────────────────────────────────
            _melhor  = saldo_mensal["saldo"].max()
            _pior    = saldo_mensal["saldo"].min()
            _proj_acum = media_mensal * len(meses_proj)
            _meses_pos = (saldo_mensal["saldo"] >= 0).sum()
            _meses_neg = (saldo_mensal["saldo"] < 0).sum()

            k1, k2, k3, k4 = st.columns(4)
            k1.metric(
                f"Média ({n_meses_base} meses base)",
                fmt_brl_signed(media_mensal),
            )
            k2.metric("Melhor mês", fmt_brl_signed(_melhor))
            k3.metric("Pior mês",   fmt_brl_signed(_pior))
            k4.metric(
                f"Projeção acumulada ({len(meses_proj)}m)",
                fmt_brl_signed(_proj_acum) if meses_proj else "—",
            )

            st.markdown(
                f"<p style='color:#555;font-size:0.75rem;font-family:DM Mono,monospace;"
                f"margin-top:0.3rem'>"
                f"meses no positivo: <span style='color:{colors[0]}'>{_meses_pos}</span> · "
                f"meses no negativo: <span style='color:#ff5555'>{_meses_neg}</span>"
                f"</p>",
                unsafe_allow_html=True,
            )

            # ── Tabela ────────────────────────────────────────────────────────
            with st.expander("tabela de saldos mensais", expanded=False):
                tbl_s = saldo_mensal[["mes","receita","gasto","saldo"]].copy()
                tbl_s["base"] = tbl_s["mes"].apply(
                    lambda m: "✓" if base_range[0] <= m <= base_range[1] else ""
                )
                tbl_s.columns = ["Mês", "Receita", "Gasto", "Saldo", "Base"]
                for col in ["Receita", "Gasto", "Saldo"]:
                    tbl_s[col] = tbl_s[col].map(fmt_brl_signed)
                if meses_proj:
                    proj_rows = pd.DataFrame({
                        "Mês": meses_proj,
                        "Receita": ["—"] * len(meses_proj),
                        "Gasto":   ["—"] * len(meses_proj),
                        "Saldo":   [fmt_brl_signed(media_mensal)] * len(meses_proj),
                        "Base":    ["(proj.)"] * len(meses_proj),
                    })
                    tbl_s = pd.concat([tbl_s, proj_rows], ignore_index=True)
                st.dataframe(
                    tbl_s.sort_values("Mês", ascending=False).reset_index(drop=True),
                    width='stretch', height=300,
                )

        # ─── Sub-tab B: Acumulado projetado ────────────────────────────────────
        with st5_b:
            st.markdown(
                "<p style='color:#555;font-size:0.75rem;font-family:DM Mono,monospace;"
                "margin-bottom:0.5rem'>"
                "patrimônio estimado partindo do networth atual e aplicando o saldo médio mensal</p>",
                unsafe_allow_html=True,
            )

            # Ponto de partida: networth atual (ou só conta se não tiver)
            if _pluggy_conta is not None:
                _nw_atual = _pluggy_conta + _pluggy_caixinha - (_pluggy_fatura or 0)
                _nw_label = "Networth atual (Pluggy)"
            elif balamt_recente is not None:
                _nw_atual = balamt_recente + saldo_caixinha
                _nw_label = "Networth atual (Supabase)"
            else:
                _nw_atual = None
                _nw_label = "—"

            col_nw, col_ajuste = st.columns([1, 2])
            with col_nw:
                st.markdown(
                    f"<p style='color:#666;font-size:0.72rem;font-family:DM Mono,monospace;"
                    f"text-transform:uppercase;letter-spacing:0.08em;margin-bottom:0.2rem'>"
                    f"{_nw_label}</p>",
                    unsafe_allow_html=True,
                )
                nw_input = st.number_input(
                    "nw",
                    value=float(_nw_atual) if _nw_atual is not None else 0.0,
                    step=500.0,
                    format="%.2f",
                    key="proj_nw_input",
                    label_visibility="collapsed",
                    help="Patrimônio inicial para a projeção acumulada",
                )
            with col_ajuste:
                st.markdown(
                    "<p style='color:#666;font-size:0.72rem;font-family:DM Mono,monospace;"
                    "text-transform:uppercase;letter-spacing:0.08em;margin-bottom:0.2rem'>"
                    "ajuste de saldo mensal projetado (R$/mês)</p>",
                    unsafe_allow_html=True,
                )
                saldo_ajuste = st.slider(
                    "ajuste",
                    min_value=-5000.0,
                    max_value=5000.0,
                    value=0.0,
                    step=100.0,
                    key="proj_saldo_ajuste",
                    label_visibility="collapsed",
                    help="Ajuste sobre a média calculada — útil para simular cenários",
                )

            _saldo_proj = media_mensal + saldo_ajuste
            st.markdown(
                f"<p style='color:#555;font-size:0.75rem;font-family:DM Mono,monospace;'>"
                f"saldo usado na projeção: "
                f"<span style='color:{_accent}'>{fmt_brl_signed(_saldo_proj)}/mês</span>"
                f"</p>",
                unsafe_allow_html=True,
            )

            if not meses_proj and not saldo_mensal.empty:
                st.info("Defina uma data de projeção futura para ver o acumulado.")
            else:
                # Série histórica acumulada (saldo_mensal cumsum desde o início)
                saldo_hist_acum = saldo_mensal.copy()
                saldo_hist_acum["saldo_acum"] = saldo_hist_acum["saldo"].cumsum()

                # Série projetada: parte do nw_input, cresce com _saldo_proj
                _pts_proj_x = [ultimo_mes_str] + meses_proj
                _pts_proj_y = [nw_input]
                for _ in meses_proj:
                    _pts_proj_y.append(_pts_proj_y[-1] + _saldo_proj)

                # Série histórica de networth (da tabela de saldos, se disponível)
                _tem_nw_hist = (
                    not df_saldos.empty
                    and "balamt" in df_saldos.columns
                )

                fig_acum = go.Figure()

                if _tem_nw_hist:
                    nw_hist_plot = saldos_sorted[["data", "networth"]].dropna(subset=["networth"])
                    fig_acum.add_scatter(
                        x=nw_hist_plot["data"],
                        y=nw_hist_plot["networth"],
                        name="Networth real",
                        mode="lines+markers",
                        line=dict(color=colors[0], width=2),
                        marker=dict(size=5),
                        hovertemplate="<b>%{x|%Y-%m}</b><br>Networth: R$ %{y:,.2f}<extra></extra>",
                        fill="tozeroy",
                        fillcolor="rgba(200,240,96,0.08)",
                    )

                # Projeção como linha tracejada
                fig_acum.add_scatter(
                    x=_pts_proj_x,
                    y=_pts_proj_y,
                    name="Projeção",
                    mode="lines+markers",
                    line=dict(color=colors[1], width=2, dash="dash"),
                    marker=dict(size=6, symbol="circle-open"),
                    hovertemplate="<b>%{x}</b> (proj.)<br>Estimativa: R$ %{y:,.2f}<extra></extra>",
                )

                # Meta opcional — linha horizontal
                _meta = st.session_state.get("proj_meta", None)

                fig_acum.update_layout(
                    **build_plotly_theme(),
                    height=420,
                    xaxis_title=None,
                    yaxis_title="R$",
                    legend=dict(
                        orientation="h", yanchor="bottom", y=1.02, font=dict(size=11)
                    ),
                )
                st.plotly_chart(fig_acum, width='stretch')

                # KPIs da projeção acumulada
                _nw_fim = _pts_proj_y[-1] if _pts_proj_y else nw_input
                _variacao = _nw_fim - nw_input
                _pct = (_variacao / nw_input * 100) if nw_input != 0 else 0

                b1, b2, b3 = st.columns(3)
                b1.metric("Patrimônio inicial", fmt_brl(nw_input))
                b2.metric(
                    f"Patrimônio em {proj_ate.strftime('%m/%Y')}",
                    fmt_brl(_nw_fim),
                    delta=f"{'+' if _variacao >= 0 else ''}{fmt_brl_signed(_variacao)}",
                )
                b3.metric(
                    "Variação total",
                    f"{_pct:+.1f}%",
                )

    # ── Editar categoria ──────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### ✏️ editar categoria")

    todas_cats = sorted(CATEGORY_COLORS.keys())

    # Seleção da transação via índice
    if show_raw.empty:
        st.info("Nenhuma transação para exibir.")
    else:
        # Monta rótulo legível para o selectbox
        def _row_label(i, row):
            data_str = row["data"].strftime("%d/%m/%y") if hasattr(row["data"], "strftime") else str(row["data"])[:10]
            desc = str(row["descricao"])[:40]
            val  = fmt_brl_signed(row["valor"])
            cat  = row["categoria"]
            return f"{data_str} · {desc} · {val} · [{cat}]"

        opcoes_labels = [_row_label(i, r) for i, r in show_raw.iterrows()]
        opcoes_map    = {lbl: i for i, lbl in enumerate(opcoes_labels)}

        sel_label = st.selectbox(
            "selecione a transação",
            options=opcoes_labels,
            index=0,
            key="tab4_sel_txn",
            label_visibility="collapsed",
        )
        sel_idx = opcoes_map[sel_label]
        sel_row = show_raw.iloc[sel_idx]

        # Conta quantas transações têm a mesma descrição no df filtrado
        desc_sel   = sel_row["descricao"]
        data_sel   = sel_row["data"].strftime("%Y-%m-%d")
        cat_atual  = sel_row["categoria"]
        n_iguais   = (show_raw["descricao"] == desc_sel).sum()

        col_cat, col_b1, col_b2 = st.columns([3, 1, 1])
        with col_cat:
            nova_cat = st.selectbox(
                "nova categoria",
                options=todas_cats,
                index=todas_cats.index(cat_atual) if cat_atual in todas_cats else 0,
                key="tab4_nova_cat",
                label_visibility="collapsed",
            )
        with col_b1:
            btn_esta = st.button("✅ só esta", use_container_width=True, key="btn_esta_txn")
        with col_b2:
            lbl_todas = f"🔁 todas ({n_iguais})" if n_iguais > 1 else "🔁 todas"
            btn_todas = st.button(lbl_todas, use_container_width=True, key="btn_todas_txn",
                                  disabled=(nova_cat == cat_atual))

        if btn_esta:
            if nova_cat == cat_atual:
                st.info("Categoria já é essa.")
            else:
                try:
                    save_categoria_override(desc_sel, nova_cat, data_str=data_sel)
                    st.success(f"Categoria desta transação → **{nova_cat}**")
                    load_categoria_overrides.clear()
                    st.rerun()
                except Exception as _e:
                    st.error(f"Erro ao salvar: {_e}")

        if btn_todas:
            try:
                save_categoria_override(desc_sel, nova_cat, data_str=None)
                st.success(f"Todas as transações '{desc_sel[:40]}' → **{nova_cat}**")
                load_categoria_overrides.clear()
                st.rerun()
            except Exception as _e:
                st.error(f"Erro ao salvar: {_e}")

        # Info sobre overrides ativos
        if not df_cat_overrides.empty:
            ov_desc = df_cat_overrides[df_cat_overrides["descricao"] == desc_sel]
            if not ov_desc.empty:
                with st.expander(f"overrides ativos para '{desc_sel[:40]}'", expanded=False):
                    for _, ov in ov_desc.iterrows():
                        escopo = f"data {ov['data']}" if ov["data"] != _SENTINELA else "todas"
                        st.markdown(
                            f"<span style='color:#888;font-size:0.8rem;font-family:DM Mono,monospace'>"
                            f"{escopo} → <b style='color:#c8f060'>{ov['categoria']}</b></span>",
                            unsafe_allow_html=True
                        )

        with st.expander("🔍 debug overrides", expanded=False):
            st.write("**df_cat_overrides (todos):**")
            st.dataframe(df_cat_overrides)
            st.write(f"**descricao selecionada:** `{desc_sel}`")
            st.write(f"**_SENTINELA:** `{_SENTINELA}`")
            if not df_cat_overrides.empty:
                st.write("**data dtype:**", df_cat_overrides["data"].dtype)
                st.write("**match sentinela:**", (df_cat_overrides["data"] == _SENTINELA).tolist())
            # mostra todas as linhas do df global com essa descrição e sua categoria resolvida
            hits = df[df["descricao"] == desc_sel][["data","descricao","categoria"]].head(10)
            st.write(f"**ocorrências no df global ({len(hits)}):**")
            st.dataframe(hits)
