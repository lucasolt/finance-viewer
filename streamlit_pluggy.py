"""
streamlit_pluggy.py — página Streamlit que lê dados via Pluggy Data API.

Setup:
1. pip install streamlit requests pandas
2. crie .streamlit/secrets.toml com:

   [pluggy]
   client_id = "seu-client-id"
   client_secret = "seu-client-secret"
   item_id = "seu-item-id"          # ou uma lista: item_ids = ["id1", "id2"]

3. streamlit run streamlit_pluggy.py
"""
import streamlit as st
import pandas as pd
from pluggy_client import PluggyClient, transactions_to_df

st.set_page_config(page_title="Pluggy", layout="wide")
st.title("Dados financeiros via Pluggy")

cfg = st.secrets["pluggy"]
item_ids = cfg.get("item_ids") or [cfg["item_id"]]


# API key vale 2h; cacheia o client autenticado por ~1h45 pra ser seguro.
@st.cache_resource
def get_client():
    c = PluggyClient(cfg["client_id"], cfg["client_secret"])
    c.authenticate()
    return c


@st.cache_data(ttl=60 * 60, show_spinner="Buscando dados na Pluggy...")
def load_data(item_ids: list[str]) -> pd.DataFrame:
    client = get_client()
    all_txns = []
    for iid in item_ids:
        all_txns.extend(client.all_transactions(iid))
    return transactions_to_df(all_txns)


with st.sidebar:
    st.caption("Conexões: " + ", ".join(item_ids))
    if st.button("Forçar refresh"):
        load_data.clear()
        get_client.clear()
        st.rerun()

df = load_data(item_ids)

if df.empty:
    st.warning("Nenhuma transação retornada. Confira o item_id e se a conexão "
               "no Meu Pluggy está ativa (status do item).")
    st.stop()

# filtro de período
if "date" in df.columns:
    dmin, dmax = df["date"].min().date(), df["date"].max().date()
    start, end = st.slider("Período", dmin, dmax, (dmin, dmax))
    mask = (df["date"].dt.date >= start) & (df["date"].dt.date <= end)
    view = df[mask]
else:
    view = df

c1, c2, c3 = st.columns(3)
c1.metric("Transações", len(view))
if "amount" in view.columns:
    c2.metric("Entradas", f"R$ {view[view.amount > 0].amount.sum():,.2f}")
    c3.metric("Saídas", f"R$ {view[view.amount < 0].amount.sum():,.2f}")

st.dataframe(view, use_container_width=True, hide_index=True)

# gasto por categoria
if {"category", "amount"}.issubset(view.columns):
    st.subheader("Saídas por categoria")
    cat = (view[view.amount < 0]
           .groupby("category")["amount"].sum().abs()
           .sort_values(ascending=False))
    st.bar_chart(cat)
