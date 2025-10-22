import os
import json
import time
import platform
from datetime import datetime

# Tenta importar bibliotecas do Windows
if platform.system() == "Windows":
    try:
        import win32print
        import win32ui
    except ImportError:
        win32print = None
        win32ui = None
else:
    win32print = None
    win32ui = None

PEDIDOS_FILE = "pedidos.json"       # Deve ser o mesmo arquivo do servidor (sincronizado)
IMPRESSORAS_FILE = "impressoras.json"

# ---------------------------------------------------
# Funções auxiliares
# ---------------------------------------------------
def carregar_json(path, default=[]):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except Exception:
            return default

# ---------------------------------------------------
# Impressão local automática
# ---------------------------------------------------
def imprimir_texto(texto, nome_impressora=None):
    sistema = platform.system()

    if sistema != "Windows" or win32print is None:
        print("⚠️ Impressão local não disponível neste sistema.")
        return

    try:
        printer_name = nome_impressora or win32print.GetDefaultPrinter()

        hDC = win32ui.CreateDC()
        hDC.CreatePrinterDC(printer_name)
        hDC.StartDoc("Pedido Automático - THE RUA")
        hDC.StartPage()

        # Fonte compacta — ideal para POS-80
        font = win32ui.CreateFont({
            "name": "Arial",
            "height": 20 * -1,   # ~18pt
            "weight": 400,
        })
        hDC.SelectObject(font)

        y = 30
        for linha in texto.splitlines():
            hDC.TextOut(30, y, linha.strip())
            y += 45  # espaçamento compacto para economizar papel

        hDC.EndPage()
        hDC.EndDoc()
        hDC.DeleteDC()

        print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Pedido impresso com sucesso ({printer_name})")

    except Exception as e:
        print(f"❌ Erro ao imprimir: {e}")

# ---------------------------------------------------
# Loop principal — monitora novos pedidos
# ---------------------------------------------------
def main():
    print("🖨️ Serviço de Impressão THE RUA iniciado...")
    print("Aguardando novos pedidos para impressão automática...\n")

    ja_impresso = set()

    while True:
        try:
            pedidos = carregar_json(PEDIDOS_FILE)
            impressoras = carregar_json(IMPRESSORAS_FILE)

            if not pedidos:
                time.sleep(5)
                continue

            for pedido in pedidos:
                pid = pedido.get("id")
                if not pid or pid in ja_impresso:
                    continue

                # Monta o texto para impressão
                texto = f"""
====== THE RUA HAMBURGUERIA ======
Data: {datetime.now().strftime("%d/%m/%Y %H:%M")}
Código: {pedido.get('codigo_rastreio', '----')}
Cliente: {pedido.get('nome', '---')}
Tipo: {pedido.get('tipo_pedido', '---')}
"""

                if pedido.get("tipo_pedido") == "Entrega":
                    texto += f"Endereço: {pedido.get('endereco','')}\n"

                texto += "\nItens:\n"
                for item in pedido.get("produtos", []):
                    nome = item.get("nome", "")
                    qtd = item.get("quantidade", 1)
                    preco = float(item.get("preco", 0))
                    texto += f"- {qtd}x {nome} R$ {qtd * preco:.2f}\n"

                texto += f"\nTotal: R$ {pedido.get('total',0):.2f}\n"
                texto += f"Pagamento: {pedido.get('pagamento','')}\n"

                if pedido.get("observacoes"):
                    texto += f"Obs: {pedido['observacoes']}\n"

                texto += "==============================\n"

                # Seleciona impressora
                nome_imp = None
                if impressoras:
                    nome_imp = impressoras[0].get("endereco") or impressoras[0].get("nome")

                imprimir_texto(texto, nome_imp)
                ja_impresso.add(pid)

            time.sleep(8)

        except KeyboardInterrupt:
            print("\n🛑 Serviço encerrado manualmente.")
            break
        except Exception as e:
            print(f"⚠️ Erro no loop principal: {e}")
            time.sleep(10)

# ---------------------------------------------------
# Execução
# ---------------------------------------------------
if __name__ == "__main__":
    main()
