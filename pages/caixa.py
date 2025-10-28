import streamlit as st
import json
import os
import platform
import urllib.parse
from datetime import datetime

# -------------------------------
# Tentativa segura de importar st_javascript
# -------------------------------
try:
    from streamlit_javascript import st_javascript
except Exception:
    st_javascript = None

# -------------------------------
# Segurança — exige login e verifica cargo
# -------------------------------
if "logado" not in st.session_state or not st.session_state["logado"]:
    st.warning("⚠️ Acesso restrito. Faça login para continuar.")
    st.stop()

cargo = st.session_state.get("cargo", "")

pagina_atual = os.path.basename(__file__)
if (
    (pagina_atual == "caixa.py" and cargo not in ["caixa", "admin"]) or
    (pagina_atual == "cozinha.py" and cargo not in ["cozinha", "admin"]) or
    (pagina_atual == "entregador.py" and cargo not in ["entregador", "admin"]) or
    (pagina_atual == "cadastro_produtos.py" and cargo not in ["admin"]) or
    (pagina_atual == "relatorios.py" and cargo not in ["admin", "caixa"])
):
    st.error("🚫 Você não tem permissão para acessar esta página.")
    st.stop()

# -------------------------------
# Caminhos e arquivos
# -------------------------------
DATA_FILE = "pedidos.json"
CAIXA_FILE = "caixa.json"
IMPRESSORAS_FILE = "impressoras.json"
RELATORIOS_DIR = "relatorios"
os.makedirs(RELATORIOS_DIR, exist_ok=True)

# -------------------------------
# Funções utilitárias
# -------------------------------
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

# -------------------------------
# Painel de Impressão Persistente (corrigido)
# -------------------------------
def _render_painel_impressao_persistente():
    """Painel RawBT com keys exclusivas — evita erro StreamlitDuplicateElementId"""
    if not st.session_state.get("mostrar_painel_impressao"):
        return

    texto_para_imprimir = st.session_state.get("ultimo_texto_impressao", "")
    if not texto_para_imprimir:
        st.session_state["mostrar_painel_impressao"] = False
        return

    texto_codificado = urllib.parse.quote(texto_para_imprimir)
    url_intent = f"intent://print/{texto_codificado}#Intent;scheme=rawbt;package=ru.a402d.rawbtprinter;end"
    url_rawbt = f"rawbt://print?text={texto_codificado}"
    ts = int(datetime.now().timestamp())
    file_name = f"pedido_the_rua_{ts}.txt"

    with st.container():
        st.markdown("---")
        st.markdown("### 🖨️ Painel de Impressão (RawBT / Download)")

        st.markdown(
            f"""
            <div style='margin-top:12px;text-align:center;'>
                <a href="{url_intent}" 
                   style="background:#007bff;color:white;padding:12px 20px;
                   border:none;border-radius:8px;font-size:16px;margin-right:8px;text-decoration:none;">
                    🖨️ Imprimir via RawBT
                </a>
                <a href="{url_rawbt}" 
                   style="background:#28a745;color:white;padding:12px 20px;
                   border:none;border-radius:8px;font-size:16px;margin-right:8px;text-decoration:none;">
                    🔁 Alternativo (RawBT Link)
                </a>
                <button id="fechar_painel_btn" 
                    style="background:#6c757d;color:white;padding:12px 20px;
                    border:none;border-radius:8px;font-size:16px;margin-right:8px;">
                    ✖️ Fechar painel
                </button>
                <a href="data:text/plain;charset=utf-8,{urllib.parse.quote(texto_para_imprimir)}" 
                   download="{file_name}" 
                   style="background:#ffc107;color:black;padding:12px 20px;border:none;border-radius:8px;font-size:16px;text-decoration:none;">
                    ⬇️ Baixar arquivo (.txt)
                </a>
            </div>
            <script>
                document.getElementById('fechar_painel_btn').onclick = function() {{
                    try {{
                        localStorage.setItem("the_rua_fechar_painel_impressao", "1");
                    }} catch(e){{ }}
                    setTimeout(()=>location.reload(), 200);
                }};
            </script>
            """,
            unsafe_allow_html=True,
        )

    try:
        if st_javascript:
            fechar_flag = st_javascript("localStorage.getItem('the_rua_fechar_painel_impressao');")
            if fechar_flag:
                st_javascript("localStorage.removeItem('the_rua_fechar_painel_impressao');")
                st.session_state["mostrar_painel_impressao"] = False
                st.rerun()
    except Exception:
        pass

    if st.button("✖️ Fechar painel de impressão", key=f"close_{ts}"):
        st.session_state["mostrar_painel_impressao"] = False
        st.rerun()

