import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from ofxparse import OfxParser
from supabase import create_client
import io

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

# ── Constants ─────────────────────────────────────────────────────────────────
PLOTLY_THEME = dict(
    paper_bgcolor="#0f0f0f", plot_bgcolor="#0f0f0f",
    font=dict(family="DM Sans", color="#e8e8e0", size=12),
    xaxis=dict(gridcolor="#1e1e1e", linecolor="#2a2a2a"),
    yaxis=dict(gridcolor="#1e1e1e", linecolor="#2a2a2a"),
    colorway=["#c8f060","#60c8f0","#f060c8","#f0c860","#60f0c8","#c860f0"],
)
COLORS = ["#c8f060","#60c8f0","#f060c8","#f0c860","#60f0c8","#c860f0","#f09060","#9060f0"]

CATEGORY_MAP = {
    "ifood": "Alimentação", "rappi": "Alimentação", "mcdonalds": "Alimentação",
    "burger": "Alimentação", "subway": "Alimentação", "padaria": "Alimentação",
    "mercado": "Alimentação", "supermercado": "Alimentação", "carrefour": "Alimentação",
    "restaurante": "Alimentação", "lanche": "Alimentação", "pizza": "Alimentação",
    "uber eats": "Alimentação", "pão de açúcar": "Alimentação",
    "uber": "Transporte", "99": "Transporte", "cabify": "Transporte",
    "shell": "Transporte", "ipiranga": "Transporte", "posto": "Transporte",
    "estacionamento": "Transporte", "onibus": "Transporte", "metro": "Transporte",
    "passagem": "Transporte",
    "netflix": "Streaming", "spotify": "Streaming", "amazon prime": "Streaming",
    "hbo": "Streaming", "disney": "Streaming", "globoplay": "Streaming",
    "farmacia": "Saúde", "drogaria": "Saúde", "drogasil": "Saúde",
    "ultrafarma": "Saúde", "consulta": "Saúde", "medico": "Saúde",
    "clinica": "Saúde", "academia": "Saúde",
    "pix": "Transferência", "ted": "Transferência", "doc": "Transferência",
    "transferencia": "Transferência",
    "aluguel": "Moradia", "condominio": "Moradia", "luz": "Moradia",
    "agua": "Moradia", "internet": "Moradia",
    "claro": "Telecom", "vivo": "Telecom", "tim": "Telecom", "oi": "Telecom",
    "amazon": "Compras", "americanas": "Compras", "magazine": "Compras",
    "shopee": "Compras", "aliexpress": "Compras",
    "steam": "Lazer", "cinema": "Lazer", "bar": "Lazer", "cerveja": "Lazer",
}

# ── Helpers ───────────────────────────────────────────────────────────────────
def fmt_brl(val: float) -> str:
    return f"R$ {abs(val):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def guess_category(desc: str) -> str:
    d = desc.lower()
    for kw, cat in CATEGORY_MAP.items():
        if kw in d:
            return cat
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
    res = sb.table("transacoes").select("*").execute()
    if not res.data:
        return pd.DataFrame()
    df = pd.DataFrame(res.data)
    df["data"] = pd.to_datetime(df["data"])
    df["mes"] = df["data"].dt.to_period("M").astype(str)
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
        })
    # upsert ignores duplicates via UNIQUE constraint
    sb.table("transacoes").upsert(rows, on_conflict="data,descricao,valor").execute()
    load_from_supabase.clear()

# ── Login ─────────────────────────────────────────────────────────────────────
if "authed" not in st.session_state:
    st.session_state.authed = False

if not st.session_state.authed:
    st.markdown("<div class='login-wrap'>", unsafe_allow_html=True)
    st.title("💸 gastos")
    pwd = st.text_input("senha", type="password", label_visibility="collapsed",
                        placeholder="senha")
    if st.button("entrar", use_container_width=True):
        if pwd == st.secrets["APP_PASSWORD"]:
            st.session_state.authed = True
            st.rerun()
        else:
            st.error("senha incorreta")
    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# ── Load data ─────────────────────────────────────────────────────────────────
df = load_from_supabase()

# ── Header ────────────────────────────────────────────────────────────────────
st.title("💸 controle de gastos")
st.markdown("<p class='upload-hint'>upload de extratos OFX — pode enviar vários de uma vez</p>",
            unsafe_allow_html=True)
st.divider()

# ── Upload ────────────────────────────────────────────────────────────────────
uploaded = st.file_uploader(
    "OFX", type=["ofx"], accept_multiple_files=True, label_visibility="collapsed"
)

