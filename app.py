import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from ofxparse import OfxParser
import io
from datetime import datetime

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Gastos",
    page_icon="💸",
    layout="wide",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@300;400;600&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

/* Background */
.stApp {
    background-color: #0f0f0f;
    color: #e8e8e0;
}

/* Hide default header */
header[data-testid="stHeader"] { background: transparent; }

/* Title */
h1 {
    font-family: 'DM Mono', monospace !important;
    font-size: 1.6rem !important;
    color: #c8f060 !important;
    letter-spacing: -0.03em;
    margin-bottom: 0 !important;
}

h2, h3 {
    font-family: 'DM Mono', monospace !important;
    color: #e8e8e0 !important;
    font-size: 0.95rem !important;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}

/* Metric cards */
[data-testid="metric-container"] {
    background: #1a1a1a;
    border: 1px solid #2a2a2a;
    border-radius: 8px;
    padding: 1rem 1.2rem;
}
[data-testid="metric-container"] label {
    color: #666 !important;
    font-size: 0.72rem !important;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    font-family: 'DM Mono', monospace !important;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    color: #c8f060 !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 1.5rem !important;
}

/* Upload area */
[data-testid="stFileUploadDropzone"] {
    background: #1a1a1a !important;
    border: 1px dashed #333 !important;
    border-radius: 8px !important;
}
[data-testid="stFileUploadDropzone"]:hover {
    border-color: #c8f060 !important;
}

/* Selectbox / multiselect */
[data-testid="stSelectbox"] > div > div,
[data-testid="stMultiSelect"] > div > div {
    background: #1a1a1a !important;
    border-color: #2a2a2a !important;
    color: #e8e8e0 !important;
}

/* Dataframe */
[data-testid="stDataFrame"] {
    border: 1px solid #2a2a2a;
    border-radius: 8px;
}

