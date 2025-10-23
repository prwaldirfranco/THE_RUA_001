import streamlit as st
import json
import os
import platform
import urllib.parse
from datetime import datetime
from streamlit_javascript import st_javascript

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
IMPRESSORAS_FILE = "impressoras.json"

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
# Impressão automática (Windows ou Android/RawBT)
# ---------------------------------------------------
def _detect_android_env():
    android_keys = ("ANDROID_BOOTLOGO", "ANDROID_ROOT", "ANDROID_DATA", "ANDROID_ARGUMENT")
    return any(k in os.environ for k in android_keys)

def imprimir_texto(texto, titulo="PEDIDO THE RUA"):
    sistema = platform.system()
    impressora_config = None

    # Carrega impressora configurada
    if os.path.exists(IMPRESSORAS_FILE):
        try:
            with open(IMPRESSORAS_FILE, "r", encoding="utf-8") as f:
                impressoras = json.load(f)
                if impressoras:
                    impressora_config = impressoras[0].get("endereco") or impressoras[0].get("nome")
        except Exception:
            impressora_config = None

    # Caso Windows
    if sistema == "Windows":
        try:
            import win32print, win32ui
            printer_name = impressora_config or win32print.GetDefaultPrinter()
            hDC = win32ui.CreateDC()
            hDC.CreatePrinterDC(printer_name)
            hDC.StartDoc(titulo)
            hDC.StartPage()
            font = win32ui.CreateFont({"name": "Arial", "height": -18, "weight": 400})
            hDC.SelectObject(font)
            y = 20
            for linha in texto.splitlines():
                hDC.TextOut(20, y, linha.strip())
                y += 35
            hDC.EndPage()
            hDC.EndDoc()
            hDC.DeleteDC()
            st.success(f"🖨️ Impresso com sucesso na impressora: {printer_name}")
        except Exception as e:
            st.error(f"❌ Erro ao imprimir (Windows): {e}")

    else:
        # Detecta Android via navegador (JavaScript)
        user_agent = st_javascript("navigator.userAgent.toLowerCase();")
        is_android = (
            _detect_android_env()
            or (user_agent and "android" in user_agent)
        )

        if is_android:
            try:
                texto_para_imprimir = texto.strip().replace("\n\n", "\n")
                texto_codificado = urllib.parse.quote(texto_para_imprimir)
                url_intent = f"intent://print/{texto_codificado}#Intent;scheme=rawbt;package=ru.a402d.rawbtprinter;end"
                url_rawbt = f"rawbt://print?text={texto_codificado}"

                st.info("📱 Impressora Bluetooth RawBT detectada — pronta para imprimir.")
                st.markdown(
                    f"""
                    <div style='margin-top:10px;text-align:center;'>
                        <a href="{url_intent}" target="_blank">
                            <button style="background:#007bff;color:white;padding:12px 20px;border:none;border-radius:10px;font-size:17px;">
                                🖨️ Imprimir via RawBT
                            </button>
                        </a>
                        &nbsp;
                        <a href="{url_rawbt}" target="_blank">
                            <button style="background:#28a745;color:white;padding:12px 20px;border:none;border-radius:10px;font-size:17px;">
                                🔁 Alternativo (RawBT Link)
                            </button>
                        </a>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                st.caption("✅ Toque em **Imprimir via RawBT** para enviar diretamente ao app. Se não funcionar, use o botão alternativo ou baixe o arquivo abaixo.")
                st.download_button(
                    "⬇️ Baixar arquivo (.txt) — abrir no RawBT",
                    data=texto_para_imprimir,
                    file_name="pedido_the_rua.txt",
                    mime="text/plain",
                )
            except Exception as e:
                st.error(f"Erro ao preparar impressão Android: {e}")
        else:
            st.warning("⚠️ Impressão local desativada. Use um tablet Android com o app RawBT.")

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
        return {"aberto": False, "valor_inicial": 0.0}
    with open(CAIXA_FILE, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
            if not isinstance(data, dict):
                data = {"aberto": False, "valor_inicial": 0.0}
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
# Interface
# ---------------------------------------------------
st.set_page_config(page_title="Caixa - THE RUA", layout="wide")
st.title("💵 Painel do Caixa")
st.caption("Gerencie pedidos, vendas no balcão e o fechamento do caixa.")

# --- Teste de impressão ---
st.sidebar.subheader("🖨️ Impressora Local")
if st.sidebar.button("🧾 Testar Impressão"):
    imprimir_texto("""
====== TESTE DE IMPRESSÃO ======
Impressora configurada corretamente!
==============================
""", titulo="Teste de Impressão")

# --- Caixa ---
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
        st.success("Caixa fechado com sucesso! ✅")
        st.rerun()

# ---------------------------------------------------
# Venda no Balcão
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
        if st.form_submit_button("💾 Registrar Pedido"):
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
                imprimir_pedido(novo)
                st.success("✅ Pedido de balcão registrado e impresso!")
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

        if st.button("🖨️ Imprimir", key=f"print_{pedido['id']}"):
            imprimir_pedido(pedido)

        if st.button("🗑️ Excluir", key=f"del_{pedido['id']}"):
            excluir_pedido(pedido)
            st.warning("Pedido excluído.")
            st.rerun()
