import streamlit as st
import json
import os
import platform
import mimetypes
import urllib.parse
from datetime import datetime

# try import st_javascript but don't crash if not available
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
def carregar_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except:
            return default

def salvar_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def carregar_pedidos():
    return carregar_json(DATA_FILE, [])

def salvar_pedidos(pedidos):
    salvar_json(DATA_FILE, pedidos)

def carregar_caixa():
    return carregar_json(CAIXA_FILE, {"aberto": False, "valor_inicial": 0.0})

def salvar_caixa(caixa):
    salvar_json(CAIXA_FILE, caixa)

def excluir_pedido(pedido_id):
    pedidos = [p for p in carregar_pedidos() if str(p.get("id")) != str(pedido_id)]
    salvar_pedidos(pedidos)

def atualizar_status(pedido_id, novo_status):
    pedidos = carregar_pedidos()
    for p in pedidos:
        if str(p.get("id")) == str(pedido_id):
            p["status"] = novo_status
    salvar_pedidos(pedidos)

# ---------------------------------------------------
# Impressão automática (Windows ou Android/RawBT)
# ---------------------------------------------------
# ---------------------------------------------------
# Impressão automática (Windows ou Android/RawBT)
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

    # Caso Windows — impressão direta
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

    # --- Força exibição RawBT no navegador ---
    texto_para_imprimir = texto.strip().replace("\r\n", "\n").replace("\n\n", "\n")
    texto_codificado = urllib.parse.quote(texto_para_imprimir)
    url_intent = f"intent://print/{texto_codificado}#Intent;scheme=rawbt;package=ru.a402d.rawbtprinter;end"
    url_rawbt = f"rawbt://print?text={texto_codificado}"

    st.markdown("### 🖨️ Impressão via RawBT (Android)")
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

    st.download_button(
        label="⬇️ Baixar arquivo (.txt) — abrir manualmente no RawBT",
        data=texto_para_imprimir,
        file_name="pedido_the_rua.txt",
        mime="text/plain",
    )

# ---------------------------------------------------
# Impressão de Pedido
# ---------------------------------------------------
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
    if pedido.get("troco_para"):
        texto += f"Troco para: {pedido['troco_para']}\n"
    if pedido.get("observacoes"):
        texto += f"Obs: {pedido['observacoes']}\n"
    texto += "\n==============================\n"
    imprimir_texto(texto, titulo="Pedido THE RUA")

# ---------------------------------------------------
# Funções de Caixa e Relatórios
# ---------------------------------------------------
def abrir_caixa(valor_inicial):
    caixa = {
        "aberto": True,
        "valor_inicial": valor_inicial,
        "aberto_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "fechado_em": None,
    }
    salvar_caixa(caixa)

def gerar_relatorio_caixa():
    pedidos = carregar_pedidos()
    caixa = carregar_caixa()
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

