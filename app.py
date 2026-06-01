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
    "Lima 🟢":      ["#c8f060","#60c8f0","#f060c8","#f0c860","#60f0c8","#c860f0","#f09060","#9060f0"],
    "Neon 🔵":      ["#00f5ff","#ff006e","#ffbe0b","#8338ec","#3a86ff","#fb5607","#06d6a0","#ef476f"],
    "Pastel 🌸":    ["#ffb3c6","#bde0fe","#caffbf","#ffd6a5","#fdffb6","#c8b6ff","#a8dadc","#f4a261"],
    "Mono ⬜":      ["#ffffff","#cccccc","#999999","#666666","#444444","#bbbbbb","#aaaaaa","#888888"],
    "Fogo 🔴":      ["#ff4d4d","#ff8c00","#ffd700","#ff6b6b","#ff9a3c","#ffcc02","#e63946","#f4a261"],
    "Oceano 🌊":    ["#0096c7","#00b4d8","#48cae4","#90e0ef","#ade8f4","#023e8a","#0077b6","#caf0f8"],
    "Ardósia 🩶":   ["#94a3b8","#7c8fa3","#64748b","#a8b8c8","#b0bec5","#78909c","#90a4ae","#607d8b"],
    "Terra 🤎":     ["#a87c5a","#c4a882","#8b6347","#d4b896","#7a5c3e","#b89068","#967055","#c8a87a"],
    "Sage 🌿":      ["#7a9e7e","#9ab89e","#5a8060","#b4c8b4","#6b8f6e","#88a88a","#4e7252","#a0b8a0"],
    "Chumbo 🌑":    ["#8892a0","#6e7a88","#a4aeb8","#545e6a","#b8c0c8","#404850","#7a8490","#c0c8d0"],
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
    # Alimentação — iFood
    "ifd*": "Alimentação",
    "ifood": "Alimentação",
    # Alimentação — estabelecimentos
    "zaffari": "Alimentação",
    "companhiazaffari": "Alimentação",
    "banca cafe acores": "Alimentação",
    "la brescia": "Alimentação",
    "armazem e fruteira": "Alimentação",
    "themis restaurante": "Alimentação",
    "rappi": "Alimentação",
    "mcdonalds": "Alimentação",
    "burger": "Alimentação",
    "subway": "Alimentação",
    "padaria": "Alimentação",
    "mercado": "Alimentação",
    "supermercado": "Alimentação",
    "carrefour": "Alimentação",
    "restaurante": "Alimentação",
    "lanche": "Alimentação",
    "pizza": "Alimentação",
    "pão de açúcar": "Alimentação",
    # Transporte
    "uber* trip": "Transporte",
    "uber uber *trip": "Transporte",
    "uber": "Transporte",
    "99": "Transporte",
    "cabify": "Transporte",
    "shell": "Transporte",
    "ipiranga": "Transporte",
    "posto": "Transporte",
    "estacionamento": "Transporte",
    "onibus": "Transporte",
    "metro": "Transporte",
    "passagem": "Transporte",
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
    # Streaming
    "dm *spotify": "Streaming",
    "spotify": "Streaming",
    "netflix": "Streaming",
    "amazon prime": "Streaming",
    "hbo": "Streaming",
    "disney": "Streaming",
    "globoplay": "Streaming",
    # Telecom
    "telefonica brasil": "Telecom",
    "conta vivo": "Telecom",
    "vivo": "Telecom",
    "claro": "Telecom",
    "tim": "Telecom",
    "oi": "Telecom",
    # Compras
    "amazon": "Compras",
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
    # Vestuário
    "h&m": "Vestuário",
    "lupo": "Vestuário",
    "hering": "Vestuário",
    "renner": "Vestuário",
    "riachuelo": "Vestuário",
    "zara": "Vestuário",
    # Lazer
    "tabarcaria": "Lazer",
    "trinca tabarcaria": "Lazer",
    "ingresso com": "Lazer",
    "steam": "Lazer",
    "cinema": "Lazer",
    "bar": "Lazer",
    "cerveja": "Lazer",
    # Casa
    "mp *appgas": "Casa",
    "appgas": "Casa",
    "aluguel": "Casa",
    "condominio": "Casa",
    "luz": "Casa",
    "agua": "Casa",
    "internet": "Casa",
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

def guess_category(desc: str) -> str:
    import re
    d = desc.lower()
    if "pagamento de fatura" in d:
        return "Pagamento de Fatura"
    for kw, cat in CATEGORY_MAP.items():
        if kw in d:
            return cat
    if re.search(r"•{3}\.\d{3}\.\d{3}-•{2}", desc):
        return "Transferência Pessoal"
    return "Outros"

