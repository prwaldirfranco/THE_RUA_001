import streamlit as st
import json
import os
from datetime import datetime

if "logado" not in st.session_state or not st.session_state["logado"]:
    st.warning("⚠️ Acesso restrito. Faça login para continuar.")
    st.stop()

# ===============================
# Configurações e caminhos
# ===============================
st.set_page_config(page_title="Cadastro de Produtos - THE RUA", layout="wide")

DATA_FILE = "produtos.json"
PEDIDOS_FILE = "pedidos.json"
CAIXA_FILE = "caixa.json"
UPLOADS_DIR = "uploads/produtos"
os.makedirs(UPLOADS_DIR, exist_ok=True)

# ===============================
# Funções auxiliares
# ===============================
def carregar_produtos():
    """Carrega os produtos do JSON."""
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, indent=4, ensure_ascii=False)
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except:
            return []

def salvar_produtos(produtos):
    """Salva a lista de produtos no JSON."""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(produtos, f, indent=4, ensure_ascii=False)

def gerar_id(produtos):
    """Gera um novo ID incremental."""
    if not produtos:
        return "1"
    return str(max(int(p["id"]) for p in produtos) + 1)

def limpar_registros():
    """Limpa todos os registros do sistema (pedidos, caixa e produtos)."""
    with open(PEDIDOS_FILE, "w", encoding="utf-8") as f:
        json.dump([], f, indent=4, ensure_ascii=False)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump([], f, indent=4, ensure_ascii=False)
    with open(CAIXA_FILE, "w", encoding="utf-8") as f:
        json.dump({"aberto": False, "aberto_em": None, "fechado_em": None, "valor_inicial": 0.0}, f, indent=4, ensure_ascii=False)

# ===============================
# Interface principal
# ===============================
st.title("🍔 Administração - Cadastro e Manutenção de Produtos")
st.caption("Adicione, edite, gerencie os produtos e limpe registros do sistema.")

produtos = carregar_produtos()

# ------------------------------------------------
# 🧹 Botão de limpeza geral
# ------------------------------------------------
st.markdown("### ⚙️ Manutenção do Sistema")
if st.button("🧹 Limpar TODOS os Registros do Sistema"):
    limpar_registros()
    st.warning("⚠️ Todos os registros (pedidos, caixa e produtos) foram limpos!")
    st.balloons()
    st.stop()

st.divider()

