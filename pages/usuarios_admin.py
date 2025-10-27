import streamlit as st
import json
import os

USERS_FILE = "usuarios.json"

# =============================
# Funções auxiliares
# =============================
def carregar_usuarios():
    """Carrega os usuários do JSON ou cria padrão se não existir"""
    if not os.path.exists(USERS_FILE):
        usuarios_padrao = [
            {"usuario": "admin", "senha": "1234", "nome": "Administrador", "cargo": "admin"},
            {"usuario": "caixa", "senha": "1234", "nome": "Caixa", "cargo": "caixa"},
            {"usuario": "cozinha", "senha": "1234", "nome": "Cozinha", "cargo": "cozinha"},
            {"usuario": "entregador", "senha": "1234", "nome": "Entregador", "cargo": "entregador"},
        ]
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(usuarios_padrao, f, indent=4, ensure_ascii=False)
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except:
            return []

def salvar_usuarios(usuarios):
    """Salva os usuários no JSON"""
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(usuarios, f, indent=4, ensure_ascii=False)

# =============================
# Segurança
# =============================
if "logado" not in st.session_state or not st.session_state["logado"]:
    st.warning("⚠️ Acesso restrito. Faça login como administrador.")
    st.stop()

if st.session_state.get("cargo") != "admin":
    st.error("🚫 Você não tem permissão para acessar esta página.")
    st.stop()

# =============================
# Interface de Administração
# =============================
st.set_page_config(page_title="Administração de Usuários - THE RUA", layout="wide")
st.title("👥 Administração de Usuários")
st.caption("Gerencie contas e permissões de acesso ao sistema.")

usuarios = carregar_usuarios()

# =============================
# Adicionar novo usuário
# =============================
st.subheader("➕ Adicionar Novo Usuário")
with st.form("form_add_user"):
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        usuario = st.text_input("Usuário (login)")
    with col2:
        senha = st.text_input("Senha", type="password")
    with col3:
        nome = st.text_input("Nome completo")
    with col4:
        cargo = st.selectbox("Cargo", ["admin", "caixa", "cozinha", "entregador"])
    submitted = st.form_submit_button("💾 Adicionar Usuário")

    if submitted:
        if not usuario or not senha or not nome:
            st.error("⚠️ Todos os campos são obrigatórios.")
        elif any(u["usuario"] == usuario for u in usuarios):
            st.warning("⚠️ Já existe um usuário com esse login.")
        else:
            usuarios.append({
                "usuario": usuario,
                "senha": senha,
                "nome": nome,
                "cargo": cargo
            })
            salvar_usuarios(usuarios)
            st.success(f"✅ Usuário '{usuario}' adicionado com sucesso!")
            st.rerun()

# =============================
# Listagem e edição
# =============================
st.divider()
st.subheader("🧾 Usuários Cadastrados")

if not usuarios:
    st.info("Nenhum usuário cadastrado.")
else:
    for i, u in enumerate(usuarios):
        with st.expander(f"👤 {u.get('nome', 'Sem nome')} ({u.get('usuario', '-')})"):
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                novo_nome = st.text_input("Nome", value=u.get("nome", ""), key=f"nome_{i}")
            with col2:
                nova_senha = st.text_input("Senha", value=u.get("senha", ""), type="password", key=f"senha_{i}")
            with col3:
                novo_usuario = st.text_input("Usuário", value=u.get("usuario", ""), key=f"user_{i}")
            with col4:
                novo_cargo = st.selectbox(
                    "Cargo",
                    ["admin", "caixa", "cozinha", "entregador"],
                    index=["admin", "caixa", "cozinha", "entregador"].index(u.get("cargo", "caixa")),
                    key=f"cargo_{i}"
                )

            c1, c2 = st.columns([1, 1])
            with c1:
                if st.button("💾 Salvar Alterações", key=f"salvar_{i}"):
                    u["nome"] = novo_nome
                    u["senha"] = nova_senha
                    u["usuario"] = novo_usuario
                    u["cargo"] = novo_cargo
                    salvar_usuarios(usuarios)
                    st.success("✅ Alterações salvas com sucesso!")
                    st.rerun()
            with c2:
                if st.button("🗑️ Excluir Usuário", key=f"del_{i}"):
                    if u["usuario"] == "admin":
                        st.warning("⚠️ O usuário 'admin' não pode ser excluído.")
                    else:
                        usuarios.pop(i)
                        salvar_usuarios(usuarios)
                        st.warning(f"Usuário '{u['usuario']}' removido.")
                        st.rerun()