def parse_ofx(file_bytes: bytes) -> pd.DataFrame:
    ofx = OfxParser.parse(io.BytesIO(file_bytes))
    rows = []
    for account in ofx.accounts:
        for txn in account.statement.transactions:
            rows.append({
                "data": txn.date.date() if hasattr(txn.date, "date") else txn.date,
                "descricao": txn.memo or txn.payee or "",
                "valor": float(txn.amount),
            })
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    df["data"] = pd.to_datetime(df["data"])
    df["mes"] = df["data"].dt.to_period("M").astype(str)
    df["categoria"] = df["descricao"].apply(guess_category)
    return df

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
    df["categoria"] = df["descricao"].apply(guess_category)
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
df = load_from_supabase()
prefs = load_prefs()

# Apply saved prefs to session state (only first run)
if "prefs_loaded" not in st.session_state:
    if "color_scheme" in prefs:
        st.session_state["color_scheme"] = prefs["color_scheme"]
    if "cat_state" in prefs:
        st.session_state["cat_state"] = json.loads(prefs["cat_state"])
    if "tipo" in prefs:
        st.session_state["tipo_radio"] = prefs["tipo"]
    if "ano_sel" in prefs:
        st.session_state["ano_sel"] = prefs["ano_sel"]
    if "m_range" in prefs:
        st.session_state["m_range"] = tuple(json.loads(prefs["m_range"]))
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
    for f in files:
        try:
            parsed = parse_ofx(f.read())
            if not parsed.empty:
                parsed["origem"] = origem
                frames.append(parsed)
        except Exception as e:
            errors.append(f"{f.name}: {e}")
    if frames:
        new_df = pd.concat(frames, ignore_index=True).drop_duplicates(
            subset=["data", "descricao", "valor", "origem"]
        )
        with st.spinner("salvando no banco..."):
            save_to_supabase(new_df)
        st.success(f"{len(new_df)} transações ({origem}) salvas.")
    for e in errors:
        st.error(e)

with col_up1:
    st.markdown("<p style='color:#555;font-size:0.75rem;font-family:DM Mono,monospace;text-transform:uppercase;letter-spacing:0.08em;'>Extrato da conta</p>", unsafe_allow_html=True)
    up_extrato = st.file_uploader("extrato", type=["ofx"], accept_multiple_files=True,
                                   label_visibility="collapsed", key="up_extrato")
    if up_extrato:
        process_upload(up_extrato, "extrato")
        df = load_from_supabase()

with col_up2:
    st.markdown("<p style='color:#555;font-size:0.75rem;font-family:DM Mono,monospace;text-transform:uppercase;letter-spacing:0.08em;'>Fatura do cartão</p>", unsafe_allow_html=True)
    up_fatura = st.file_uploader("fatura", type=["ofx"], accept_multiple_files=True,
                                  label_visibility="collapsed", key="up_fatura")
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
    # Ano
    anos = sorted(df["data"].dt.year.unique())
    _ano_default_idx = 0
    if "ano_sel" in st.session_state:
        _opts = ["Todos"] + [str(a) for a in anos]
        _ano_default_idx = _opts.index(st.session_state["ano_sel"]) if st.session_state["ano_sel"] in _opts else 0
    ano_sel = st.selectbox("Ano", ["Todos"] + [str(a) for a in anos], index=_ano_default_idx, key="ano_sel_w")
    save_pref("ano_sel", ano_sel)
    # Range de meses
    MONTH_NAMES = ["Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez"]
    _m_default = st.session_state.get("m_range", (1, 12))
    m_range = st.select_slider("Período", options=list(range(1, 13)),
                               format_func=lambda x: MONTH_NAMES[x-1],
                               value=_m_default, key="m_range")
    save_pref("m_range", str(list(m_range)))
    _tipo_opts = ["Gastos", "Receitas", "Tudo"]
    _tipo_idx = _tipo_opts.index(st.session_state.get("tipo_radio", "Gastos")) if st.session_state.get("tipo_radio") in _tipo_opts else 0
    tipo = st.radio("Tipo", _tipo_opts, index=_tipo_idx)
    save_pref("tipo", tipo)

    st.markdown("### Categorias")
    cats = sorted(df["categoria"].unique())
    EXCLUDED_BY_DEFAULT = {"Pagamento de Fatura", "Crédito de Fatura", "Transferência Pessoal", "Investimento"}

    # Inicializa estado das categorias na primeira vez ou para categorias novas
    if "cat_state" not in st.session_state:
        st.session_state.cat_state = {}
    for c in cats:
        if c not in st.session_state.cat_state:
            st.session_state.cat_state[c] = c not in EXCLUDED_BY_DEFAULT

    col_a, col_b = st.columns(2)
    if col_a.button("✓ Tudo", width='stretch'):
        for c in cats:
            st.session_state[f"cat_{c}"] = True
            st.session_state.cat_state[c] = True
        save_pref("cat_state", json.dumps(st.session_state.cat_state))
        st.rerun()
    if col_b.button("✗ Nada", width='stretch'):
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
            load_from_supabase.clear()
            st.session_state.confirm_delete = False
            st.rerun()
        if col_d.button("✗ Não", width='stretch'):
            st.session_state.confirm_delete = False
            st.rerun()
    if st.button("🚪 Sair"):
        st.session_state.authed = False
        st.rerun()

