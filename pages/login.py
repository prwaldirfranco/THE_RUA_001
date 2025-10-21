import streamlit as st

if "logado" not in st.session_state or not st.session_state["logado"]:
    st.warning("⚠️ Acesso restrito. Faça login para continuar.")
    st.stop()\

st.title("THE RUA")

usuario = st.text_input("Usuário")
senha = st.text_input("Senha", type="password")

if st.button("Entrar"):
    # Simples validação (expanda com banco ou JSON)
    if usuario == "admin" and senha == "admin123":
        st.session_state["logado"] = True
        st.session_state["usuario"] = usuario
        st.session_state["nivel"] = "admin"
        st.experimental_rerun()
    elif usuario == "atendente" and senha == "atendente123":
        st.session_state["logado"] = True
        st.session_state["usuario"] = usuario
        st.session_state["nivel"] = "atendente"
        st.experimental_rerun()
    else:
        st.error("Usuário ou senha inválidos")