if "mostrar_painel_impressao" not in st.session_state:
    st.session_state["mostrar_painel_impressao"] = False
if "ultimo_texto_impressao" not in st.session_state:
    st.session_state["ultimo_texto_impressao"] = ""

# -------------------------------
# Impressão
# -------------------------------
def imprimir_texto(texto, titulo="PEDIDO THE RUA", direct=False):
    sistema = platform.system()
    impressora_config = None

    if os.path.exists(IMPRESSORAS_FILE):
        try:
            with open(IMPRESSORAS_FILE, "r", encoding="utf-8") as f:
                impressoras = json.load(f)
                if impressoras:
                    impressora_config = impressoras[0].get("endereco") or impressoras[0].get("nome")
        except Exception:
            impressora_config = None

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
            st.success(f"🖨️ Impresso na impressora: {printer_name}")
            return
        except Exception as e:
            st.error(f"❌ Erro ao imprimir: {e}")
            return

    texto_para_imprimir = texto.strip().replace("\r\n", "\n").replace("\n\n", "\n")

    if direct:
        texto_codificado = urllib.parse.quote(texto_para_imprimir)
        url_intent = f"intent://print/{texto_codificado}#Intent;scheme=rawbt;package=ru.a402d.rawbtprinter;end"
        if st_javascript:
            st_javascript(f"window.open('{url_intent}', '_blank');")
            st.success("🖨️ Tentando imprimir diretamente via RawBT...")
        else:
            st.markdown(f'<a href="{url_intent}" target="_blank">🖨️ Clique para imprimir diretamente via RawBT</a>', unsafe_allow_html=True)
    else:
        st.session_state["ultimo_texto_impressao"] = texto_para_imprimir
        st.session_state["mostrar_painel_impressao"] = True
        st.rerun()

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
        for r in item.get("removidos", []):
            texto += f"    - sem {r}\n"
        for ex in item.get("extras", []):
            texto += f"    + {ex.get('qtd',1)}x {ex.get('nome')} (+R$ {float(ex.get('preco',0)):.2f})\n"

    texto += f"\nTotal: R$ {pedido.get('total', 0):.2f}\nPagamento: {pedido.get('pagamento', '')}\n"
    if pedido.get("troco_para"):
        texto += f"Troco para: {pedido['troco_para']}\n"
    if pedido.get("observacoes"):
        texto += f"Obs: {pedido['observacoes']}\n"
    texto += "\n==============================\n"
    imprimir_texto(texto, titulo="Pedido THE RUA")

# -------------------------------
# Caixa e Relatórios
# -------------------------------
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
    imprimir_texto(rel, titulo="Fechamento THE RUA", direct=True)
    return rel, nome  # Retorne nome em vez de caminho para file_name

# -------------------------------
# Interface Principal
# -------------------------------
st.set_page_config(page_title="Caixa - THE RUA", layout="wide")
st.title("💵 Painel do Caixa")
st.caption("Gerencie pedidos, comprovantes e impressão via RawBT ou Windows.")

if st.button("🔄 Atualizar informações"):
    st.rerun()

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
        rel, file_name = fechar_caixa()
        st.success("Caixa fechado com sucesso ✅")
        st.text_area("📋 Relatório do Dia", rel, height=300)
        st.markdown(
            f'<a href="data:text/plain;charset=utf-8,{urllib.parse.quote(rel)}" download="{file_name}">⬇️ Baixar Relatório do Dia</a>',
            unsafe_allow_html=True
        )
        st.stop()

# Impressão de teste
st.sidebar.subheader("🖨️ Impressora Local")
if st.sidebar.button("🧾 Testar Impressão"):
    testar_texto = "====== TESTE DE IMPRESSÃO ======\n✅ Impressora configurada corretamente.\n=============================="
    imprimir_texto(testar_texto, titulo="Teste de Impressão")

# Renderizar o painel de impressão aqui, acima da lista de pedidos, para maior visibilidade
_render_painel_impressao_persistente()

# Lista de pedidos
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
            st.markdown(f"- {item.get('quantidade', 0)}x {item.get('nome', '')} (R$ {item.get('preco', 0):.2f})")

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