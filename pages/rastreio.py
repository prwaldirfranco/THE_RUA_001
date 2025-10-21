import streamlit as st
import json
import os

DATA_FILE = "pedidos.json"

def carregar_pedidos():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except:
            return []

st.set_page_config(page_title="Rastrear Pedido", layout="wide")
st.title("📍 Rastrear Pedido")

codigo = st.text_input("Digite o código de rastreio do seu pedido")

if st.button("Buscar Pedido"):
    pedidos = carregar_pedidos()
    pedido = next((p for p in pedidos if str(p.get("codigo_rastreio")) == str(codigo)), None)

    if not pedido:
        st.error("Pedido não encontrado. Verifique o código e tente novamente.")
    else:
        st.success(f"Pedido encontrado para **{pedido['nome']}**")
        st.write(f"📞 Telefone: {pedido['telefone']}")
        st.write(f"🕒 Data: {pedido['data']}")
        st.write(f"💵 Total: R$ {pedido['total']:.2f}")
        st.write(f"📦 Tipo de pedido: {pedido['tipo_pedido']}")
        if pedido['tipo_pedido'] == "Entrega":
            st.write(f"📍 Endereço: {pedido['endereco']}")

        # Barra de status do pedido
        status = pedido.get("status", "Aguardando aceite")
        status_etapas = ["Aguardando aceite", "Em preparo", "Pronto", "Em rota de entrega", "Entregue"]

        st.progress(status_etapas.index(status) / (len(status_etapas) - 1))
        st.markdown(f"### 🚚 Status atual: **{status}**")

        # Histórico
        st.markdown("#### Itens do pedido:")
        for item in pedido["produtos"]:
            st.markdown(f"- {item['quantidade']}x {item['nome']} — R$ {item['preco'] * item['quantidade']:.2f}")

        st.info("Acompanhe aqui o andamento do seu pedido em tempo real.")
