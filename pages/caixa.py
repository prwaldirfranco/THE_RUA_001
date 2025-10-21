import streamlit as st
import json
import os
from datetime import datetime

# ---------------------------------------------------
# Segurança — exige login antes de acessar a página
# ---------------------------------------------------
if "logado" not in st.session_state or not st.session_state["logado"]:
    st.warning("⚠️ Acesso restrito. Faça login para continuar.")
    st.stop()

# ---------------------------------------------------
# Caminhos e arquivos de dados
# ---------------------------------------------------
DATA_FILE = "pedidos.json"
CAIXA_FILE = "caixa.json"

# ---------------------------------------------------
# Funções utilitárias
# ---------------------------------------------------
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

def excluir_pedido(pedido_id):
    pedidos = carregar_pedidos()
    pedidos = [p for p in pedidos if str(p.get("id")) != str(pedido_id)]
    salvar_pedidos(pedidos)

def atualizar_status(pedido_id, novo_status):
    pedidos = carregar_pedidos()
    for p in pedidos:
        if str(p.get("id")) == str(pedido_id):
            p["status"] = novo_status
            salvar_pedidos(pedidos)
            return True
    return False

# ---------------------------------------------------
# Impressão via Win32 (local)
# ---------------------------------------------------
def imprimir_texto(texto, titulo="PEDIDO THE RUA"):
    try:
        printer_name = win32print.GetDefaultPrinter()
        hDC = win32ui.CreateDC()
        hDC.CreatePrinterDC(printer_name)
        hDC.StartDoc(titulo)
        hDC.StartPage()

        # Define fonte tamanho 18 (altura ajustada)
        font = win32ui.CreateFont({
            "name": "Arial",
            "height": -25,  # equivalente a tamanho 18
            "weight": 400,
        })
        hDC.SelectObject(font)

        # Posição e espaçamento otimizados
        x, y = 20, 30
        for linha in texto.splitlines():
            hDC.TextOut(x, y, linha.strip())
            y += 50  # espaçamento entre linhas reduzido

        hDC.EndPage()
        hDC.EndDoc()
        hDC.DeleteDC()
        st.success("🖨️ Impressão enviada para POS-80 (local).")

    except Exception as e:
        st.error(f"Erro ao imprimir: {e}")

def imprimir_pedido(pedido):
    texto = f"""
====== THE RUA HAMBURGUERIA ======
Data: {datetime.now().strftime("%d/%m/%Y %H:%M")}
Código: {pedido['codigo_rastreio']}
Cliente: {pedido['nome']}
Telefone: {pedido['telefone']}
Tipo: {pedido['tipo_pedido']}
"""
    if pedido["tipo_pedido"] == "Entrega":
        texto += f"Endereço: {pedido['endereco']}\n"

    texto += "\nItens:\n"
    for item in pedido.get("produtos", []):
        texto += f"- {item['quantidade']}x {item['nome']} R$ {item['preco'] * item['quantidade']:.2f}\n"

    texto += f"\nTotal: R$ {pedido['total']:.2f}\nPagamento: {pedido['pagamento']}\n"
    if pedido.get("troco_para"):
        texto += f"Troco para: {pedido['troco_para']}\n"
    if pedido.get("observacoes"):
        texto += f"Obs: {pedido['observacoes']}\n"
    texto += "\n==============================\n"

    imprimir_texto(texto, titulo="Pedido THE RUA")