# ── Filter ────────────────────────────────────────────────────────────────────
# apply date filter
if ano_sel == "Todos":
    mask_data = (df["data"].dt.month >= m_range[0]) & (df["data"].dt.month <= m_range[1])
else:
    mask_data = (df["data"].dt.year == int(ano_sel)) &                 (df["data"].dt.month >= m_range[0]) & (df["data"].dt.month <= m_range[1])
dff = df[mask_data & df["categoria"].isin(cats_sel)].copy()
if tipo == "Gastos":
    dff = dff[dff["valor"] < 0]
elif tipo == "Receitas":
    dff = dff[dff["valor"] > 0]
dff["valor_abs"] = dff["valor"].abs()

# ── KPIs ──────────────────────────────────────────────────────────────────────
gastos  = dff[dff["valor"] < 0]["valor"].sum()
receitas = dff[dff["valor"] > 0]["valor"].sum()
saldo   = gastos + receitas
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total gasto",    fmt_brl(gastos))
c2.metric("Total recebido", fmt_brl(receitas))
c3.metric("Saldo",          fmt_brl(saldo))
c4.metric("Transações",     len(dff))
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
    else:
        por_mes = (dff.groupby("mes")["valor_abs"].sum().reset_index().sort_values("mes"))
        fig = go.Figure()
        fig.add_bar(x=por_mes["mes"], y=por_mes["valor_abs"],
                    marker_color=get_accent(), marker_line_width=0,
                    hovertemplate="<b>%{x}</b><br>R$ %{y:,.2f}<extra></extra>")
        fig.update_layout(**build_plotly_theme(), height=380, bargap=0.3,
                          xaxis_title=None, yaxis_title="R$", showlegend=False)
        st.plotly_chart(fig, width='stretch')
        media = por_mes["valor_abs"].mean()
        st.markdown(f"<p style='color:#555;font-size:0.8rem;font-family:DM Mono,monospace;'>média mensal: <span style='color:{get_accent()}'>{fmt_brl(media)}</span></p>",
                    unsafe_allow_html=True)

with tab2:
    if dff.empty:
        st.info("Nenhum dado no período.")
    elif tipo == "Tudo":
        # Side-by-side: receitas vs gastos por categoria
        rec_cat = dff[dff["valor"] > 0].groupby("categoria")["valor"].sum().rename("Receita")
        gas_cat = dff[dff["valor"] < 0].groupby("categoria")["valor"].abs().rename("Gasto")
        por_cat_tudo = pd.concat([rec_cat, gas_cat], axis=1).fillna(0)
        por_cat_tudo.index.name = "categoria"
        por_cat_tudo = por_cat_tudo.reset_index()
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
        colors = get_colors()
        fig_ev = go.Figure()
        # gastos (negative stack)
        for i, cat in enumerate(gas_cat["categoria"].unique()):
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
        fig_ev = px.bar(por_mes_cat, x="mes", y="valor_abs", color="categoria",
                        barmode="stack", color_discrete_sequence=get_colors(),
                        labels={"valor_abs":"R$","mes":"","categoria":""})
        fig_ev.update_layout(**build_plotly_theme(), height=420, bargap=0.25,
                             legend=dict(orientation="h", yanchor="bottom", y=1.02,
                                         font=dict(size=11)))
        fig_ev.update_traces(
            hovertemplate="<b>%{x}</b><br>%{data.name}<br>R$ %{y:,.2f}<extra></extra>")
        st.plotly_chart(fig_ev, width='stretch')

with tab4:
    show = dff[["data","descricao","categoria","valor"]].copy()
    show["valor"] = show["valor"].map(lambda v: f"{'+' if v > 0 else ''}{fmt_brl(v)}")
    show = show.sort_values("data", ascending=False).reset_index(drop=True)
    show.columns = ["Data","Descrição","Categoria","Valor"]
    st.dataframe(show, width='stretch', height=480)
    st.markdown("<p style='color:#333;font-size:0.75rem;font-family:DM Mono,monospace;'>edite o CATEGORY_MAP no código para ajustar categorias</p>",
                unsafe_allow_html=True)
