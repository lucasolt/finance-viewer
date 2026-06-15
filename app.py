import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import io
import datetime
import re

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="Gastos", page_icon="💸", layout="wide")

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@300;400;600&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
[data-baseweb="slider"] [role="slider"] {
    background-color: #555 !important; border-color: #555 !important; box-shadow: none !important;
}
[data-baseweb="slider"] div[class*="Track"] > div:nth-child(2) { background-color: #444 !important; }
[data-baseweb="slider"] div[class*="InnerTrack"] { background-color: #444 !important; }
div[data-testid="stSlider"] div[class*="track"] { background: #444 !important; }
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
    "Ardósia 🪶":   ["#94a3b8","#7c8fa3","#64748b","#a8b8c8","#b0bec5","#78909c","#90a4ae","#607d8b",
                     "#b4c4d8","#8ca0b8","#748498","#c0d0e0","#c8d4da","#90a8b0","#a8bcc4","#708898"],
    "Terra 🤎":     ["#a87c5a","#c4a882","#8b6347","#d4b896","#7a5c3e","#b89068","#967055","#c8a87a",
                     "#c89060","#dfc09a","#a07040","#e8caa8","#906840","#caa878","#b08060","#dab888"],
    "Sage 🌿":      ["#7a9e7e","#9ab89e","#5a8060","#b4c8b4","#6b8f6e","#88a88a","#4e7252","#a0b8a0",
                     "#8ab88e","#aacaae","#6a9070","#c4d8c4","#7ba07e","#98b89a","#5e8262","#b0c8b0"],
    "Chumbo 🌑":    ["#8892a0","#6e7a88","#a4aeb8","#545e6a","#b8c0c8","#404850","#7a8490","#c0c8d0",
                     "#98a2b0","#7e8e98","#b4bec8","#646e7a","#c8d0d8","#505860","#8a949e","#d0d8e0"],
}

# ── Helpers ───────────────────────────────────────────────────────────────────
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

# ── Category mapping ──────────────────────────────────────────────────────────
CATEGORY_MAP = {
    # Vícios & Conveniência
    "tabarcaria": "Vícios & Conveniência",
    "trinca tabarcaria": "Vícios & Conveniência",
    "tabacariacapri": "Vícios & Conveniência",
    "tabacaria": "Vícios & Conveniência",
    "havana revistaria e ta": "Vícios & Conveniência",
    "cameron": "Vícios & Conveniência",
    "banca cafe": "Vícios & Conveniência",
    "posto": "Vícios & Conveniência",
    "combust": "Vícios & Conveniência",
    # Alimentação & Mercado
    "alimentos": "Alimentação & Mercado",
    "super apolo": "Alimentação & Mercado",
    "zaffari": "Alimentação & Mercado",
    "mini mercado": "Alimentação & Mercado",
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
    "mercado": "Alimentação & Mercado",
    "restaurante": "Alimentação & Mercado",
    "lancheria": "Alimentação & Mercado",
    "cafe": "Alimentação & Mercado",
    # Saúde
    "farmacia": "Saúde",
    "farmacias": "Saúde",
    "drogaria": "Saúde",
    "sao joao": "Saúde",
    "panvel": "Saúde",
    "hospital": "Saúde",
    "clinica": "Saúde",
    "laboratorio": "Saúde",
    "medico": "Saúde",
    # Transporte
    "uber": "Transporte",
    "99": "Transporte",
    "gasolina": "Transporte",
    "estacionamento": "Transporte",
    # Assinaturas
    "spotify": "Assinaturas",
    "netflix": "Assinaturas",
    "amazon prime": "Assinaturas",
    "chatgpt": "Assinaturas",
    "openai": "Assinaturas",
    "claude": "Assinaturas",
    "anthropic": "Assinaturas",
    "apple": "Assinaturas",
    "google one": "Assinaturas",
    "icloud": "Assinaturas",
    "youtube": "Assinaturas",
    # Lazer
    "pub": "Lazer",
    "bar": "Lazer",
    "cinema": "Lazer",
    "teatro": "Lazer",
    "show": "Lazer",
    "ingresso": "Lazer",
    # Compras
    "amazon": "Compras",
    "mercado livre": "Compras",
    "magalu": "Compras",
    "shopee": "Compras",
    "aliexpress": "Compras",
    "shein": "Compras",
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
}

# ── guess_category ────────────────────────────────────────────────────────────
def guess_category(desc: str, valor: float = 0.0) -> str:
    d = desc.lower()

    if "pagamento de fatura" in d:
        return "Pagamento de Fatura"

    # Bolsa residência
    if ("transferência recebida" in d or "transferencia recebida" in d) and \
       "lucas oltramari" in d and 4500 <= abs(valor) <= 5000:
        return "Bolsa Residência"

    REGEX_MAP = [
        (r"^ifd\*",           "iFood"),
        (r"ifood",            "iFood"),
        (r"\buber\b",         "Transporte"),
        (r"uberride",         "Transporte"),
        (r"^dm \*",           "Assinaturas"),
        (r"\*spotify",        "Assinaturas"),
        (r"\bpub\b",          "Lazer"),
        (r"^pagamento recebido$", "Crédito de Fatura"),
    ]
    for pattern, cat in REGEX_MAP:
        if re.search(pattern, d):
            return cat

    for kw, cat in sorted(CATEGORY_MAP.items(), key=lambda x: -len(x[0])):
        if kw in d:
            return cat

    if re.search(r"•{3}\.\\d{3}\.\\d{3}-•{2}", desc):
        return "Transferência Pessoal"

    return "Outros"

# ── detectar_reembolsos ──────────────────────────────────────────────────────
def detectar_reembolsos(df: pd.DataFrame, janela_dias: int = 90) -> pd.DataFrame:
    df = df.copy()
    df["reembolsado"] = False
    if df.empty:
        return df

    def extrai_doc(desc):
        m = re.search(r"\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}", str(desc))
        if m:
            return m.group(0)
        m = re.search(r"•{3}\.\d{3}\.\d{3}-•{2}", str(desc))
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

# ── Load Pluggy CSV ──────────────────────────────────────────────────────────
@st.cache_data
def load_pluggy_csv(file) -> pd.DataFrame:
    df = pd.read_csv(file)
    if "Unnamed: 0" in df.columns:
        df = df.drop(columns=["Unnamed: 0"])

    # Rename to match legacy column names
    df = df.rename(columns={
        "date": "data",
        "description": "descricao",
        "amount": "valor",
        "category": "categoria_pluggy",
    })

    df["data"] = pd.to_datetime(df["data"], utc=True)
    df["data"] = df["data"].dt.tz_localize(None)

    # ── Normalizar sinais ─────────────────────────────────────
    # platinum (cartão de crédito): Pluggy retorna DEBIT positivo e CREDIT negativo → inverter tudo
    mask_plat = df["accountName"] == "platinum"
    df.loc[mask_plat, "valor"] = df.loc[mask_plat, "valor"] * -1
    # Nu Pagamentos (conta corrente): já vem com sinais corretos

    df["mes"] = df["data"].dt.to_period("M").astype(str)
    df["origem"] = df["accountName"].apply(lambda x: "fatura" if x == "platinum" else "extrato")
    df["categoria"] = df.apply(lambda r: guess_category(r["descricao"], r["valor"]), axis=1)

    df = detectar_reembolsos(df)
    return df

# ══════════════════════════════════════════════════════════════════════════════
# MAIN APP
# ══════════════════════════════════════════════════════════════════════════════
st.title("💸 gastos")

uploaded = st.file_uploader(
    "CSV do Pluggy", type=["csv"],
    label_visibility="collapsed",
    help="Exporte do Pluggy e arraste aqui",
)

if uploaded:
    df = load_pluggy_csv(uploaded)
    st.session_state["df_cache"] = df
elif "df_cache" in st.session_state:
    df = st.session_state["df_cache"]
else:
    st.markdown("""
    <div style='text-align:center; padding: 4rem 0; color: #333;'>
        <div style='font-size: 3rem;'>📂</div>
        <div style='font-family: DM Mono, monospace; font-size: 0.85rem; margin-top: 1rem;'>
            nenhum dado ainda — faça upload de um CSV do Pluggy
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Aparência")
    scheme = st.selectbox("Esquema de cores", list(COLOR_SCHEMES.keys()), key="color_scheme")
    st.divider()

    st.markdown("### Filtros")
    _min_date = df["data"].min().date()
    _max_date = df["data"].max().date()
    _meses_disp = sorted(df["mes"].unique())

    PRESET_OPTS = ["Tudo", "Últimos 12 meses", "Este ano (YTD)", "Este mês", "Personalizado", "Barra deslizante"]
    preset = st.selectbox("Período", PRESET_OPTS, index=5, key="date_preset")

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
        _sel = st.session_state.get("range_slider", (_meses_disp[0], _meses_disp[-1]))
        _m_ini, _m_fim = _sel[0], _sel[-1]
        d_start = pd.Period(_m_ini, freq="M").start_time.date()
        d_end = pd.Period(_m_fim, freq="M").end_time.date()
        d_start = max(d_start, _min_date)
        d_end = min(d_end, _max_date)
        st.caption("↓ use a barra abaixo do gráfico")
    else:  # Personalizado
        c_ini, c_fim = st.columns(2)
        d_start = c_ini.date_input("De", value=_min_date, min_value=_min_date, max_value=_max_date)
        d_end = c_fim.date_input("Até", value=_max_date, min_value=_min_date, max_value=_max_date)

    st.divider()

    tipo = st.radio("Tipo", ["Tudo", "Gastos", "Receitas"], horizontal=True)
    origem_opts = ["Tudo"] + sorted(df["origem"].unique())
    origem = st.radio("Origem", origem_opts, horizontal=True)

    st.divider()
    st.markdown("### Categorias")
    cats_all = sorted(df["categoria"].unique())

    col_a, col_b = st.columns(2)
    if col_a.button("✓ Todas", use_container_width=True):
        st.session_state["sel_cats"] = cats_all
    if col_b.button("✕ Nenhuma", use_container_width=True):
        st.session_state["sel_cats"] = []

    sel_cats = st.multiselect(
        "Categorias", cats_all,
        default=st.session_state.get("sel_cats", cats_all),
        key="sel_cats_widget",
        label_visibility="collapsed",
    )

# ── Apply filters ─────────────────────────────────────────────────────────────
mask = (
    (df["data"].dt.date >= d_start) &
    (df["data"].dt.date <= d_end) &
    (df["categoria"].isin(sel_cats))
)
if origem != "Tudo":
    mask &= df["origem"] == origem

dff_tabela = df[mask].copy()

if tipo == "Gastos":
    dff = dff_tabela[dff_tabela["valor"] < 0].copy()
elif tipo == "Receitas":
    dff = dff_tabela[dff_tabela["valor"] > 0].copy()
else:
    dff = dff_tabela.copy()

# KPI base: todos os filtros exceto tipo, excluindo reembolsados
dff_total = dff_tabela[~dff_tabela["reembolsado"]].copy()

# ── KPIs ──────────────────────────────────────────────────────────────────────
gastos   = dff_total[dff_total["valor"] < 0]["valor"].sum()
receitas = dff_total[dff_total["valor"] > 0]["valor"].sum()
saldo    = gastos + receitas

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total gasto",    fmt_brl(gastos))
c2.metric("Total recebido", fmt_brl(receitas))
c3.metric("Saldo período",  fmt_brl_signed(saldo),
          delta=f"{'+' if saldo >= 0 else ''}{saldo:.2f}", delta_color="normal")
c4.metric("Transações",     len(dff_total))

st.divider()

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Por mês", "Por categoria", "Evolução", "Transações", "Detalhes"])

# ── Tab 1: Por mês ───────────────────────────────────────────────────────────
with tab1:
    if dff.empty:
        st.info("Nenhum dado no período.")
    elif tipo == "Tudo":
        meses_u = sorted(dff["mes"].unique())
        rec_mes = dff[dff["valor"] > 0].groupby("mes")["valor"].sum().reindex(meses_u, fill_value=0)
        gas_mes = dff[dff["valor"] < 0].groupby("mes")["valor"].sum().reindex(meses_u, fill_value=0)
        sal_mes = rec_mes + gas_mes
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
        st.plotly_chart(fig, use_container_width=True)
        _tbl = pd.DataFrame({"Mês": meses_u, "Receitas": rec_mes.values,
                             "Gastos": gas_mes.abs().values, "Saldo": sal_mes.values})
        st.download_button("⬇ baixar tabela (.xlsx)", df_to_xlsx(_tbl), "por_mes.xlsx",
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    else:
        meses_u = sorted(dff["mes"].unique())
        val_mes = dff.groupby("mes")["valor"].sum().reindex(meses_u, fill_value=0)
        colors = get_colors()
        fig = go.Figure()
        fig.add_bar(x=meses_u, y=val_mes.abs().values, name=tipo,
                    marker_color=colors[0], marker_line_width=0,
                    hovertemplate="<b>%{x}</b><br>R$ %{y:,.2f}<extra></extra>")
        fig.update_layout(**build_plotly_theme(), height=420, bargap=0.25,
                          xaxis_title=None, yaxis_title="R$")
        st.plotly_chart(fig, use_container_width=True)

    # Barra deslizante
    if preset == "Barra deslizante" and len(_meses_disp) > 1:
        st.select_slider("Período", options=_meses_disp,
                         value=(st.session_state.get("range_slider", (_meses_disp[0], _meses_disp[-1]))),
                         key="range_slider")

# ── Tab 2: Por categoria ─────────────────────────────────────────────────────
with tab2:
    if dff.empty:
        st.info("Nenhum dado no período.")
    else:
        # Só gastos para o treemap/pie (faz mais sentido)
        dff_gastos = dff[dff["valor"] < 0].copy() if tipo == "Tudo" else dff.copy()
        if dff_gastos.empty:
            st.info("Nenhum gasto no período.")
        else:
            cat_sum = dff_gastos.groupby("categoria")["valor"].sum().abs().sort_values(ascending=False)
            cat_df = cat_sum.reset_index()
            cat_df.columns = ["Categoria", "Total"]
            cat_df["Pct"] = (cat_df["Total"] / cat_df["Total"].sum() * 100).round(1)

            col_pie, col_bar = st.columns([1, 1.5])
            with col_pie:
                fig_pie = px.pie(cat_df, values="Total", names="Categoria",
                                 color_discrete_sequence=get_colors(), hole=0.45)
                fig_pie.update_traces(textinfo="percent+label", textfont_size=11)
                fig_pie.update_layout(**build_plotly_theme(), height=420,
                                      showlegend=False, margin=dict(t=20, b=20))
                st.plotly_chart(fig_pie, use_container_width=True)

            with col_bar:
                fig_bar = px.bar(cat_df, x="Total", y="Categoria", orientation="h",
                                 color="Categoria", color_discrete_sequence=get_colors(),
                                 text=cat_df["Total"].apply(lambda v: fmt_brl(v)))
                fig_bar.update_traces(textposition="outside", textfont_size=11)
                fig_bar.update_layout(**build_plotly_theme(), height=420,
                                      showlegend=False, yaxis=dict(categoryorder="total ascending"),
                                      xaxis_title="R$", yaxis_title=None,
                                      margin=dict(l=10, r=80))
                st.plotly_chart(fig_bar, use_container_width=True)

            st.download_button("⬇ baixar tabela (.xlsx)", df_to_xlsx(cat_df),
                               "por_categoria.xlsx",
                               "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

            # Breakdown por mês × categoria (heatmap)
            st.markdown("### Categorias × Meses")
            pivot = dff_gastos.pivot_table(index="categoria", columns="mes",
                                            values="valor", aggfunc="sum").abs().fillna(0)
            pivot = pivot.reindex(columns=sorted(pivot.columns))
            fig_heat = px.imshow(pivot, color_continuous_scale=["#0f0f0f", get_accent()],
                                  aspect="auto", text_auto=".0f")
            fig_heat.update_layout(**build_plotly_theme(), height=max(300, len(pivot) * 28),
                                    margin=dict(l=10, t=30))
            st.plotly_chart(fig_heat, use_container_width=True)

# ── Tab 3: Evolução ──────────────────────────────────────────────────────────
with tab3:
    if dff.empty:
        st.info("Nenhum dado no período.")
    else:
        dff_sorted = dff.sort_values("data").copy()
        dff_sorted["acumulado"] = dff_sorted["valor"].cumsum()
        colors = get_colors()

        fig_evo = go.Figure()
        fig_evo.add_scatter(x=dff_sorted["data"], y=dff_sorted["acumulado"],
                            mode="lines", name="Saldo acumulado",
                            line=dict(color=colors[0], width=2),
                            fill="tozeroy",
                            fillcolor=colors[0].replace(")", ",0.08)").replace("rgb", "rgba")
                            if colors[0].startswith("rgb") else colors[0] + "14",
                            hovertemplate="<b>%{x|%d/%m/%Y}</b><br>Acumulado: R$ %{y:,.2f}<extra></extra>")
        fig_evo.add_hline(y=0, line_color="#333", line_width=1)
        fig_evo.update_layout(**build_plotly_theme(), height=420,
                              xaxis_title=None, yaxis_title="R$ acumulado")
        st.plotly_chart(fig_evo, use_container_width=True)

        # Evolução por categoria
        st.markdown("### Evolução mensal por categoria")
        top_cats = dff[dff["valor"] < 0].groupby("categoria")["valor"].sum().abs().nlargest(8).index.tolist()
        dff_top = dff[dff["categoria"].isin(top_cats)].copy()
        if not dff_top.empty:
            evo_cat = dff_top.groupby(["mes", "categoria"])["valor"].sum().abs().reset_index()
            fig_evo_cat = px.line(evo_cat, x="mes", y="valor", color="categoria",
                                  color_discrete_sequence=get_colors(), markers=True)
            fig_evo_cat.update_layout(**build_plotly_theme(), height=420,
                                      xaxis_title=None, yaxis_title="R$",
                                      legend=dict(orientation="h", yanchor="bottom", y=1.02,
                                                  font=dict(size=10)))
            st.plotly_chart(fig_evo_cat, use_container_width=True)

# ── Tab 4: Transações ────────────────────────────────────────────────────────
with tab4:
    if dff_tabela.empty:
        st.info("Nenhum dado no período.")
    else:
        busca = st.text_input("🔍 Buscar na descrição", "", key="busca_transacoes")
        df_show = dff_tabela.copy()
        if busca:
            df_show = df_show[df_show["descricao"].str.contains(busca, case=False, na=False)]

        df_display = df_show[["data", "descricao", "valor", "categoria", "origem"]].copy()
        df_display["data"] = df_display["data"].dt.strftime("%d/%m/%Y")
        df_display["valor_fmt"] = df_display["valor"].apply(fmt_brl_signed)
        df_display = df_display.sort_values("data", ascending=False)

        st.dataframe(
            df_display[["data", "descricao", "valor_fmt", "categoria", "origem"]].rename(columns={
                "data": "Data", "descricao": "Descrição", "valor_fmt": "Valor",
                "categoria": "Categoria", "origem": "Origem",
            }),
            use_container_width=True,
            height=600,
            hide_index=True,
        )
        st.caption(f"{len(df_display)} transações")
        st.download_button("⬇ baixar (.xlsx)", df_to_xlsx(df_show), "transacoes.xlsx",
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# ── Tab 5: Detalhes (dados brutos Pluggy) ────────────────────────────────────
with tab5:
    st.markdown("### Dados brutos do Pluggy")
    cols_raw = [c for c in df.columns if c not in ["_doc", "_eh_reembolso", "_eh_envio"]]
    st.dataframe(df[cols_raw].sort_values("data", ascending=False),
                 use_container_width=True, height=500, hide_index=True)
    st.caption(f"{len(df)} registros • {df['accountName'].nunique()} contas • "
               f"{df['data'].min().strftime('%d/%m/%Y')} a {df['data'].max().strftime('%d/%m/%Y')}")

    # Comparação: categoria Pluggy vs. guess_category
    st.markdown("### Pluggy vs. Guess Category")
    if "categoria_pluggy" in df.columns:
        comp = df[["descricao", "categoria_pluggy", "categoria"]].drop_duplicates()
        comp = comp[comp["categoria_pluggy"] != comp["categoria"]].sort_values("descricao")
        if comp.empty:
            st.success("Todas as categorias coincidem.")
        else:
            st.caption(f"{len(comp)} divergências")
            st.dataframe(comp.rename(columns={
                "descricao": "Descrição", "categoria_pluggy": "Pluggy", "categoria": "Guess"
            }), use_container_width=True, height=400, hide_index=True)
