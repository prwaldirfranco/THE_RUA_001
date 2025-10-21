# pages/dashboard.py
import streamlit as st
import json
import os
from datetime import datetime
import time

PEDIDOS_FILE = "pedidos.json"

# ---------------------------
# Funções auxiliares
# ---------------------------
def carregar_pedidos():
    if not os.path.exists(PEDIDOS_FILE):
        with open(PEDIDOS_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)
        return []
    with open(PEDIDOS_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except:
            return []

# ---------------------------
# Interface principal
# ---------------------------
st.set_page_config(page_title="📊 Dashboard - POS-80", layout="wide")
st.title("📊 Dashboard - Acompanhamento de Pedidos")
st.caption("Visualize o status dos pedidos em tempo real.")

# Atualização automática simples
intervalo = st.sidebar.slider("🔄 Atualizar automaticamente (segundos)", 5, 60, 10)
st.sidebar.write("🕒 Última atualização:", datetime.now().strftime("%H:%M:%S"))
if st.sidebar.button("🔁 Atualizar agora"):
    st.rerun()

# ---------------------------
# Carregar e exibir pedidos
# ---------------------------
pedidos = carregar_pedidos()
if not pedidos:
    st.warning("Nenhum pedido registrado ainda.")
    st.stop()

# Estatísticas por status
status_counts = {}
for p in pedidos:
    s = p.get("status", "Desconhecido")
    status_counts[s] = status_counts.get(s, 0) + 1

# Indicadores principais
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("🕒 Aguardando aceite", status_counts.get("Aguardando aceite", 0))
col2.metric("👨‍🍳 Em preparo", status_counts.get("Em preparo", 0))
col3.metric("✅ Pronto", status_counts.get("Pronto", 0))
col4.metric("🚗 Em rota", status_counts.get("Em rota de entrega", 0))
col5.metric("📬 Entregue", status_counts.get("Entregue", 0))

st.divider()
st.subheader("📋 Detalhes dos pedidos")

# ---------------------------
# Lógica para abrir detalhes
# ---------------------------
if "pedido_detalhe" not in st.session_state:
    st.session_state["pedido_detalhe"] = None

# Listar pedidos recentes
for p in sorted(pedidos, key=lambda x: x.get("data", ""), reverse=True):
    col1, col2, col3 = st.columns([2, 3, 2])
    with col1:
        st.markdown(f"### 🧾 #{p.get('codigo_rastreio')}")
        st.caption(f"Cliente: {p.get('nome')}")
        st.caption(f"Data: {p.get('data')}")

    with col2:
        st.write(f"**Status:** {p.get('status')}")
        st.write(f"**Total:** R$ {p.get('total', 0):.2f}")
        st.caption(f"Tipo: {p.get('tipo_pedido')} — Pagamento: {p.get('pagamento')}")
        if p.get("tipo_pedido") == "Consumir no local" and p.get("status") == "Pronto":
            st.success("🍔 Pedido de BALCÃO pronto para retirada!")

    with col3:
        if st.button("📄 Ver Detalhes", key=f"det_{p['id']}"):
            st.session_state["pedido_detalhe"] = p

# ---------------------------
# Exibir detalhes do pedido selecionado
# ---------------------------
if st.session_state["pedido_detalhe"]:
    p = st.session_state["pedido_detalhe"]
    st.divider()
    st.subheader(f"📦 Detalhes do Pedido #{p['codigo_rastreio']}")
    st.write(f"👤 Cliente: {p['nome']} — {p['telefone']}")
    st.write(f"📦 Tipo: {p['tipo_pedido']} — 💰 Pagamento: {p['pagamento']}")
    if p["tipo_pedido"] == "Entrega":
        st.write(f"📍 Endereço: {p['endereco']}")
    st.write(f"🕒 Data: {p['data']}")
    st.write("### Itens do pedido:")
    for item in p["produtos"]:
        st.markdown(f"- {item['quantidade']}x {item['nome']} — R$ {item['preco']:.2f}")
    st.markdown(f"**Total:** R$ {p['total']:.2f}")

    # Se tiver comprovante PIX, mostrar
    if p.get("comprovante") and os.path.exists(p["comprovante"]):
        with open(p["comprovante"], "rb") as f:
            st.download_button("📎 Baixar comprovante PIX", data=f, file_name=os.path.basename(p["comprovante"]))

    if st.button("❌ Fechar Detalhes"):
        st.session_state["pedido_detalhe"] = None
        st.rerun()