# ---------------------------------------------------
# Controle de caixa
# ---------------------------------------------------
def carregar_caixa():
    if not os.path.exists(CAIXA_FILE):
        return {"aberto": False, "aberto_em": None, "fechado_em": None, "valor_inicial": 0.0}
    with open(CAIXA_FILE, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
            if not isinstance(data, dict):
                data = {"aberto": False, "valor_inicial": 0.0}
            if "valor_inicial" not in data:
                data["valor_inicial"] = 0.0
            return data
        except:
            return {"aberto": False, "valor_inicial": 0.0}

def salvar_caixa(caixa):
    with open(CAIXA_FILE, "w", encoding="utf-8") as f:
        json.dump(caixa, f, indent=4, ensure_ascii=False)

def abrir_caixa(valor_inicial=0.0):
    caixa = {
        "aberto": True,
        "aberto_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "fechado_em": None,
        "valor_inicial": float(valor_inicial)
    }
    salvar_caixa(caixa)

def fechar_caixa():
    caixa = carregar_caixa()
    caixa["aberto"] = False
    caixa["fechado_em"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    salvar_caixa(caixa)
    return caixa

def gerar_relatorio_caixa():
    pedidos = carregar_pedidos()
    if not pedidos:
        return None
    total_geral = sum(p.get("total", 0) for p in pedidos)
    por_pagamento = {}
    for p in pedidos:
        pg = p.get("pagamento", "Outros")
        por_pagamento[pg] = por_pagamento.get(pg, 0) + p.get("total", 0)
    return {"total": total_geral, "pagamentos": por_pagamento, "qtd": len(pedidos)}

# ---------------------------------------------------
# Interface principal
# ---------------------------------------------------
st.set_page_config(page_title="Caixa - THE RUA", layout="wide")
st.title("💵 Painel do Caixa")
st.caption("Gerencie pedidos, vendas no balcão e o fechamento do caixa.")

# Abertura / Fechamento
st.sidebar.header("🧾 Controle de Caixa")
caixa = carregar_caixa()

if not caixa.get("aberto", False):
    with st.sidebar.form("abrir_caixa_form"):
        valor_inicial = st.number_input("Valor inicial (R$)", min_value=0.0, step=10.0, value=0.0)
        if st.form_submit_button("🔓 Abrir Caixa"):
            abrir_caixa(valor_inicial)
            st.success(f"Caixa aberto com R$ {valor_inicial:.2f}.")
            st.rerun()
else:
    st.sidebar.success(f"✅ Caixa aberto em: {caixa['aberto_em']}")
    st.sidebar.info(f"💵 Valor inicial: R$ {caixa['valor_inicial']:.2f}")
    if st.sidebar.button("🔒 Fechar Caixa"):
        rel = gerar_relatorio_caixa()
        fechado = fechar_caixa()
        if rel:
            dinheiro = rel["pagamentos"].get("Dinheiro", 0.0)
            total_final = caixa["valor_inicial"] + dinheiro
            resumo = f"""
====== FECHAMENTO THE RUA ======
Aberto em: {caixa['aberto_em']}
Fechado em: {fechado['fechado_em']}

Valor inicial: R$ {caixa['valor_inicial']:.2f}
Total pedidos: {rel['qtd']}
Total geral: R$ {rel['total']:.2f}

Por pagamento:
"""
            for pg, valor in rel["pagamentos"].items():
                resumo += f"- {pg}: R$ {valor:.2f}\n"

            resumo += f"\n==============================\n💰 Total em dinheiro físico: R$ {total_final:.2f}\n=============================="
            imprimir_texto(resumo, titulo="Fechamento THE RUA")
        st.success("Caixa fechado com sucesso!")
        st.rerun()

# ---------------------------------------------------
# Venda no Balcão (recolhido)
# ---------------------------------------------------
st.markdown("---")
with st.expander("🧾 Registrar Pedido de Balcão"):
    with st.form("novo_pedido_form"):
        nome = st.text_input("Nome do Cliente")
        telefone = st.text_input("Telefone")
        tipo_pedido = st.selectbox("Tipo", ["Consumo no local", "Retirada", "Entrega"])
        endereco = st.text_area("Endereço (somente para entrega)")
        pagamento = st.selectbox("Forma de pagamento", ["Dinheiro", "Pix", "Cartão"])
        total = st.number_input("Valor Total (R$)", min_value=0.0, step=1.0)
        obs = st.text_area("Observações")
        enviar = st.form_submit_button("💾 Registrar Pedido")

        if enviar:
            if not nome or total <= 0:
                st.error("Preencha nome e valor total.")
            else:
                novo = {
                    "id": str(int(datetime.now().timestamp())),
                    "codigo_rastreio": str(int(datetime.now().timestamp()))[-4:],
                    "nome": nome,
                    "telefone": telefone,
                    "tipo_pedido": tipo_pedido,
                    "endereco": endereco,
                    "pagamento": pagamento,
                    "troco_para": "",
                    "observacoes": obs,
                    "produtos": [],
                    "status": "Em preparo",
                    "data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "total": total
                }
                pedidos = carregar_pedidos()
                pedidos.append(novo)
                salvar_pedidos(pedidos)
                st.success("✅ Pedido de balcão registrado!")
                st.rerun()

# ---------------------------------------------------
# Lista de pedidos
# ---------------------------------------------------
pedidos = carregar_pedidos()
if not pedidos:
    st.info("Nenhum pedido registrado ainda.")
    st.stop()

pedidos = sorted(pedidos, key=lambda x: x.get("data", ""), reverse=True)
filtro = st.selectbox("Filtrar por status", ["Todos", "Aguardando aceite", "Em preparo", "Pronto", "Em rota de entrega", "Entregue"])
if filtro != "Todos":
    pedidos = [p for p in pedidos if p.get("status") == filtro]

for pedido in pedidos:
    st.markdown("---")
    col1, col2, col3 = st.columns([3, 2, 2])

    with col1:
        st.subheader(f"📦 Pedido #{pedido['codigo_rastreio']}")
        st.write(f"👤 {pedido['nome']} — {pedido['telefone']}")
        st.write(f"🕒 {pedido['data']}")
        st.write(f"💵 Total: R$ {pedido['total']:.2f}")
        st.write(f"📦 Tipo: {pedido['tipo_pedido']}")
        if pedido["tipo_pedido"] == "Entrega":
            st.caption(f"📍 {pedido['endereco']}")
        st.caption(f"🧾 Pagamento: {pedido['pagamento']}")
        if pedido.get("comprovante") and os.path.exists(pedido["comprovante"]):
            with open(pedido["comprovante"], "rb") as f:
                st.download_button("📎 Ver comprovante", data=f, file_name=os.path.basename(pedido["comprovante"]))
        if pedido.get("observacoes"):
            st.caption(f"✏️ {pedido['observacoes']}")

    with col2:
        st.markdown("#### Itens")
        for item in pedido.get("produtos", []):
            st.markdown(f"- {item['quantidade']}x {item['nome']} (R$ {item['preco']:.2f})")

    with col3:
        st.markdown("#### Ações")
        st.write(f"🟢 **{pedido['status']}**")

        if pedido["status"] == "Aguardando aceite":
            if st.button("✅ Aceitar", key=f"aceitar_{pedido['id']}"):
                atualizar_status(pedido["id"], "Em preparo")
                st.success("Pedido aceito.")
                st.rerun()

        if st.button("✏️ Editar", key=f"edit_{pedido['id']}"):
            with st.form(f"edit_form_{pedido['id']}"):
                nome = st.text_input("Nome", pedido["nome"])
                telefone = st.text_input("Telefone", pedido["telefone"])
                endereco = st.text_input("Endereço", pedido["endereco"])
                obs = st.text_area("Observações", pedido.get("observacoes", ""))
                if st.form_submit_button("Salvar"):
                    pedido["nome"], pedido["telefone"], pedido["endereco"], pedido["observacoes"] = nome, telefone, endereco, obs
                    salvar_pedidos(pedidos)
                    st.success("Atualizado!")
                    st.rerun()

        if st.button("🗑️ Excluir", key=f"del_{pedido['id']}"):
            excluir_pedido(pedido["id"])
            st.warning("Pedido excluído.")
            st.rerun()

        if st.button("🖨️ Imprimir", key=f"print_{pedido['id']}"):
            imprimir_pedido(pedido)


