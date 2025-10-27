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
# Painel persistente de impressão (mostra quando existe texto a imprimir)
# ---------------------------------------------------
def _render_painel_impressao_persistente():
    """
    Se st.session_state['mostrar_painel_impressao'] for True, exibe o painel com
    botões RawBT / fallback / download / fechar painel.
    """
    if not st.session_state.get("mostrar_painel_impressao"):
        return

    texto_para_imprimir = st.session_state.get("ultimo_texto_impressao", "")
    if not texto_para_imprimir:
        # nada a mostrar
        st.session_state["mostrar_painel_impressao"] = False
        return

    texto_codificado = urllib.parse.quote(texto_para_imprimir)
    url_intent = f"intent://print/{texto_codificado}#Intent;scheme=rawbt;package=ru.a402d.rawbtprinter;end"
    url_rawbt = f"rawbt://print?text={texto_codificado}"

    cont = st.container()
    with cont:
        st.markdown("---")
        st.markdown("### 🖨️ Painel de Impressão (RawBT / Download)")
        st.markdown(
            f"""
            <div style='margin-top:12px;text-align:center;'>
                <!-- Intent: abre RawBT; usamos window.open em JS para abrir nova aba -->
                <button onclick="window.open('{url_intent}', '_blank')" style="background:#007bff;color:white;padding:12px 20px;border:none;border-radius:8px;font-size:16px;margin-right:8px;">
                    🖨️ Imprimir via RawBT
                </button>

                <button onclick="window.open('{url_rawbt}', '_blank')" style="background:#28a745;color:white;padding:12px 20px;border:none;border-radius:8px;font-size:16px;margin-right:8px;">
                    🔁 Alternativo (RawBT Link)
                </button>

                <button id="fechar_painel_btn" style="background:#6c757d;color:white;padding:12px 20px;border:none;border-radius:8px;font-size:16px;">
                    ✖️ Fechar painel
                </button>
            </div>
            <script>
            // O botão de fechar comunica ao Streamlit via alteração de localStorage
            // e o usuário deve então clicar no botão 'Fechar painel' para remover a UI.
            document.getElementById('fechar_painel_btn').onclick = function() {{
                try {{
                    localStorage.setItem("the_rua_fechar_painel_impressao", "1");
                }} catch(e){{ }}
                // Tenta forçar um pequeno reload (não obrigatório)
                setTimeout(()=>location.reload(), 200);
            }};
            </script>
            """,
            unsafe_allow_html=True,
        )

        # Download em .txt
        st.download_button(
            label="⬇️ Baixar arquivo (.txt) — abrir manualmente no RawBT",
            data=texto_para_imprimir,
            file_name="pedido_the_rua.txt",
            mime="text/plain",
        )

        st.info("Toque em 'Imprimir via RawBT' — se o RawBT abrir, confirme 'Print' no app. Quando terminar, clique em 'Fechar painel'.")

    # Detecta se o botão JS foi acionado definindo localStorage (navegador)
    # Em seguida limpa o painel.
    try:
        # st_javascript pode retornar a flag se estiver disponível
        if st_javascript:
            fechar_flag = st_javascript("localStorage.getItem('the_rua_fechar_painel_impressao');")
            if fechar_flag:
                # limpa localStorage via JS e fecha painel
                st_javascript("localStorage.removeItem('the_rua_fechar_painel_impressao');")
                st.session_state["mostrar_painel_impressao"] = False
                st.experimental_rerun()
        else:
            # fallback: se o usuário clicar no botão "Fechar painel" dentro do Streamlit (adicionado abaixo)
            pass
    except Exception:
        pass

    # Botão de fechar painel (fallback, via Python)
    if st.button("✖️ Fechar painel de impressão (se ainda visível)"):
        st.session_state["mostrar_painel_impressao"] = False
        st.experimental_rerun()

# Render painel de impressão (se ativo) sempre no topo da página
if "mostrar_painel_impressao" not in st.session_state:
    st.session_state["mostrar_painel_impressao"] = False
if "ultimo_texto_impressao" not in st.session_state:
    st.session_state["ultimo_texto_impressao"] = ""
_render_painel_impressao_persistente()

# ---------------------------------------------------
# Impressão automática (Windows ou Android/RawBT)
# ---------------------------------------------------
def _detect_android_env():
    android_keys = ("ANDROID_BOOTLOGO", "ANDROID_ROOT", "ANDROID_DATA", "ANDROID_ARGUMENT")
    return any(k in os.environ for k in android_keys)

def imprimir_texto(texto, titulo="PEDIDO THE RUA"):
    """
    - Mantém impressão direta no Windows (win32).
    - Para web/Android: prepara texto, guarda em session_state e mostra painel persistente de impressão.
    """
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

    # Para web/Android: prepara texto e mostra painel fixo de impressão (RawBT)
    texto_para_imprimir = texto.strip().replace("\r\n", "\n").replace("\n\n", "\n")

    # grava em sessão para painel persistente
    st.session_state["ultimo_texto_impressao"] = texto_para_imprimir
    st.session_state["mostrar_painel_impressao"] = True

    # renderiza painel imediatamente
    _render_painel_impressao_persistente()

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
        nome = item.get("nome", "")
        qtd = item.get("quantidade", 1)
        preco = float(item.get("preco", 0))
        subtotal = preco * qtd
        texto += f"- {qtd}x {nome} R$ {subtotal:.2f}\n"

        # Ingredientes removidos
        removidos = item.get("removidos", [])
        if removidos:
            for r in removidos:
                texto += f"    - sem {r}\n"

        # Extras adicionados
        extras = item.get("extras", [])
        if extras:
            for ex in extras:
                texto += f"    + {ex.get('qtd',1)}x {ex.get('nome')} (+R$ {float(ex.get('preco',0)):.2f})\n"

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
                    for f_name in os.listdir(uploads_dir):
                        if str(pedido["id"]) in f_name:
                            comprovante = os.path.join(uploads_dir, f_name)
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
                else:
                    # Se for URL remoto (http...), exibe botão de download link
                    if isinstance(comprovante, str) and comprovante.startswith("http"):
                        st.image(comprovante, caption="📄 Comprovante PIX (online)", use_container_width=True)
                        st.markdown(
                            f"""
                            <a href="{comprovante}" download target="_blank">
                                <button style="background:#007bff;color:white;padding:10px 18px;
                                              border:none;border-radius:8px;font-size:16px;margin-top:8px;">
                                    ⬇️ Baixar Comprovante
                                </button>
                            </a>
                            """,
                            unsafe_allow_html=True
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
