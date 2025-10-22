import streamlit as st
import json
import os
from datetime import datetime
import win32print, win32ui

CONFIG_FILE = "impressoras.json"

# ============================================================
# Funções utilitárias
# ============================================================
def carregar_impressoras():
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, indent=4, ensure_ascii=False)
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except:
            return []

def salvar_impressoras(impressoras):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(impressoras, f, indent=4, ensure_ascii=False)

def imprimir_teste(nome_impressora):
    """Faz uma impressão de teste local."""
    try:
        printer_name = nome_impressora or win32print.GetDefaultPrinter()
        hDC = win32ui.CreateDC()
        hDC.CreatePrinterDC(printer_name)
        hDC.StartDoc("Impressão de Teste POS-80")
        hDC.StartPage()

        font = win32ui.CreateFont({
            "name": "Arial",
            "height": 18 * -1,
            "weight": 400
        })
        hDC.SelectObject(font)
        y = 80
        for linha in [
            "====== TESTE DE IMPRESSÃO ======",
            f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
            "Sistema POS-80 Hamburgueria",
            "Impressora funcionando corretamente!",
            "==============================="
        ]:
            hDC.TextOut(80, y, linha)
            y += 80
        hDC.EndPage()
        hDC.EndDoc()
        hDC.DeleteDC()
        st.success("🖨️ Impressão de teste enviada com sucesso!")
    except Exception as e:
        st.error(f"Erro ao imprimir: {e}")

# ============================================================
# Interface
# ============================================================
st.title("🖨️ Configuração de Impressoras - POS-80")
st.caption("Adicione impressoras Bluetooth, USB, IP ou locais para uso automático no sistema.")

impressoras = carregar_impressoras()

# ---------------------------
# Formulário de nova impressora
# ---------------------------
with st.form("form_add_imp"):
    st.subheader("➕ Adicionar Impressora")
    nome = st.text_input("Nome da impressora (ex: POS-80 Balcão)")
    tipo = st.selectbox("Tipo de conexão", ["Bluetooth", "USB", "Wi-Fi / IP", "Local (Windows)"])
    endereco = st.text_input("Endereço (MAC, IP ou nome da impressora local)")
    salvar = st.form_submit_button("💾 Salvar Impressora")

    if salvar:
        if not nome:
            st.error("Informe um nome para a impressora.")
        else:
            nova = {"id": len(impressoras) + 1, "nome": nome, "tipo": tipo, "endereco": endereco}
            impressoras.append(nova)
            salvar_impressoras(impressoras)
            st.success("✅ Impressora adicionada com sucesso!")
            st.rerun()

st.divider()
st.subheader("📋 Impressoras Configuradas")

if not impressoras:
    st.info("Nenhuma impressora cadastrada ainda.")
else:
    for imp in impressoras:
        col1, col2, col3, col4 = st.columns([3, 3, 2, 2])
        with col1:
            st.write(f"**{imp['nome']}**")
            st.caption(f"{imp['tipo']} — {imp['endereco'] or 'Automática'}")
        with col2:
            if st.button("🖨️ Testar", key=f"test_{imp['id']}"):
                imprimir_teste(imp['endereco'])
        with col3:
            if st.button("✏️ Editar", key=f"edit_{imp['id']}"):
                st.session_state["edit_imp"] = imp
                st.rerun()
        with col4:
            if st.button("🗑️ Remover", key=f"del_{imp['id']}"):
                impressoras = [i for i in impressoras if i["id"] != imp["id"]]
                salvar_impressoras(impressoras)
                st.warning(f"Impressora {imp['nome']} removida.")
                st.rerun()

# ---------------------------
# Edição
# ---------------------------
if "edit_imp" in st.session_state:
    imp = st.session_state["edit_imp"]
    st.divider()
    st.subheader(f"✏️ Editar Impressora - {imp['nome']}")
    with st.form("edit_form_imp"):
        nome = st.text_input("Nome", imp["nome"])
        tipo = st.selectbox("Tipo de conexão", ["Bluetooth", "USB", "Wi-Fi / IP", "Local (Windows)"], index=["Bluetooth","USB","Wi-Fi / IP","Local (Windows)"].index(imp["tipo"]))
        endereco = st.text_input("Endereço", imp["endereco"])
        salvar_edit = st.form_submit_button("💾 Salvar Alterações")
        if salvar_edit:
            for i in impressoras:
                if i["id"] == imp["id"]:
                    i.update({"nome": nome, "tipo": tipo, "endereco": endereco})
            salvar_impressoras(impressoras)
            del st.session_state["edit_imp"]
            st.success("Impressora atualizada!")
            st.rerun()