# ------------------------------------------------
# Formulário de cadastro / edição
# ------------------------------------------------
with st.form("cadastro_produto_form"):
    st.subheader("🆕 Novo Produto")
    nome = st.text_input("Nome do produto")
    descricao = st.text_area("Descrição")
    preco = st.number_input("Preço (R$)", min_value=0.0, step=0.5)
    imagem = st.file_uploader("Imagem do produto", type=["png", "jpg", "jpeg"])

    # Novo: ingredientes e extras
    st.markdown("**Ingredientes padrão** (um por linha). Cliente poderá desmarcar ao pedir.")
    ingredientes_text = st.text_area("Ingredientes (ex: Pão\nCarne\nQueijo)")
    st.markdown("**Extras opcionais** — formato por linha: Nome:preco (ex: Bacon:3.50)")
    extras_text = st.text_area("Extras (ex:\nBacon:3.50\nCheddar:2.00)")

    enviado = st.form_submit_button("💾 Salvar Produto")
    if enviado:
        if not nome or preco <= 0:
            st.error("Por favor, preencha todos os campos obrigatórios (nome e preço).")
        else:
            produtos = carregar_produtos()
            novo_id = gerar_id(produtos)
            imagem_path = ""

            if imagem:
                imagem_path = os.path.join(UPLOADS_DIR, f"{int(datetime.now().timestamp())}_{imagem.name}")
                with open(imagem_path, "wb") as f:
                    f.write(imagem.getbuffer())

            # Parse ingredientes
            ingredientes = []
            if ingredientes_text:
                ingredientes = [line.strip() for line in ingredientes_text.splitlines() if line.strip()]

            # Parse extras
            extras = []
            if extras_text:
                for line in extras_text.splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    if ":" in line:
                        nome_extra, preco_extra = line.split(":", 1)
                        try:
                            preco_val = float(preco_extra.replace(",", ".").strip())
                        except:
                            preco_val = 0.0
                        extras.append({"nome": nome_extra.strip(), "preco": preco_val})
                    else:
                        # sem preco, ignora ou adiciona com preco 0
                        extras.append({"nome": line, "preco": 0.0})

            produto = {
                "id": novo_id,
                "nome": nome,
                "descricao": descricao,
                "preco": preco,
                "imagem": imagem_path.replace("\\", "/"),
                "ingredientes": ingredientes,
                "extras": extras,
                "criado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

            produtos.append(produto)
            salvar_produtos(produtos)
            st.success(f"✅ Produto **{nome}** cadastrado com sucesso!")
            st.balloons()
            st.rerun()

# ------------------------------------------------
# Listagem de produtos cadastrados
# ------------------------------------------------
st.divider()
st.subheader("📦 Produtos Cadastrados")

if not produtos:
    st.info("Nenhum produto cadastrado ainda.")
else:
    for p in produtos:
        with st.container():
            st.markdown("---")
            col1, col2, col3 = st.columns([2, 4, 2])

            with col1:
                if p.get("imagem") and os.path.exists(p["imagem"]):
                    st.image(p["imagem"], width=120)
                else:
                    st.image("https://via.placeholder.com/120x120.png?text=Sem+Imagem", width=120)

            with col2:
                st.write(f"### {p['nome']}")
                st.write(p.get("descricao", ""))
                st.write(f"💰 **R$ {p['preco']:.2f}**")
                st.caption(f"🕒 Cadastrado em: {p.get('criado_em', '-')}")
                # mostra ingredientes e extras no admin
                if p.get("ingredientes"):
                    st.markdown("**Ingredientes (padrão):** " + ", ".join(p.get("ingredientes", [])))
                if p.get("extras"):
                    extras_str = ", ".join([f"{e['nome']} (+R$ {float(e['preco']):.2f})" for e in p.get("extras", [])])
                    st.markdown("**Extras:** " + extras_str)

            with col3:
                if st.button("✏️ Editar", key=f"edit_{p['id']}"):
                    st.session_state["editando"] = p["id"]
                    st.rerun()
                if st.button("🗑️ Excluir", key=f"del_{p['id']}"):
                    produtos = [x for x in produtos if x["id"] != p["id"]]
                    salvar_produtos(produtos)
                    st.warning(f"Produto **{p['nome']}** removido.")
                    st.rerun()

# ------------------------------------------------
# Edição de produto existente
# ------------------------------------------------
if "editando" in st.session_state:
    edit_id = st.session_state["editando"]
    produto_editar = next((x for x in produtos if x["id"] == edit_id), None)
    if produto_editar:
        st.divider()
        st.subheader(f"✏️ Editar Produto - {produto_editar['nome']}")

        with st.form("editar_produto_form"):
            nome = st.text_input("Nome", produto_editar["nome"])
            descricao = st.text_area("Descrição", produto_editar.get("descricao", ""))
            preco = st.number_input("Preço (R$)", value=float(produto_editar.get("preco", 0.0)), step=0.5)
            nova_imagem = st.file_uploader("Alterar imagem (opcional)", type=["png", "jpg", "jpeg"])

            # show current ingredientes/extras as editable textareas
            ing_text = "\n".join(produto_editar.get("ingredientes", []))
            extras_lines = "\n".join([f"{e['nome']}:{e['preco']}" for e in produto_editar.get("extras", [])])

            ingredientes_text = st.text_area("Ingredientes (um por linha)", value=ing_text)
            extras_text = st.text_area("Extras (Nome:preco por linha)", value=extras_lines)

            enviar_edicao = st.form_submit_button("💾 Salvar Alterações")
            if enviar_edicao:
                produto_editar["nome"] = nome
                produto_editar["descricao"] = descricao
                produto_editar["preco"] = preco

                if nova_imagem:
                    imagem_path = os.path.join(UPLOADS_DIR, f"{int(datetime.now().timestamp())}_{nova_imagem.name}")
                    with open(imagem_path, "wb") as f:
                        f.write(nova_imagem.getbuffer())
                    produto_editar["imagem"] = imagem_path.replace("\\", "/")

                # parse ingredientes
                produto_editar["ingredientes"] = [line.strip() for line in ingredientes_text.splitlines() if line.strip()]

                # parse extras
                extras_new = []
                for line in extras_text.splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    if ":" in line:
                        nome_extra, preco_extra = line.split(":", 1)
                        try:
                            preco_val = float(preco_extra.replace(",", ".").strip())
                        except:
                            preco_val = 0.0
                        extras_new.append({"nome": nome_extra.strip(), "preco": preco_val})
                    else:
                        extras_new.append({"nome": line, "preco": 0.0})
                produto_editar["extras"] = extras_new

                salvar_produtos(produtos)
                del st.session_state["editando"]
                st.success("Produto atualizado com sucesso!")
                st.rerun()
