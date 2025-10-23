import json
import os
import time
import serial
from datetime import datetime

PEDIDOS_FILE = "../pedidos.json"  # arquivo sincronizado com o sistema
IMPRESSORAS_FILE = "impressoras.json"

def carregar_json(path, default=[]):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except:
            return default

def imprimir_serial(com_port, texto):
    try:
        with serial.Serial(com_port, 9600, timeout=2) as s:
            s.write(texto.encode('utf-8'))
            s.write(b"\n\n\n")
        print(f"[{datetime.now()}] ✅ Impresso com sucesso via {com_port}")
    except Exception as e:
        print(f"❌ Erro na impressora {com_port}: {e}")

def main():
    ja_impresso = set()
    impressoras = carregar_json(IMPRESSORAS_FILE)

    if not impressoras:
        print("⚠️ Nenhuma impressora configurada. Crie um arquivo 'impressoras.json'")
        print('Exemplo: [{"nome": "POS-80", "porta": "COM5"}]')
        return

    porta = impressoras[0].get("porta", "COM5")

    print(f"🖨️ Cliente POS-80 iniciado (porta {porta})")
    print("Aguardando novos pedidos...")

    while True:
        pedidos = carregar_json(PEDIDOS_FILE)
        for p in pedidos:
            pid = p.get("id")
            if pid in ja_impresso:
                continue

            texto = f"""
======= THE RUA =======
Data: {datetime.now().strftime("%d/%m/%Y %H:%M")}
Código: {p['codigo_rastreio']}
Cliente: {p['nome']}
Tipo: {p['tipo_pedido']}
-----------------------
"""
            for item in p.get("produtos", []):
                texto += f"- {item['quantidade']}x {item['nome']}  R$ {item['preco']*item['quantidade']:.2f}\n"
            texto += f"\nTotal: R$ {p['total']:.2f}\nPagamento: {p['pagamento']}\n"
            texto += "=======================\n\n\n"

            imprimir_serial(porta, texto)
            ja_impresso.add(pid)

        time.sleep(5)

if __name__ == "__main__":
    main()
