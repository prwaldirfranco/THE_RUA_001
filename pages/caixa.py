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
# Impressão direta via RAWBT
# -------------------------------
def imprimir_rawbt(texto):
    """Gera botão de impressão RawBT dentro de cada pedido."""
    texto = texto.strip().replace("\r\n", "\n").replace("\n\n", "\n")
    texto_codificado = urllib.parse.quote(texto)
    url_intent = f"intent://print/{texto_codificado}#Intent;scheme=rawbt;package=ru.a402d.rawbtprinter;end"
    url_rawbt = f"rawbt://print?text={texto_codificado}"

    st.markdown(
        f"""
        <div style='margin-top:6px;margin-bottom:6px;'>
            <button onclick="(function(){{
                const ua = navigator.userAgent.toLowerCase();
                let url = '{url_rawbt}';
                if(ua.includes('android')) url = '{url_intent}';
                try {{
                    const w = window.open(url, '_blank');
                    if(!w) alert('⚠️ Ative pop-ups para o RawBT funcionar corretamente.');
                }} catch(e) {{
                    alert('❌ Erro ao abrir RawBT: '+e.message);
                }}
            }})()"
            style="background:#007bff;color:white;padding:10px 18px;border:none;border-radius:8px;
                   font-size:16px;cursor:pointer;">
                🖨️ Imprimir via RawBT
            </button>
        </div>
        """,
        unsafe_allow_html=True
    )

# -------------------------------
# Impressão de texto (Windows + RawBT)
# -------------------------------
def imprimir_texto(texto, titulo="PEDIDO THE RUA", rawbt=False):
    sistema = platform.system()
    if sistema == "Windows" and not rawbt:
        try:
            import win32print, win32ui
            printer_name = win32print.GetDefaultPrinter()
            hDC = win32ui.CreateDC()
            hDC.CreatePrinterDC(printer_name)
            hDC.StartDoc(titulo)
            hDC.StartPage()
            font = win32ui.CreateFont({"name": "Arial", "height": -18})
            hDC.SelectObject(font)
            y = 20
            for linha in texto.splitlines():
                hDC.TextOut(20, y, linha.strip())
                y += 35
            hDC.EndPage()
            hDC.EndDoc()
            hDC.DeleteDC()
            st.success(f"🖨️ Impresso em: {printer_name}")
        except Exception as e:
            st.error(f"❌ Erro ao imprimir: {e}")
    else:
        imprimir_rawbt(texto)

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

    imprimir_texto(texto, rawbt=True)

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

    # 🔹 Impressão automática do fechamento
    imprimir_texto(rel, titulo="Fechamento THE RUA", rawbt=True)
    return rel, nome

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
        st.success("Caixa fechado e impresso com sucesso ✅")
        st.text_area("📋 Relatório do Dia", rel, height=300)
        st.download_button("⬇️ Baixar Relatório", rel, file_name=file_name)
        st.stop()

# Lista de pedidos
pedidos = carregar_pedidos()
if not pedidos:
    st.info("Nenhum pedido registrado.")
    st.stop()

pedidos = sorted(pedidos, key=lambda x: x.get("data", ""), reverse=True)
for pedido in pedidos:
    st.markdown("---")
    st.subheader(f"📦 Pedido #{pedido['codigo_rastreio']}")
    st.write(f"👤 {pedido['nome']} — {pedido['telefone']}")
    st.write(f"💵 Total: R$ {pedido['total']:.2f}")
    st.write(f"📦 Tipo: {pedido['tipo_pedido']}")
    if pedido["tipo_pedido"] == "Entrega":
        st.caption(f"📍 {pedido['endereco']}")
    st.caption(f"🧾 Pagamento: {pedido['pagamento']}")
    if pedido.get("observacoes"):
        st.caption(f"✏️ {pedido['observacoes']}")

    # 🖨️ Botão de imprimir dentro do pedido
    imprimir_pedido(pedido)

    if pedido["status"] == "Aguardando aceite":
        if st.button("✅ Aceitar Pedido", key=f"aceitar_{pedido['id']}"):
            atualizar_status(pedido["id"], "Em preparo")
            st.success("Pedido aceito.")
            st.rerun()

    if st.button("🗑️ Excluir Pedido", key=f"del_{pedido['id']}"):
        excluir_pedido(pedido["id"])
        st.warning("Pedido excluído.")
        st.rerun()
