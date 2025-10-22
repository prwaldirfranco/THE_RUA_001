import streamlit as st
import json
import os
import pandas as pd
from datetime import datetime

# ---------------------------------------------------
# Segurança — exige login antes de acessar a página
# ---------------------------------------------------
if "logado" not in st.session_state or not st.session_state["logado"]:
    st.warning("⚠️ Acesso restrito. Faça login para continuar.")
    st.stop()

# ---------------------------------------------------
# Caminhos e arquivos
# ---------------------------------------------------
DATA_FILE = "pedidos.json"

# ---------------------------------------------------
# Funções auxiliares
# ---------------------------------------------------
def carregar_pedidos():
    """Carrega os pedidos do arquivo JSON"""
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except Exception:
            return []

def gerar_dataframe(pedidos):
    """Transforma pedidos em DataFrame pandas"""
    if not pedidos:
        return pd.DataFrame(columns=[
            "Data", "Código", "Cliente", "Total", "Pagamento",
            "Tipo Pedido", "Status"
        ])

    dados = []
    for p in pedidos:
        dados.append({
            "Data": p.get("data", ""),
            "Código": p.get("codigo_rastreio", ""),
            "Cliente": p.get("nome", ""),
            "Total": float(p.get("total", 0.0)),
            "Pagamento": p.get("pagamento", "—"),
            "Tipo Pedido": p.get("tipo_pedido", "—"),
            "Status": p.get("status", "—")
        })

    df = pd.DataFrame(dados)
    if not df.empty:
        df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
    return df

# ---------------------------------------------------
# Interface principal
# ---------------------------------------------------
st.set_page_config(page_title="📊 Relatórios - THE RUA", layout="wide")
st.title("📊 Relatórios de Vendas - THE RUA")
st.caption("Acompanhe o desempenho da sua hamburgueria em tempo real.")

pedidos = carregar_pedidos()
df = gerar_dataframe(pedidos)

if df.empty:
    st.info("Nenhum pedido registrado ainda.")
    st.stop()

# ---------------------------------------------------
# Filtros de período e status
# ---------------------------------------------------
col1, col2, col3 = st.columns(3)
with col1:
    data_inicio = st.date_input(
        "De:",
        value=df["Data"].min().date() if not df.empty else datetime.now().date()
    )
with col2:
    data_fim = st.date_input(
        "Até:",
        value=df["Data"].max().date() if not df.empty else datetime.now().date()
    )
with col3:
    status_filtro = st.selectbox(
        "Status do Pedido:",
        ["Todos"] + sorted(df["Status"].unique().tolist())
    )

# Aplicar filtros
df_filtrado = df[
    (df["Data"].dt.date >= data_inicio) &
    (df["Data"].dt.date <= data_fim)
]
if status_filtro != "Todos":
    df_filtrado = df_filtrado[df_filtrado["Status"] == status_filtro]

# ---------------------------------------------------
# Resumo do período
# ---------------------------------------------------
st.divider()
st.subheader("📅 Resumo do Período Selecionado")

col1, col2, col3, col4 = st.columns(4)
with col1:
    total_pedidos = len(df_filtrado)
    st.metric("Pedidos Realizados", total_pedidos)

with col2:
    total_vendas = df_filtrado["Total"].sum()
    st.metric("Total em Vendas (R$)", f"{total_vendas:,.2f}")

with col3:
    valor_medio = df_filtrado["Total"].mean() if total_pedidos > 0 else 0
    st.metric("Ticket Médio (R$)", f"{valor_medio:,.2f}")

with col4:
    status_mais_frequente = df_filtrado["Status"].mode()[0] if not df_filtrado.empty else "—"
    st.metric("Status mais comum", status_mais_frequente)

# ---------------------------------------------------
# Gráficos
# ---------------------------------------------------
st.divider()
st.subheader("📈 Análises Visuais")

col1, col2 = st.columns(2)

with col1:
    vendas_por_dia = df_filtrado.groupby(df_filtrado["Data"].dt.date)["Total"].sum()
    st.bar_chart(vendas_por_dia, height=300)
    st.caption("💰 Total de vendas por dia")

with col2:
    vendas_por_pagamento = df_filtrado.groupby("Pagamento")["Total"].sum().sort_values(ascending=False)
    st.bar_chart(vendas_por_pagamento, height=300)
    st.caption("💳 Total de vendas por forma de pagamento")

# ---------------------------------------------------
# Detalhamento completo
# ---------------------------------------------------
st.divider()
st.subheader("📋 Detalhamento dos Pedidos")

st.dataframe(
    df_filtrado.sort_values(by="Data", ascending=False),
    use_container_width=True,
    hide_index=True
)

# ---------------------------------------------------
# Exportação
# ---------------------------------------------------
st.divider()
st.subheader("📤 Exportar Relatório")

csv = df_filtrado.to_csv(index=False).encode("utf-8")
st.download_button(
    label="⬇️ Baixar Relatório (CSV)",
    data=csv,
    file_name=f"relatorio_{data_inicio}_{data_fim}.csv",
    mime="text/csv"
)

st.success("✅ Relatório pronto para análise!")