if uploaded:
    frames = []
    errors = []
    for f in uploaded:
        try:
            parsed = parse_ofx(f.read())
            if not parsed.empty:
                frames.append(parsed)
        except Exception as e:
            errors.append(f"{f.name}: {e}")

    if frames:
        new_df = pd.concat(frames, ignore_index=True).drop_duplicates(
            subset=["data", "descricao", "valor"]
        )
        with st.spinner("salvando no banco..."):
            save_to_supabase(new_df)
        df = load_from_supabase()
        st.success(f"{len(new_df)} transações processadas.")

    for e in errors:
        st.error(e)

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
    st.markdown("### Filtros")
    meses = sorted(df["mes"].unique())
    meses_sel = st.multiselect("Meses", meses, default=meses)
    cats = sorted(df["categoria"].unique())
    cats_sel = st.multiselect("Categorias", cats, default=cats)
    tipo = st.radio("Tipo", ["Gastos", "Receitas", "Tudo"], index=0)
    st.divider()
    if st.button("🗑 Apagar todos os dados"):
        get_supabase().table("transacoes").delete().neq("id", 0).execute()
        load_from_supabase.clear()
        st.rerun()
    if st.button("🚪 Sair"):
        st.session_state.authed = False
        st.rerun()

# ── Filter ────────────────────────────────────────────────────────────────────
dff = df[df["mes"].isin(meses_sel) & df["categoria"].isin(cats_sel)].copy()
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
    por_mes = (dff[dff["valor"] < 0].groupby("mes")["valor_abs"]
               .sum().reset_index().sort_values("mes"))
    if por_mes.empty:
        st.info("Nenhum gasto no período.")
    else:
        fig = go.Figure()
        fig.add_bar(x=por_mes["mes"], y=por_mes["valor_abs"],
                    marker_color="#c8f060", marker_line_width=0,
                    hovertemplate="<b>%{x}</b><br>R$ %{y:,.2f}<extra></extra>")
        fig.update_layout(**PLOTLY_THEME, height=380, bargap=0.3,
                          xaxis_title=None, yaxis_title="R$", showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
        media = por_mes["valor_abs"].mean()
        st.markdown(f"<p style='color:#555;font-size:0.8rem;font-family:DM Mono,monospace;'>média mensal: <span style='color:#c8f060'>{fmt_brl(media)}</span></p>",
                    unsafe_allow_html=True)

with tab2:
    por_cat = (dff[dff["valor"] < 0].groupby("categoria")["valor_abs"]
               .sum().reset_index().sort_values("valor_abs", ascending=False))
    if por_cat.empty:
        st.info("Nenhum gasto no período.")
    else:
        col_a, col_b = st.columns(2)
        with col_a:
            fig_bar = go.Figure()
            fig_bar.add_bar(x=por_cat["valor_abs"], y=por_cat["categoria"],
                            orientation="h", marker_color="#c8f060", marker_line_width=0,
                            hovertemplate="<b>%{y}</b><br>R$ %{x:,.2f}<extra></extra>")
            fig_bar.update_layout(**PLOTLY_THEME, height=380,
                                  xaxis_title="R$", yaxis_title=None, showlegend=False)
            st.plotly_chart(fig_bar, use_container_width=True)
        with col_b:
            fig_pie = px.pie(por_cat, values="valor_abs", names="categoria",
                             hole=0.55, color_discrete_sequence=COLORS)
            fig_pie.update_traces(textfont_size=11,
                hovertemplate="<b>%{label}</b><br>R$ %{value:,.2f}<br>%{percent}<extra></extra>")
            fig_pie.update_layout(**PLOTLY_THEME, height=380,
                                  showlegend=True, legend=dict(font=dict(size=11)))
            st.plotly_chart(fig_pie, use_container_width=True)

with tab3:
    por_mes_cat = (dff[dff["valor"] < 0].groupby(["mes","categoria"])["valor_abs"]
                   .sum().reset_index().sort_values("mes"))
    if por_mes_cat.empty:
        st.info("Nenhum gasto no período.")
    else:
        fig_ev = px.bar(por_mes_cat, x="mes", y="valor_abs", color="categoria",
                        barmode="stack", color_discrete_sequence=COLORS,
                        labels={"valor_abs":"R$","mes":"","categoria":""})
        fig_ev.update_layout(**PLOTLY_THEME, height=420, bargap=0.25,
                             legend=dict(orientation="h", yanchor="bottom", y=1.02,
                                         font=dict(size=11)))
        fig_ev.update_traces(
            hovertemplate="<b>%{x}</b><br>%{data.name}<br>R$ %{y:,.2f}<extra></extra>")
        st.plotly_chart(fig_ev, use_container_width=True)

with tab4:
    show = dff[["data","descricao","categoria","valor"]].copy()
    show["valor"] = show["valor"].map(lambda v: f"{'+' if v > 0 else ''}{fmt_brl(v)}")
    show = show.sort_values("data", ascending=False).reset_index(drop=True)
    show.columns = ["Data","Descrição","Categoria","Valor"]
    st.dataframe(show, use_container_width=True, height=480)
    st.markdown("<p style='color:#333;font-size:0.75rem;font-family:DM Mono,monospace;'>edite o CATEGORY_MAP no código para ajustar categorias</p>",
                unsafe_allow_html=True)
