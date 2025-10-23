import streamlit as st
import json
import os
import platform
import urllib.parse
from datetime import datetime

# Tenta importar o JS, mas não quebra se não existir
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

    # Carrega impressora configurada (se houver)
    if os.path.exists(IMPRESSORAS_FILE):
        try:
            with open(IMPRESSORAS_FILE, "r", encoding="utf-8") as f:
                impressoras = json.load(f)
                if impressoras:
                    impressora_config = impressoras[0].get("endereco") or impressoras[0].get("nome")
        except Exception:
            impressora_config = None

    # --- Impressão direta no Windows ---
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

    # --- Impressão via RawBT (Android) ---
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
        st.info("📱 Dispositivo Android detectado — pronto para imprimir via RawBT.")
        st.markdown(
            f"""
            <div style='text-align:center;margin-top:20px;'>
                <a href="{url_intent}" target="_blank">
                    <button style="background:#007bff;color:white;padding:16px 26px;
                                   border:none;border-radius:12px;font-size:18px;">
                        🖨️ Imprimir via RawBT
                    </button>
                </a>
                <br><br>
                <a href="{url_rawbt}" target="_blank">
                    <button style="background:#28a745;color:white;padding:14px 22px;
                                   border:none;border-radius:10px;font-size:16px;">
                        🔁 Alternativo (RawBT Link)
                    </button>
                </a>
            </div>
            """,
            unsafe_allow_html=True
        )
        st.download_button(
            "⬇️ Baixar arquivo (.txt) — abrir manualmente no RawBT",
            data=texto_para_imprimir,
            file_name="pedido_the_rua.txt",
            mime="text/plain",
        )
    else:
        st.warning("⚠️ Impressão local desativada. Use um tablet Android com o app RawBT instalado.")


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
        texto += f"- {item.get('quantidade',0)}x {item.get('nome','')} R$ {item.get('preco',0)*item.get('quantidade',0):.2f}\n"

    texto += f"\nTotal: R$ {pedido.get('total',0):.2f}\nPagamento: {pedido.get('pagamento','')}\n"
    if pedido.get("troco_para"):
        texto += f"Troco para: {pedido['troco_para']}\n"
    if pedido.get("observacoes"):
        texto += f"Obs: {pedido['observacoes']}\n"
    texto += "\n==============================\n"

    imprimir_texto(texto, titulo="Pedido THE RUA")


# ---------------------------------------------------
# Interface do Caixa
# ---------------------------------------------------
st.set_page_config(page_title="Caixa - THE RUA", layout="wide")
st.title("💵 Painel do Caixa")
st.caption("Gerencie pedidos, veja comprovantes PIX e imprima recibos diretamente.")

pedidos = carregar_pedidos()
if not pedidos:
    st.info("Nenhum pedido registrado ainda.")
    st.stop()

pedidos = sorted(pedidos, key=lambda x: x.get("data", ""), reverse=True)
filtro = st.selectbox("Filtrar por status", ["Todos", "Aguardando aceite", "Em preparo", "Pronto", "Entregue"])
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

        # 💳 Mostrar e permitir baixar comprovante PIX (enviado pelo cliente)
        if pedido.get("pagamento") == "Pix":
            st.markdown("💳 **Pagamento via PIX**")
            if pedido.get("comprovante_pix"):
                st.image(pedido["comprovante_pix"], caption="📄 Comprovante PIX", use_container_width=True)
                st.download_button(
                    label="⬇️ Baixar Comprovante PIX",
                    data=open(pedido["comprovante_pix"], "rb").read(),
                    file_name=f"comprovante_{pedido['codigo_rastreio']}.jpg",
                    mime="image/jpeg",
                )
            else:
                st.info("Aguardando envio do comprovante PIX pelo cliente...")

    with col2:
        st.markdown("#### Itens")
        for item in pedido.get("produtos", []):
            st.markdown(f"- {item.get('quantidade',0)}x {item.get('nome','')} (R$ {item.get('preco',0):.2f})")

    with col3:
        st.markdown("#### Ações")
        st.write(f"🟢 **{pedido['status']}**")

        if st.button("🖨️ Imprimir Pedido", key=f"print_{pedido['id']}"):
            imprimir_pedido(pedido)

        if st.button("🗑️ Excluir", key=f"del_{pedido['id']}"):
            excluir_pedido(pedido['id'])
            st.warning("Pedido excluído.")
            st.rerun()
