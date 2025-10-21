import streamlit as st

if "logado" not in st.session_state or not st.session_state["logado"]:
    st.warning("⚠️ Acesso restrito. Faça login para continuar.")
    st.stop()

if "logado" not in st.session_state or not st.session_state["logado"]:
    st.warning("⚠️ Acesso restrito. Faça login para continuar.")
    st.stop()

st.title("Gerenciar Usuários")

usuario = st.text_input("Usuário")
senha = st.text_input("Senha", type="password")
nivel = st.selectbox("Nível", ["admin", "atendente"])

if st.button("Cadastrar Usuário"):
    if usuario and senha:
        # Salvar no banco/json
        st.success(f"Usuário {usuario} cadastrado.")
    else:
        st.error("Preencha todos os campos.")
