# app.py — Sistema centralizado (Cardápio público + Rastreio + Login/Menu)
import streamlit as st
import json
import os
import random
import time
from datetime import datetime

# ----------------------------
# Config + esconder menu padrão
# ----------------------------
st.set_page_config(page_title="THE RUA BURGUER", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
        [data-testid="stSidebarNav"] {display: none !important;}
        [data-testid="stSidebar"] section[data-testid="stSidebarNav"] {display: none !important;}
    </style>
""", unsafe_allow_html=True)

# ----------------------------
# Arquivos de dados
# ----------------------------
PEDIDOS_FILE = "pedidos.json"
PRODUTOS_FILE = "produtos.json"
USERS_FILE = "usuarios.json"
SESSION_FILE = "session.json"
UPLOADS_DIR = "uploads"
os.makedirs(UPLOADS_DIR, exist_ok=True)

# ----------------------------
# Utilitários
# ----------------------------
def garantir_json(path, default):
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(default, f, indent=4, ensure_ascii=False)

def carregar_json(path):
    garantir_json(path, [])
    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except:
            return []

def salvar_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def gerar_codigo_rastreio():
    return f"{random.randint(1000,9999)}"

# ----------------------------
# Sessão persistente
# ----------------------------
def carregar_sessao():
    if os.path.exists(SESSION_FILE):
        try:
            with open(SESSION_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                st.session_state.update(data)
        except:
            pass

def salvar_sessao():
    data = {k: v for k, v in st.session_state.items() if k in ["logado", "usuario", "nome", "cargo"]}
    with open(SESSION_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f)

def limpar_sessao():
    if os.path.exists(SESSION_FILE):
        os.remove(SESSION_FILE)
    st.session_state.clear()

carregar_sessao()

# ----------------------------
# Usuários
# ----------------------------
def carregar_usuarios():
    if not os.path.exists(USERS_FILE):
        usuarios_padrao = [
            {"usuario": "admin", "senha": "1234", "nome": "Administrador", "cargo": "admin"},
            {"usuario": "caixa", "senha": "1234", "nome": "Caixa", "cargo": "caixa"},
            {"usuario": "cozinha", "senha": "1234", "nome": "Cozinha", "cargo": "cozinha"},
            {"usuario": "entregador", "senha": "1234", "nome": "Entregador", "cargo": "entregador"}
        ]
        salvar_json(USERS_FILE, usuarios_padrao)
    return carregar_json(USERS_FILE)

def validar_login(usuario, senha):
    usuarios = carregar_usuarios()
    for u in usuarios:
        if u["usuario"] == usuario and u["senha"] == senha:
            return u
    return None

# ----------------------------
# Renderizadores de páginas
# ----------------------------
def render_cardapio_publico():
    st.title("🍔 Cardápio Público - THE RUA")
    st.caption("Monte seu pedido como quiser — retire, adicione ingredientes e acompanhe o pedido com um código de rastreio.")

    produtos = carregar_json(PRODUTOS_FILE)
    if not produtos:
        st.warning("⚠️ Nenhum produto cadastrado ainda.")
        return

    if "carrinho" not in st.session_state:
        st.session_state.carrinho = []

    cols = st.columns(2)
    for i, produto in enumerate(produtos):
        with cols[i % 2]:
            img = produto.get("imagem", "")
            if img and os.path.exists(img):
                st.image(img, width=250)
            elif produto.get("imagem", "").startswith("http"):
                st.image(produto["imagem"], width=250)
            else:
                st.image("https://via.placeholder.com/250x250.png?text=Sem+Imagem", width=250)
            st.subheader(produto["nome"])
            st.caption(produto.get("descricao", ""))
            st.markdown(f"💰 **R$ {float(produto['preco']):.2f}**")

            # Ingredientes padrão
            ingredientes = produto.get("ingredientes", [])
            removidos = []
            if ingredientes:
                st.markdown("**Ingredientes (desmarque o que deseja remover):**")
                for ing in ingredientes:
                    if not st.checkbox(ing, value=True, key=f"ing_{produto['id']}_{ing}"):
                        removidos.append(ing)

            # Extras opcionais
            extras = produto.get("extras", [])
            extras_escolhidos = []
            if extras:
                nomes_extras = [f"{e['nome']} (+R$ {e['preco']:.2f})" for e in extras]
                sel = st.multiselect("Extras:", nomes_extras, key=f"ext_{produto['id']}")
                for s in sel:
                    nome = s.split(" (+R$")[0]
                    item = next((x for x in extras if x["nome"] == nome), None)
                    if item:
                        qtd = st.number_input(f"Qtd {nome}", min_value=1, value=1, key=f"qtd_{produto['id']}_{nome}")
                        extras_escolhidos.append({"nome": nome, "preco": float(item["preco"]), "qtd": int(qtd)})

            # Quantidade e adicionar
            qtd = st.number_input(f"Qtd {produto['nome']}", min_value=0, step=1, key=f"qtd_{produto['id']}")
            if qtd > 0:
                if st.button(f"Adicionar {produto['nome']}", key=f"add_{produto['id']}"):
                    extras_total = sum(e["preco"] * e["qtd"] for e in extras_escolhidos)
                    subtotal = (float(produto["preco"]) + extras_total) * qtd
                    st.session_state.carrinho.append({
                        "id": produto["id"],
                        "nome": produto["nome"],
                        "quantidade": qtd,
                        "preco": float(produto["preco"]),
                        "subtotal": subtotal,
                        "removidos": removidos,
                        "extras": extras_escolhidos
                    })
                    st.success(f"{produto['nome']} adicionado!")
                    st.rerun()

    st.divider()
    st.header("🛒 Seu Carrinho")
    if not st.session_state.carrinho:
        st.info("Seu carrinho está vazio.")
    else:
        total = 0
        for i, item in enumerate(st.session_state.carrinho):
            total += item["subtotal"]
            st.markdown(f"**{item['quantidade']}x {item['nome']} — R$ {item['subtotal']:.2f}**")
            if item["removidos"]:
                st.caption("❌ Sem: " + ", ".join(item["removidos"]))
            if item["extras"]:
                for ex in item["extras"]:
                    st.caption(f"➕ {ex['qtd']}x {ex['nome']} (+R$ {ex['preco']:.2f})")
            if st.button(f"Remover {item['nome']}", key=f"rm_{i}"):
                st.session_state.carrinho.pop(i)
                st.rerun()
        st.markdown(f"### 💰 Total: R$ {total:.2f}")

        st.divider()
        nome = st.text_input("Nome completo")
        telefone = st.text_input("Telefone / WhatsApp")
        tipo_pedido = st.radio("Tipo de pedido", ["Consumir no local", "Retirada", "Entrega"])
        endereco = st.text_area("Endereço completo") if tipo_pedido == "Entrega" else ""
        pagamento = st.selectbox("Forma de pagamento", ["Dinheiro", "Cartão", "Pix", "Transferência"])
        troco_para, comprovante_path = "", ""

        if pagamento == "Dinheiro":
            troco_para = st.text_input("Troco para quanto?")
        elif pagamento == "Pix":
            comprovante = st.file_uploader("Anexar comprovante (opcional)", type=["png","jpg","jpeg","pdf"])
            if comprovante:
                fname = f"{int(time.time())}_{comprovante.name}"
                path = os.path.join(UPLOADS_DIR, fname)
                with open(path, "wb") as f:
                    f.write(comprovante.getbuffer())
                comprovante_path = path

        observacoes = st.text_area("Observações (ex: sem cebola, bem passado...)")

        if st.button("✅ Confirmar Pedido"):
            if not nome or not telefone:
                st.error("Preencha nome e telefone.")
            else:
                codigo = gerar_codigo_rastreio()
                pedido = {
                    "id": str(int(time.time())),
                    "codigo_rastreio": codigo,
                    "nome": nome,
                    "telefone": telefone,
                    "tipo_pedido": tipo_pedido,
                    "endereco": endereco,
                    "pagamento": pagamento,
                    "troco_para": troco_para,
                    "comprovante": comprovante_path,
                    "observacoes": observacoes,
                    "produtos": st.session_state.carrinho,
                    "status": "Aguardando aceite",
                    "data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "total": total
                }
                pedidos = carregar_json(PEDIDOS_FILE)
                pedidos.append(pedido)
                salvar_json(PEDIDOS_FILE, pedidos)
                st.session_state.carrinho = []
                st.session_state["ultimo_codigo"] = codigo
                st.success("🎉 Pedido realizado com sucesso!")
                st.balloons()
                st.rerun()

    # ---------------------------
    # POP-UP do código de rastreio (mantém após o rerun)
    # ---------------------------
    if "ultimo_codigo" in st.session_state and st.session_state["ultimo_codigo"]:
        with st.container():
            st.markdown("### ✅ Pedido Confirmado!")
            st.info(f"Seu código de rastreio é: **{st.session_state['ultimo_codigo']}**")
            if st.button("🆗 Fechar aviso"):
                st.session_state["ultimo_codigo"] = ""
                st.rerun()

# ----------------------------
# Rastreio
# ----------------------------
def render_rastreamento():
    st.title("🔎 Rastreio de Pedido")
    codigo = st.text_input("Código de rastreio")
    if st.button("Pesquisar"):
        pedidos = carregar_json(PEDIDOS_FILE)
        encontrados = [p for p in pedidos if str(p["codigo_rastreio"]) == codigo]
        if not encontrados:
            st.warning("Código não encontrado.")
            return
        p = encontrados[0]
        st.success(f"Pedido #{p['codigo_rastreio']} — {p['status']}")
        st.write(f"👤 {p['nome']} — {p['telefone']}")
        st.write(f"🕒 {p['data']}")
        for item in p["produtos"]:
            st.write(f"- {item['quantidade']}x {item['nome']}")
            if item["removidos"]:
                st.caption("❌ Sem: " + ", ".join(item["removidos"]))
            if item["extras"]:
                for ex in item["extras"]:
                    st.caption(f"➕ {ex['qtd']}x {ex['nome']} (+R$ {ex['preco']:.2f})")
        st.markdown(f"💰 **Total: R$ {p['total']:.2f}**")

# ----------------------------
# Menu principal
# ----------------------------
if "logado" not in st.session_state:
    st.session_state["logado"] = False

st.sidebar.title("🍔 THE RUA")

if not st.session_state["logado"]:
    escolha = st.sidebar.radio("Menu", ["Cardápio Público", "Rastreio", "Login"])
else:
    cargo = st.session_state.get("cargo", "")
    if cargo == "admin":
        escolha = st.sidebar.radio("Menu", ["Cardápio Público", "Rastreio", "Caixa", "Cozinha", "Entregador", "Relatórios", "Administração", "Sair"])
    elif cargo == "caixa":
        escolha = st.sidebar.radio("Menu", ["Caixa", "Relatórios", "Sair"])
    elif cargo == "cozinha":
        escolha = st.sidebar.radio("Menu", ["Cozinha", "Sair"])
    elif cargo == "entregador":
        escolha = st.sidebar.radio("Menu", ["Entregador", "Sair"])
    else:
        escolha = st.sidebar.radio("Menu", ["Cardápio Público", "Rastreio", "Sair"])

# ----------------------------
# Ações de menu
# ----------------------------
if escolha == "Login":
    st.title("🔐 Login")
    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        user = validar_login(usuario, senha)
        if user:
            cargo = user.get("cargo", user["usuario"])
            st.session_state["logado"] = True
            st.session_state["usuario"] = user["usuario"]
            st.session_state["nome"] = user["nome"]
            st.session_state["cargo"] = cargo
            salvar_sessao()
            st.success(f"Bem-vindo(a), {user['nome']}! ({cargo.upper()})")
            st.rerun()
        else:
            st.error("Usuário/senha inválidos.")

elif escolha == "Sair":
    limpar_sessao()
    st.success("Sessão encerrada.")
    st.rerun()

elif escolha == "Cardápio Público":
    render_cardapio_publico()

elif escolha == "Rastreio":
    render_rastreamento()

else:
    if not st.session_state["logado"]:
        st.warning("⚠️ Acesso restrito.")
        st.stop()

    mapping = {
        "Caixa": "pages/caixa.py",
        "Cozinha": "pages/cozinha.py",
        "Entregador": "pages/entregador.py",
        "Relatórios": "pages/relatorios.py",
        "Administração": "pages/cadastro_produtos.py"
    }
    target = mapping.get(escolha, None)
    if target and os.path.exists(target):
        st.switch_page(target)
    else:
        st.warning("Página não encontrada.")
