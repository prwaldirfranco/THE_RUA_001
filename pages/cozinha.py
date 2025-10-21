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
# Interface da Cozinha
# ============================
st.set_page_config(page_title="Cozinha - POS-80", layout="wide")
st.title("👨‍🍳 Painel da Cozinha")
st.caption("Visualize e gerencie os pedidos aceitos pelo caixa.")

pedidos = carregar_pedidos()
if not pedidos:
    st.info("Nenhum pedido disponível no momento.")
else:
    # Filtrar apenas pedidos em preparo
    pedidos_em_preparo = [p for p in pedidos if p.get("status") in ["Em preparo", "Aguardando aceite"]]

    if not pedidos_em_preparo:
        st.info("Nenhum pedido pendente ou em preparo.")
    else:
        for pedido in pedidos_em_preparo:
            with st.container():
                st.markdown("---")
                col1, col2, col3 = st.columns([3, 2, 2])

                with col1:
                    st.subheader(f"📦 Pedido #{pedido['codigo_rastreio']}")
                    st.write(f"👤 {pedido['nome']} — {pedido['telefone']}")
                    st.write(f"🕒 {pedido['data']}")
                    st.write(f"💵 Total: R$ {pedido['total']:.2f}")
                    st.write(f"📦 Tipo: {pedido['tipo_pedido']}")
                    if pedido["tipo_pedido"] == "Entrega":
                        st.caption(f"📍 Endereço: {pedido['endereco']}")
                    if pedido.get("observacoes"):
                        st.caption(f"📝 Obs: {pedido['observacoes']}")

                with col2:
                    st.markdown("#### Itens do Pedido")
                    for item in pedido["produtos"]:
                        st.markdown(f"- {item['quantidade']}x {item['nome']} (R$ {item['preco']:.2f})")

                with col3:
                    st.markdown("#### Ações")

                    status_atual = pedido.get("status", "Aguardando aceite")
                    st.write(f"🟢 **Status atual:** {status_atual}")

                    if status_atual == "Aguardando aceite":
                        if st.button(f"✅ Aceitar Pedido #{pedido['codigo_rastreio']}", key=f"aceita_{pedido['id']}"):
                            atualizar_status(pedido["id"], "Em preparo")
                            st.success("Pedido aceito! Iniciando preparo...")
                            st.experimental_rerun()

                    elif status_atual == "Em preparo":
                        if st.button(f"🍔 Pedido Pronto #{pedido['codigo_rastreio']}", key=f"pronto_{pedido['id']}"):
                            if pedido["tipo_pedido"] == "Entrega":
                                atualizar_status(pedido["id"], "Em rota de entrega")
                                st.success("Pedido pronto e enviado para entrega!")
                            else:
                                atualizar_status(pedido["id"], "Pronto")
                                st.success("Pedido pronto para retirada ou consumo local!")
                            st.rerun()

                    elif status_atual in ["Pronto", "Em rota de entrega"]:
                        st.info("Aguardando entrega ou retirada.")

# Rodapé
st.markdown("---")
st.caption("🕒 Atualize a página para ver novos pedidos chegando em tempo real.")
