import streamlit as st
import json
import os
import platform
import mimetypes
import urllib.parse
from datetime import datetime

# Tenta importar streamlit_javascript, sem travar se não existir
try:
    from streamlit_javascript import st_javascript
except Exception:
    st_javascript = None

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
RELATORIOS_DIR = "relatorios"

os.makedirs(RELATORIOS_DIR, exist_ok=True)

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
# Impressão automática (Windows / Android RawBT)
# ---------------------------------------------------
def _detect_android_env():
    android_keys = ("ANDROID_BOOTLOGO", "ANDROID_ROOT", "ANDROID_DATA", "ANDROID_ARGUMENT")
    return any(k in os.environ for k in android_keys)

def imprimir_texto(texto, titulo="PEDIDO THE RUA"):
    sistema = platform.system()
    impressora_config = None

    # Carrega impressora configurada (se existir)
    if os.path.exists(IMPRESSORAS_FILE):
        try:
            with open(IMPRESSORAS_FILE, "r", encoding="utf-8") as f:
                impressoras = json.load(f)
                if impressoras:
                    impressora_config = impressoras[0].get("endereco") or impressoras[0].get("nome")
        except Exception:
            impressora_config = None

    # Impressão local (Windows)
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
            return
        except Exception as e:
            st.error(f"❌ Erro ao imprimir (Windows): {e}")
            return

    # Impressão Android (RawBT)
    try:
        user_agent = st_javascript("navigator.userAgent.toLowerCase();") if st_javascript else ""
    except Exception:
        user_agent = ""
    is_android = "android" in str(user_agent).lower() or _detect_android_env()

    texto_para_imprimir = texto.strip().replace("\r\n", "\n").replace("\n\n", "\n")
    texto_codificado = urllib.parse.quote(texto_para_imprimir)
    url_intent = f"intent://print/{texto_codificado}#Intent;scheme=rawbt;package=ru.a402d.rawbtprinter;end"
    url_rawbt = f"rawbt://print?text={texto_codificado}"

    if is_android:
        st.markdown(
            f"""
            <div style='margin-top:15px;text-align:center;'>
                <a href="{url_intent}" target="_blank">
                    <button style="background:#007bff;color:white;padding:14px 24px;
                                   border:none;border-radius:10px;font-size:18px;">
                        🖨️ Imprimir via RawBT
                    </button>
                </a>
                &nbsp;
                <a href="{url_rawbt}" target="_blank">
                    <button style="background:#28a745;color:white;padding:14px 24px;
                                   border:none;border-radius:10px;font-size:18px;">
                        🔁 Alternativo (RawBT Link)
                    </button>
                </a>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.warning("⚠️ Impressão local desativada. Use um tablet Android com o app RawBT.")

# ---------------------------------------------------
# Impressão e Relatórios
# ---------------------------------------------------
def testar_impressao():
    texto_teste = """
====== TESTE DE IMPRESSÃO ======
✅ Impressora configurada corretamente.
==============================
"""
    imprimir_texto(texto_teste, titulo="Teste de Impressão")

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
        texto += f"- {item.get('quantidade', 0)}x {item.get('nome', '')} R$ {item.get('preco', 0) * item.get('quantidade', 0):.2f}\n"

    texto += f"\nTotal: R$ {pedido.get('total', 0):.2f}\nPagamento: {pedido.get('pagamento', '')}\n"
    if pedido.get("observacoes"):
        texto += f"Obs: {pedido['observacoes']}\n"
    texto += "\n==============================\n"
    imprimir_texto(texto, titulo="Pedido THE RUA")

# ---------------------------------------------------
# Controle de Caixa
# ---------------------------------------------------
def carregar_caixa():
    if not os.path.exists(CAIXA_FILE):
        return {"aberto": False, "valor_inicial": 0.0}
    with open(CAIXA_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
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
    pedidos = carregar_pedidos()
    rel = gerar_relatorio_caixa(pedidos, caixa)

    # Salva relatório em arquivo
    nome_arquivo = f"relatorio_{datetime.now().strftime('%d-%m-%Y')}.txt"
    caminho_arquivo = os.path.join(RELATORIOS_DIR, nome_arquivo)
    with open(caminho_arquivo, "w", encoding="utf-8") as f:
        f.write(rel)

    # Imprime e fecha
    imprimir_texto(rel, titulo="Fechamento THE RUA")

    caixa["aberto"] = False
    caixa["fechado_em"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    salvar_caixa(caixa)
    return rel, caminho_arquivo

def gerar_relatorio_caixa(pedidos=None, caixa=None):
    pedidos = pedidos or carregar_pedidos()
    caixa = caixa or carregar_caixa()
    total_geral = sum(p.get("total", 0) for p in pedidos)
    por_pagamento = {}
    for p in pedidos:
        pg = p.get("pagamento", "Outros")
        por_pagamento[pg] = por_pagamento.get(pg, 0) + p.get("total", 0)
    rel = f"""
====== FECHAMENTO THE RUA ======
Aberto em: {caixa.get('aberto_em')}
Fechado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Valor inicial: R$ {caixa.get('valor_inicial', 0):.2f}
Total pedidos: {len(pedidos)}
Total geral: R$ {total_geral:.2f}

Por pagamento:
"""
    for pg, valor in por_pagamento.items():
        rel += f"- {pg}: R$ {valor:.2f}\n"
    dinheiro = por_pagamento.get("Dinheiro", 0)
    total_final = caixa.get("valor_inicial", 0) + dinheiro
    rel += f"""
==============================
💰 Total em dinheiro físico: R$ {total_final:.2f}
==============================
"""
    return rel

# ---------------------------------------------------
# Interface
# ---------------------------------------------------
st.set_page_config(page_title="Caixa - THE RUA", layout="wide")
st.title("💵 Painel do Caixa")
st.caption("Gerencie pedidos, comprovantes e impressão via RawBT ou Windows.")

# --- Teste de impressão ---
st.sidebar.subheader("🖨️ Impressora Local")
if st.sidebar.button("🧾 Testar Impressão"):
    testar_impressao()

# --- Controle de Caixa ---
st.sidebar.header("🧾 Controle de Caixa")
caixa = carregar_caixa()

if not caixa.get("aberto", False):
    with st.sidebar.form("abrir_caixa_form"):
        valor_inicial = st.number_input("Valor inicial (R$)", min_value=0.0, step=10.0, value=0.0)
        if st.form_submit_button("🔓 Abrir Caixa"):
            abrir_caixa(valor_inicial)
            st.success("Caixa aberto com sucesso!")
            st.rerun()
    st.warning("⚠️ O caixa está fechado. Abra o caixa para registrar pedidos.")
    st.stop()
else:
    st.sidebar.success(f"✅ Caixa aberto em: {caixa['aberto_em']}")
    st.sidebar.info(f"💵 Valor inicial: R$ {caixa['valor_inicial']:.2f}")
    if st.sidebar.button("🔒 Fechar Caixa"):
        rel, caminho = fechar_caixa()
        st.success("Caixa fechado com sucesso! ✅")
        st.text_area("📋 Relatório do Dia", rel, height=300)
        with open(caminho, "rb") as f:
            st.download_button("⬇️ Baixar Relatório do Dia", f, file_name=os.path.basename(caminho))
        st.stop()

# ---------------------------------------------------
# A partir daqui: só funciona com o caixa aberto
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
                    "observacoes": obs,
                    "status": "Em preparo",
                    "data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "total": total
                }
                pedidos = carregar_pedidos()
                pedidos.append(novo)
                salvar_pedidos(pedidos)
                imprimir_pedido(novo)
                st.success("✅ Pedido registrado e impresso!")
                st.rerun()

# ---------------------------------------------------
# Lista de Pedidos
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
            excluir_pedido(pedido["id"])
            st.warning("Pedido excluído.")
            st.rerun()