def fechar_caixa():
    caixa = carregar_caixa()
    caixa["aberto"] = False
    caixa["fechado_em"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    salvar_caixa(caixa)
    rel = gerar_relatorio_caixa()
    nome = f"relatorio_{datetime.now().strftime('%Y-%m-%d_%H-%M')}.txt"
    caminho = os.path.join(RELATORIOS_DIR, nome)
    with open(caminho, "w", encoding="utf-8") as f:
        f.write(rel)
    imprimir_texto(rel, titulo="Fechamento THE RUA")
    return rel, caminho

# ---------------------------------------------------
# Interface
# ---------------------------------------------------
st.set_page_config(page_title="Caixa - THE RUA", layout="wide")
st.title("💵 Painel do Caixa")
st.caption("Gerencie pedidos, comprovantes e impressão via RawBT ou Windows.")

# Controle de caixa
st.sidebar.header("🧾 Controle de Caixa")
caixa = carregar_caixa()

if not caixa.get("aberto", False):
    with st.sidebar.form("abrir_caixa_form"):
        valor_inicial = st.number_input("Valor inicial (R$)", min_value=0.0, step=10.0)
        if st.form_submit_button("🔓 Abrir Caixa"):
            abrir_caixa(valor_inicial)
            st.success("Caixa aberto com sucesso!")
            st.rerun()
    st.warning("⚠️ O caixa está fechado. Abra o caixa para usar o sistema.")
    st.stop()
else:
    st.sidebar.success(f"✅ Caixa aberto em: {caixa['aberto_em']}")
    st.sidebar.info(f"💵 Valor inicial: R$ {caixa['valor_inicial']:.2f}")

    if st.sidebar.button("🔒 Fechar Caixa"):
        rel, caminho = fechar_caixa()
        st.success("Caixa fechado com sucesso ✅")
        st.text_area("📋 Relatório do Dia", rel, height=300)
        with open(caminho, "rb") as f:
            st.download_button("⬇️ Baixar Relatório do Dia", f, file_name=os.path.basename(caminho))
        st.stop()

# --- Teste de impressão ---
st.sidebar.subheader("🖨️ Impressora Local")
if st.sidebar.button("🧾 Testar Impressão"):
    testar_texto = "====== TESTE DE IMPRESSÃO ======\n✅ Impressora configurada corretamente.\n=============================="
    imprimir_texto(testar_texto, titulo="Teste de Impressão")

# --- Carrega pedidos ---
pedidos = carregar_pedidos()
if not pedidos:
    st.info("Nenhum pedido registrado ainda.")
    st.stop()

pedidos = sorted(pedidos, key=lambda x: x.get("data", ""), reverse=True)
filtro = st.selectbox("Filtrar por status", ["Todos", "Aguardando aceite", "Em preparo", "Pronto", "Em rota de entrega", "Entregue"])
if filtro != "Todos":
    pedidos = [p for p in pedidos if p.get("status") == filtro]

for i, pedido in enumerate(pedidos):
    st.markdown("---")
    col1, col2, col3 = st.columns([3, 2, 2])

    # --- Coluna 1 ---
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

        # Mostra comprovante PIX (se houver)
        if pedido.get("pagamento") == "Pix":
            st.markdown("💳 **Pagamento via PIX**")
            comprovante = (
                pedido.get("comprovante_pix")
                or pedido.get("comprovante")
                or pedido.get("arquivo")
                or pedido.get("anexo")
                or pedido.get("upload_pix")
            )
            if not comprovante:
                uploads_dir = "uploads"
                if os.path.exists(uploads_dir):
                    for f in os.listdir(uploads_dir):
                        if str(pedido["id"]) in f:
                            comprovante = os.path.join(uploads_dir, f)
                            break
            if comprovante:
                ext = os.path.splitext(comprovante)[1].lower()
                mime_type = mimetypes.guess_type(comprovante)[0] or "application/octet-stream"
                if os.path.exists(comprovante):
                    if ext in [".jpg", ".jpeg", ".png"]:
                        st.image(comprovante, caption="📄 Comprovante PIX", use_container_width=True)
                    with open(comprovante, "rb") as f:
                        st.download_button(
                            label=f"⬇️ Baixar Comprovante ({os.path.basename(comprovante)})",
                            data=f,
                            file_name=os.path.basename(comprovante),
                            mime=mime_type,
                            key=f"baixar_{pedido['id']}"
                        )

    # --- Coluna 2 ---
    with col2:
        st.markdown("#### Itens")
        for item in pedido.get("produtos", []):
            st.markdown(f"- {item.get('quantidade', 0)}x {item.get('nome', '')} (R$ {item.get('preco', 0):.2f})")

    # --- Coluna 3 ---
    with col3:
        st.markdown("#### Ações")
        st.write(f"🟢 **{pedido['status']}**")

        if pedido["status"] == "Aguardando aceite":
            if st.button("✅ Aceitar Pedido", key=f"aceitar_{pedido['id']}"):
                atualizar_status(pedido["id"], "Em preparo")
                st.success("Pedido aceito.")
                st.rerun()

        if st.button("🖨️ Imprimir Pedido", key=f"print_{pedido['id']}"):
            imprimir_pedido(pedido)

        if st.button("🗑️ Excluir Pedido", key=f"del_{pedido['id']}"):
            excluir_pedido(pedido['id'])
            st.warning("Pedido excluído.")
            st.rerun()
