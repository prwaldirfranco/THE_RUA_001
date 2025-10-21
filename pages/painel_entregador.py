import streamlit as st
import json
import os
from datetime import datetime

if "logado" not in st.session_state or not st.session_state["logado"]:
    st.warning("⚠️ Acesso restrito. Faça login para continuar.")
    st.stop()

DATA_FILE = "pedidos.json"

# ============================
# Funções auxiliares
# ============================
def carregar_pedidos():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except:
            return []

def salvar_pedidos(pedidos):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(pedidos, f, indent=4, ensure_ascii=False)

def atualizar_status(pedido_id, novo_status):
    pedidos = carregar_pedidos()
    for p in pedidos:
        if str(p.get("id")) == str(pedido_id):
            p["status"] = novo_status
            salvar_pedidos(pedidos)
            return True
    return False

# ============================
# Interface do Entregador
# ============================
st.set_page_config(page_title="Entregador - POS-80", layout="wide")
st.title("🚚 Painel do Entregador")
st.caption("Visualize e confirme as entregas dos pedidos prontos para envio.")

pedidos = carregar_pedidos()
if not pedidos:
    st.info("Nenhum pedido disponível para entrega no momento.")
else:
    # Filtrar pedidos prontos para entrega ou em rota
    pedidos_entrega = [p for p in pedidos if p.get("status") in ["Em rota de entrega", "Pronto"] and p.get("tipo_pedido") == "Entrega"]

    if not pedidos_entrega:
        st.info("Nenhum pedido para entrega no momento.")
    else:
        for pedido in pedidos_entrega:
            with st.container():
                st.markdown("---")
                col1, col2, col3 = st.columns([3, 2, 2])

                with col1:
                    st.subheader(f"📦 Pedido #{pedido['codigo_rastreio']}")
                    st.write(f"👤 Cliente: **{pedido['nome']}**")
                    st.write(f"📞 {pedido['telefone']}")
                    st.write(f"🏠 Endereço: {pedido['endereco']}")
                    st.write(f"💵 Total: R$ {pedido['total']:.2f}")
                    if pedido.get("observacoes"):
                        st.caption(f"📝 Obs: {pedido['observacoes']}")

                with col2:
                    st.markdown("#### Itens do Pedido")
                    for item in pedido["produtos"]:
                        st.markdown(f"- {item['quantidade']}x {item['nome']} (R$ {item['preco']:.2f})")

                with col3:
                    st.markdown("#### Ações")
                    status_atual = pedido.get("status", "Pronto")
                    st.write(f"🟢 **Status atual:** {status_atual}")

                    if status_atual == "Pronto":
                        if st.button(f"🚚 Iniciar Entrega #{pedido['codigo_rastreio']}", key=f"iniciar_{pedido['id']}"):
                            atualizar_status(pedido["id"], "Em rota de entrega")
                            st.success("Entrega iniciada!")
                            st.rerun()

                    elif status_atual == "Em rota de entrega":
                        if st.button(f"✅ Confirmar Entrega #{pedido['codigo_rastreio']}", key=f"confirma_{pedido['id']}"):
                            atualizar_status(pedido["id"], "Entregue")
                            st.success("Pedido entregue com sucesso!")
                            st.rerun()

                    elif status_atual == "Entregue":
                        st.info("✅ Entrega concluída.")

# Rodapé
st.markdown("---")
st.caption("🔄 Atualize a página para ver novos pedidos prontos para entrega.")
