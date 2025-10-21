import streamlit as st

if "logado" not in st.session_state or not st.session_state["logado"]:
    st.warning("⚠️ Acesso restrito. Faça login para continuar.")
    st.stop()

st.title("Novo Pedido")

produtos = [
    {"id": 1, "nome": "Hambúrguer", "preco": 15.00},
    {"id": 2, "nome": "Batata Frita", "preco": 8.00},
    {"id": 3, "nome": "Refrigerante", "preco": 5.00},
]

pedido = []
quantidades = {}

for produto in produtos:
    qtd = st.number_input(f"Quantidade de {produto['nome']}", min_value=0, value=0)
    quantidades[produto['id']] = qtd
    if qtd > 0:
        pedido.append((produto['nome'], qtd, produto['preco']))

if st.button("Registrar Pedido"):
    if not pedido:
        st.error("Adicione pelo menos um produto.")
    else:
        total = sum(q * preco for _, q, preco in pedido)
        st.success(f"Pedido registrado. Total: R$ {total:.2f}")
        # Função para salvar pedido no banco/JSON, gerar código de rastreio...

        # Exibir detalhes do pedido
        for item in pedido:
            st.write(f"{item[0]} x {item[1]} - R$ {item[1]*item[2]:.2f}")
