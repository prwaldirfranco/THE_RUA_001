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

# Esconde o menu de páginas automático do Streamlit
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
# Carregar/validar usuários (simples)
# ----------------------------
def carregar_usuarios():
    if not os.path.exists(USERS_FILE):
        usuarios_padrao = [
            {"usuario": "admin", "senha": "1234", "nome": "Administrador"},
            {"usuario": "caixa", "senha": "1234", "nome": "Caixa"},
            {"usuario": "cozinha", "senha": "1234", "nome": "Cozinha"},
            {"usuario": "entregador", "senha": "1234", "nome": "Entregador"}
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
    st.caption("Escolha seus produtos, monte seu pedido e acompanhe com um código de rastreio.")

    produtos = carregar_json(PRODUTOS_FILE)
    if not produtos:
        st.warning("⚠️ Nenhum produto cadastrado ainda. Aguarde o administrador ou acesse Administração.")
        return

    # Estado do carrinho
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
            qtd = st.number_input(f"Qtd {produto['nome']}", min_value=0, step=1, key=f"q_{produto['id']}")
            if qtd > 0:
                if st.button(f"Adicionar {produto['nome']}", key=f"add_{produto['id']}"):
                    st.session_state.carrinho.append({
                        "id": produto["id"],
                        "nome": produto["nome"],
                        "quantidade": qtd,
                        "preco": float(produto["preco"])
                    })
                    st.success(f"{produto['nome']} adicionado ao carrinho!")

    st.divider()
    st.header("🛒 Seu Carrinho")
    if not st.session_state.carrinho:
        st.info("Seu carrinho está vazio.")
    else:
        total = 0
        for i, item in enumerate(st.session_state.carrinho):
            sub = item["quantidade"] * item["preco"]
            total += sub
            st.write(f"**{item['quantidade']}x {item['nome']}** — R$ {sub:.2f}")
            if st.button(f"❌ Remover {item['nome']}", key=f"rm_{i}"):
                st.session_state.carrinho.pop(i)
                st.rerun()
        st.markdown(f"### 💵 Total: R$ {total:.2f}")

        st.divider()
        st.header("📦 Finalizar Pedido")
        nome = st.text_input("Nome completo")
        telefone = st.text_input("Telefone / WhatsApp")
        tipo_pedido = st.radio("Tipo de pedido", ["Consumir no local", "Retirada", "Entrega"])
        endereco = ""
        if tipo_pedido == "Entrega":
            endereco = st.text_area("Endereço completo")
        pagamento = st.selectbox("Forma de pagamento", ["Dinheiro", "Cartão", "Pix", "Transferência"])
        troco_para = ""
        comprovante_path = ""
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
        observacoes = st.text_area("Observações (ex: sem alface)")

        if st.button("✅ Confirmar Pedido"):
            if not nome or not telefone:
                st.error("Preencha nome e telefone.")
            elif not st.session_state.carrinho:
                st.error("Carrinho vazio.")
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
                st.success(f"🎉 Pedido realizado! Código: {codigo}")
                st.balloons()
                st.rerun()

    if "ultimo_codigo" in st.session_state:
        st.info(f"✅ Pedido registrado. Seu código de rastreio: **{st.session_state['ultimo_codigo']}**")
        if st.button("Fechar aviso"):
            del st.session_state["ultimo_codigo"]
            st.rerun()

def render_rastreamento():
    st.title("🔎 Rastreio de Pedido")
    st.caption("Digite seu código de rastreio (4 dígitos) para ver o status do pedido.")
    codigo = st.text_input("Código de rastreio")
    if st.button("Pesquisar"):
        if not codigo:
            st.error("Digite o código.")
            return
        pedidos = carregar_json(PEDIDOS_FILE)
        encontrados = [p for p in pedidos if str(p.get("codigo_rastreio","")) == str(codigo)]
        if not encontrados:
            st.warning("Código não encontrado. Verifique e tente novamente.")
            return
        p = encontrados[0]
        st.success(f"Pedido #{p.get('codigo_rastreio')} — Status: {p.get('status')}")
        st.write(f"👤 Cliente: {p.get('nome')} — {p.get('telefone')}")
        st.write(f"🕒 Data: {p.get('data')}")
        st.write(f"📦 Tipo: {p.get('tipo_pedido')}")
        if p.get("tipo_pedido") == "Entrega":
            st.write(f"📍 Endereço: {p.get('endereco')}")
        st.write("🧾 Itens:")
        for item in p.get("produtos", []):
            st.write(f"- {item.get('quantidade')}x {item.get('nome')} (R$ {item.get('preco'):.2f})")
        st.write(f"💵 Total: R$ {p.get('total',0):.2f}")
        if p.get("comprovante") and os.path.exists(p.get("comprovante")):
            with open(p["comprovante"], "rb") as f:
                st.download_button("📎 Baixar comprovante", data=f, file_name=os.path.basename(p["comprovante"]))

# ----------------------------
# Menu e fluxo principal
# ----------------------------
if "logado" not in st.session_state:
    st.session_state["logado"] = False
if "pagina" not in st.session_state:
    st.session_state["pagina"] = "Cardápio Público"

st.sidebar.title("🍔 THE RUA")
if not st.session_state["logado"]:
    escolha = st.sidebar.radio("Menu", ["Cardápio Público", "Rastreio", "Login"])
else:
    escolha = st.sidebar.radio("Menu", ["Cardápio Público", "Rastreio", "Caixa", "Cozinha", "Entregador", "Relatórios", "Administração"])

if escolha == "Login":
    st.title("🔐 Login")
    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        user = validar_login(usuario, senha)
        if user:
            st.session_state["logado"] = True
            st.session_state["usuario"] = user["usuario"]
            st.session_state["nome"] = user["nome"]
            st.success(f"Bem-vindo(a), {user['nome']}!")
            st.rerun()
        else:
            st.error("Usuário/senha inválidos.")
    st.info("Apenas o Cardápio e o Rastreio estão disponíveis sem login.")

else:
    if escolha == "Cardápio Público":
        render_cardapio_publico()
    elif escolha == "Rastreio":
        render_rastreamento()
    else:
        if not st.session_state["logado"]:
            st.warning("⚠️ Acesso restrito — faça login para ver essa página.")
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
            st.warning("Página administrativa não encontrada no diretório `pages/`.")
