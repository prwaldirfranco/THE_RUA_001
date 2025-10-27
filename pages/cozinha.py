import streamlit as st
import json
import os
from datetime import datetime

# -----------------------------------
# Segurança — exige login
# -----------------------------------
if "logado" not in st.session_state or not st.session_state["logado"]:
    st.warning("⚠️ Acesso restrito. Faça login para continuar.")
    st.stop()

DATA_FILE = "pedidos.json"

# -----------------------------------
# Funções auxiliares
# -----------------------------------
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

# -----------------------------------
# Impressão (usa o mesmo painel do caixa)
# -----------------------------------
def imprimir_comanda(pedido):
    texto = f"""
====== COMANDA DE PRODUÇÃO ======
Data: {datetime.now().strftime("%d/%m/%Y %H:%M")}
Pedido: {pedido['codigo_rastreio']}
Cliente: {pedido['nome']}
Tipo: {pedido['tipo_pedido']}
"""
    if pedido["tipo_pedido"] == "Entrega":
        texto += f"Endereço: {pedido['endereco']}\n"

    texto += "\nItens:\n"
    for item in pedido.get("produtos", []):
        texto += f"- {item['quantidade']}x {item['nome']}\n"
        if item.get("removidos"):
            for r in item["removidos"]:
                texto += f"   ❌ Sem {r}\n"
        if item.get("extras"):
            for ex in item["extras"]:
                texto += f"   ➕ {ex['qtd']}x {ex['nome']}\n"

    texto += "\n==============================\n"
    st.text_area("🖨️ Comanda pronta para impressão:", texto, height=200)
    st.download_button("⬇️ Baixar Comanda (.txt)", texto, file_name=f"comanda_{pedido['codigo_rastreio']}.txt")

# -----------------------------------
# Interface principal
# -----------------------------------
st.set_page_config(page_title="Cozinha - THE RUA", layout="wide")
col1, col2 = st.columns([6, 1])
with col1:
    st.title("👨‍🍳 Painel da Cozinha")
    st.caption("Gerencie e atualize o status dos pedidos em preparo e prontos para entrega.")
with col2:
    st.markdown("<br>", unsafe_allow_html=True)  # espaço vertical
    if st.button("🚪 Sair", key="logout_cozinha"):
        import os, json
        if os.path.exists("session.json"):
            os.remove("session.json")
        st.session_state.clear()
        st.success("Sessão encerrada.")
        st.rerun()

# 🔄 Botão de atualização
st.markdown("### 🔄 Atualização Manual")
if st.button("🔁 Atualizar Pedidos"):
    st.success("Pedidos atualizados!")
    st.rerun()

pedidos = carregar_pedidos()
if not pedidos:
    st.info("Nenhum pedido encontrado.")
    st.stop()

# Exibe pedidos
for pedido in sorted(pedidos, key=lambda x: x.get("data", ""), reverse=True):
    st.markdown("---")
    col1, col2, col3 = st.columns([3, 2, 2])

    with col1:
        st.subheader(f"📦 Pedido #{pedido['codigo_rastreio']}")
        st.write(f"👤 Cliente: {pedido['nome']}")
        st.write(f"📞 {pedido['telefone']}")
        st.write(f"🕒 {pedido['data']}")
        st.write(f"💵 Total: R$ {pedido['total']:.2f}")
        st.write(f"📦 Tipo: {pedido['tipo_pedido']}")
        if pedido.get("observacoes"):
            st.caption(f"📝 Obs: {pedido['observacoes']}")

    with col2:
        st.markdown("### 🍔 Itens")
        for item in pedido["produtos"]:
            st.markdown(f"- {item['quantidade']}x {item['nome']}")
            if item.get("removidos"):
                st.caption(f"❌ Sem: {', '.join(item['removidos'])}")
            if item.get("extras"):
                st.caption("➕ " + ", ".join([f"{ex['qtd']}x {ex['nome']}" for ex in item['extras']]))

    with col3:
        st.markdown("### ⚙️ Ações")
        status_atual = pedido.get("status", "Aguardando aceite")
        st.write(f"🟢 Status atual: **{status_atual}**")

        if status_atual == "Aguardando aceite":
            if st.button("✅ Iniciar Preparo", key=f"prep_{pedido['id']}"):
                atualizar_status(pedido["id"], "Em preparo")
                st.success("Pedido em preparo!")
                st.rerun()

        elif status_atual == "Em preparo":
            if st.button("🍟 Marcar como Pronto", key=f"pronto_{pedido['id']}"):
                atualizar_status(pedido["id"], "Pronto")
                st.success("Pedido pronto para entrega!")
                st.rerun()

        elif status_atual == "Pronto":
            st.info("✅ Pedido pronto para entrega.")

        st.divider()
        if st.button("🖨️ Imprimir Comanda", key=f"imp_{pedido['id']}"):
            imprimir_comanda(pedido)

# Rodapé
st.markdown("---")
st.caption("🔄 Use o botão 'Atualizar Pedidos' para recarregar as informações sem precisar reiniciar a página.")
