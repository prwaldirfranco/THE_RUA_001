import os, json, time
from datetime import datetime
import win32print, win32ui

PEDIDOS_FILE = "pedidos.json"  # o mesmo arquivo sincronizado (ex: via OneDrive ou API)
IMPRESSORAS_FILE = "impressoras.json"

def carregar_json(path, default=[]):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except:
            return default

def imprimir_texto(texto, nome_impressora=None):
    try:
        printer_name = nome_impressora or win32print.GetDefaultPrinter()
        hDC = win32ui.CreateDC()
        hDC.CreatePrinterDC(printer_name)
        hDC.StartDoc("Pedido Automático POS-80")
        hDC.StartPage()

        font = win32ui.CreateFont({
            "name": "Arial",
            "height": 22 * -1,
            "weight": 400,
        })
        hDC.SelectObject(font)

        y = 40
        for linha in texto.splitlines():
            hDC.TextOut(40, y, linha)
            y += 60

        hDC.EndPage()
        hDC.EndDoc()
        hDC.DeleteDC()
        print(f"[{datetime.now()}] Impresso com sucesso.")
    except Exception as e:
        print(f"Erro ao imprimir: {e}")

def main():
    ja_impresso = set()
    while True:
        pedidos = carregar_json(PEDIDOS_FILE)
        impressoras = carregar_json(IMPRESSORAS_FILE)
        if not pedidos:
            time.sleep(5)
            continue

        for pedido in pedidos:
            pid = pedido.get("id")
            if pid in ja_impresso:
                continue

            texto = f"""
====== POS-80 ======
Data: {datetime.now().strftime("%d/%m/%Y %H:%M")}
Código: {pedido['codigo_rastreio']}
Cliente: {pedido['nome']}
Tipo: {pedido['tipo_pedido']}
"""
            for item in pedido.get("produtos", []):
                texto += f"- {item['quantidade']}x {item['nome']} R$ {item['preco']*item['quantidade']:.2f}\n"
            texto += f"\nTotal: R$ {pedido['total']:.2f}\n"
            texto += "======================"

            # imprime na primeira impressora da lista
            nome_imp = impressoras[0]["endereco"] if impressoras else None
            imprimir_texto(texto, nome_imp)
            ja_impresso.add(pid)
        time.sleep(10)

if __name__ == "__main__":
    print("🖨️ POS-80 Client iniciado. Aguardando pedidos...")
    main()