/* Divider */
hr { border-color: #222 !important; }

/* Tabs */
[data-testid="stTabs"] button {
    font-family: 'DM Mono', monospace !important;
    font-size: 0.75rem !important;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    color: #555 !important;
}
[data-testid="stTabs"] button[aria-selected="true"] {
    color: #c8f060 !important;
    border-bottom-color: #c8f060 !important;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: #111 !important;
    border-right: 1px solid #1e1e1e;
}

.upload-hint {
    color: #444;
    font-size: 0.8rem;
    font-family: 'DM Mono', monospace;
    margin-top: 0.5rem;
}
</style>
""", unsafe_allow_html=True)


# ── Helpers ───────────────────────────────────────────────────────────────────
PLOTLY_THEME = dict(
    paper_bgcolor="#0f0f0f",
    plot_bgcolor="#0f0f0f",
    font=dict(family="DM Sans", color="#e8e8e0", size=12),
    xaxis=dict(gridcolor="#1e1e1e", linecolor="#2a2a2a"),
    yaxis=dict(gridcolor="#1e1e1e", linecolor="#2a2a2a"),
    colorway=["#c8f060", "#60c8f0", "#f060c8", "#f0c860", "#60f0c8", "#c860f0"],
)

CATEGORY_MAP = {
    "ifood": "Alimentação",
    "rappi": "Alimentação",
    "mcdonalds": "Alimentação",
    "burger": "Alimentação",
    "subway": "Alimentação",
    "padaria": "Alimentação",
    "mercado": "Alimentação",
    "supermercado": "Alimentação",
    "carrefour": "Alimentação",
    "extra": "Alimentação",
    "pão de açúcar": "Alimentação",
    "restaurante": "Alimentação",
    "lanche": "Alimentação",
    "pizza": "Alimentação",
    "uber eats": "Alimentação",
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
    "netflix": "Streaming",
    "spotify": "Streaming",
    "amazon prime": "Streaming",
    "hbo": "Streaming",
    "disney": "Streaming",
    "globoplay": "Streaming",
    "farmacia": "Saúde",
    "drogaria": "Saúde",
    "drogasil": "Saúde",
    "ultrafarma": "Saúde",
    "consulta": "Saúde",
    "medico": "Saúde",
    "clinica": "Saúde",
    "academia": "Saúde",
    "pix": "Transferência",
    "ted": "Transferência",
    "doc": "Transferência",
    "transferencia": "Transferência",
    "aluguel": "Moradia",
    "condominio": "Moradia",
    "luz": "Moradia",
    "agua": "Moradia",
    "internet": "Moradia",
    "claro": "Telecom",
    "vivo": "Telecom",
    "tim": "Telecom",
    "oi": "Telecom",
    "amazon": "Compras",
    "americanas": "Compras",
    "magazine": "Compras",
    "shopee": "Compras",
    "aliexpress": "Compras",
    "steam": "Lazer",
    "cinema": "Lazer",
    "bar": "Lazer",
    "cerveja": "Lazer",
}

def guess_category(desc: str) -> str:
    desc_lower = desc.lower()
    for keyword, cat in CATEGORY_MAP.items():
        if keyword in desc_lower:
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

def fmt_brl(val: float) -> str:
    return f"R$ {abs(val):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


# ── State: accumulate uploads ─────────────────────────────────────────────────
if "df_all" not in st.session_state:
    st.session_state.df_all = pd.DataFrame()


# ── Header ────────────────────────────────────────────────────────────────────
st.title("💸 controle de gastos")
st.markdown("<p class='upload-hint'>upload de extratos OFX do Nubank — pode enviar vários de uma vez</p>", unsafe_allow_html=True)
st.divider()

# ── Upload ────────────────────────────────────────────────────────────────────
uploaded = st.file_uploader(
    "Selecione os arquivos OFX",
    type=["ofx"],
    accept_multiple_files=True,
    label_visibility="collapsed",
)

if uploaded:
    frames = []
    errors = []
    for f in uploaded:
        try:
            df = parse_ofx(f.read())
            if not df.empty:
                frames.append(df)
        except Exception as e:
            errors.append(f"{f.name}: {e}")

    if frames:
        new_df = pd.concat(frames, ignore_index=True).drop_duplicates(subset=["data", "descricao", "valor"])
        # merge with existing
        if not st.session_state.df_all.empty:
            combined = pd.concat([st.session_state.df_all, new_df], ignore_index=True)
            st.session_state.df_all = combined.drop_duplicates(subset=["data", "descricao", "valor"])
        else:
            st.session_state.df_all = new_df

    for e in errors:
        st.error(e)

df = st.session_state.df_all

if df.empty:
    st.markdown("""
    <div style='text-align:center; padding: 4rem 0; color: #333;'>
        <div style='font-size: 3rem;'>📂</div>
        <div style='font-family: DM Mono, monospace; font-size: 0.85rem; margin-top: 1rem;'>
            nenhum dado carregado ainda
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ── Sidebar filters ───────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Filtros")

    meses = sorted(df["mes"].unique())
    meses_sel = st.multiselect("Meses", meses, default=meses)

    cats = sorted(df["categoria"].unique())
    cats_sel = st.multiselect("Categorias", cats, default=cats)

    tipo = st.radio("Tipo", ["Gastos", "Receitas", "Tudo"], index=0)

    st.divider()
    if st.button("🗑 Limpar dados"):
        st.session_state.df_all = pd.DataFrame()
        st.rerun()

# ── Filter ────────────────────────────────────────────────────────────────────
dff = df[df["mes"].isin(meses_sel) & df["categoria"].isin(cats_sel)].copy()

if tipo == "Gastos":
    dff = dff[dff["valor"] < 0]
elif tipo == "Receitas":
    dff = dff[dff["valor"] > 0]

dff["valor_abs"] = dff["valor"].abs()

# ── KPIs ──────────────────────────────────────────────────────────────────────
gastos = dff[dff["valor"] < 0]["valor"].sum()
receitas = dff[dff["valor"] > 0]["valor"].sum()
saldo = gastos + receitas
n_txn = len(dff)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total gasto", fmt_brl(gastos))
c2.metric("Total recebido", fmt_brl(receitas))
c3.metric("Saldo", fmt_brl(saldo))
c4.metric("Transações", n_txn)

st.divider()

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(["Por mês", "Por categoria", "Evolução", "Transações"])

with tab1:
    por_mes = (
        dff[dff["valor"] < 0]
        .groupby("mes")["valor_abs"]
        .sum()
        .reset_index()
        .sort_values("mes")
    )
    if por_mes.empty:
        st.info("Nenhum gasto no período selecionado.")
    else:
        fig = go.Figure()
        fig.add_bar(
            x=por_mes["mes"],
            y=por_mes["valor_abs"],
            marker_color="#c8f060",
            marker_line_width=0,
            hovertemplate="<b>%{x}</b><br>R$ %{y:,.2f}<extra></extra>",
        )
        fig.update_layout(
            **PLOTLY_THEME,
            title=None,
            xaxis_title=None,
            yaxis_title="R$",
            showlegend=False,
            height=380,
            bargap=0.3,
        )
        st.plotly_chart(fig, use_container_width=True)

        # média
        media = por_mes["valor_abs"].mean()
        st.markdown(f"<p style='color:#555; font-size:0.8rem; font-family:DM Mono,monospace;'>média mensal: <span style='color:#c8f060'>{fmt_brl(media)}</span></p>", unsafe_allow_html=True)

with tab2:
    por_cat = (
        dff[dff["valor"] < 0]
        .groupby("categoria")["valor_abs"]
        .sum()
        .reset_index()
        .sort_values("valor_abs", ascending=False)
    )
    if por_cat.empty:
        st.info("Nenhum gasto no período selecionado.")
    else:
        col_a, col_b = st.columns([1, 1])
        with col_a:
            fig_bar = go.Figure()
            fig_bar.add_bar(
                x=por_cat["valor_abs"],
                y=por_cat["categoria"],
                orientation="h",
                marker_color="#c8f060",
                marker_line_width=0,
                hovertemplate="<b>%{y}</b><br>R$ %{x:,.2f}<extra></extra>",
            )
            fig_bar.update_layout(
                **PLOTLY_THEME,
                height=380,
                xaxis_title="R$",
                yaxis_title=None,
                showlegend=False,
            )
            st.plotly_chart(fig_bar, use_container_width=True)

        with col_b:
            fig_pie = px.pie(
                por_cat,
                values="valor_abs",
                names="categoria",
                hole=0.55,
                color_discrete_sequence=["#c8f060","#60c8f0","#f060c8","#f0c860","#60f0c8","#c860f0","#f09060","#9060f0"],
            )
            fig_pie.update_traces(
                textfont_size=11,
                hovertemplate="<b>%{label}</b><br>R$ %{value:,.2f}<br>%{percent}<extra></extra>",
            )
            fig_pie.update_layout(
                **PLOTLY_THEME,
                height=380,
                showlegend=True,
                legend=dict(font=dict(size=11)),
            )
            st.plotly_chart(fig_pie, use_container_width=True)

with tab3:
    por_mes_cat = (
        dff[dff["valor"] < 0]
        .groupby(["mes", "categoria"])["valor_abs"]
        .sum()
        .reset_index()
        .sort_values("mes")
    )
    if por_mes_cat.empty:
        st.info("Nenhum gasto no período selecionado.")
    else:
        fig_ev = px.bar(
            por_mes_cat,
            x="mes",
            y="valor_abs",
            color="categoria",
            barmode="stack",
            color_discrete_sequence=["#c8f060","#60c8f0","#f060c8","#f0c860","#60f0c8","#c860f0","#f09060","#9060f0"],
            labels={"valor_abs": "R$", "mes": "", "categoria": ""},
        )
        fig_ev.update_layout(
            **PLOTLY_THEME,
            height=420,
            bargap=0.25,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, font=dict(size=11)),
        )
        fig_ev.update_traces(
            hovertemplate="<b>%{x}</b><br>%{data.name}<br>R$ %{y:,.2f}<extra></extra>",
        )
        st.plotly_chart(fig_ev, use_container_width=True)

with tab4:
    show = dff[["data", "descricao", "categoria", "valor"]].copy()
    show["valor"] = show["valor"].map(lambda v: f"{'+' if v > 0 else ''}{fmt_brl(v)}")
    show = show.sort_values("data", ascending=False).reset_index(drop=True)
    show.columns = ["Data", "Descrição", "Categoria", "Valor"]
    st.dataframe(show, use_container_width=True, height=480)

    # edit categories inline hint
    st.markdown("<p style='color:#333; font-size:0.75rem; font-family:DM Mono,monospace;'>categorias são inferidas automaticamente — edite o CATEGORY_MAP no código para ajustar</p>", unsafe_allow_html=True)
