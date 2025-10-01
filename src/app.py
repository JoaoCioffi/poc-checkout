import streamlit as st
import pandas as pd
from datetime import datetime
import time
import pycep_correios
import random

# --- Importações do Projeto ---
from src.utils.db_functions import retrieveProductData, retrieveCustomerData, registerCustomerData
from src.utils.helpers import validateDocument, extractUserData, extractSellerAgentText, extractProductOffer
from src.agents.callback import greetingsAgent, requestUserPersonalInfoAgent, gatherUserDataAgent, sellerAgent

# --- Lógica de Negócio ---
def calculate_discount(attempts: int) -> int:
    """
    Calcula o percentual de desconto com base no número de tentativas.
    """
    if attempts > 6:
        return 10
    if 4 <= attempts <= 6:
        return 7
    if attempts == 0:
        return 0
    if attempts == 1:
        return 3
    if attempts >= 2: # Tentativas 2 e 3
        return 5
    return 0

# --- [MODIFICADO] Lógica de Simulação do Modelo de Risco ---
def model_predict(income: str, age: str, product_value: float) -> bool:
    """
    Simula um modelo de risco de inadimplência com base em regras de negócio.
    Esta é uma função genérica para a PoC.

    Args:
        income (str): A faixa de renda selecionada.
        age (str): A faixa etária selecionada.
        product_value (float): O valor do produto sendo comprado.

    Returns:
        bool: True se o perfil for aprovado, False caso contrário.
    """
    # Mapeamento da renda para um valor numérico máximo para comparação
    income_map = {
        "de 0 a R$1.000,00": 1000.0,
        "de R$1.000,01 a R$3.000,00": 3000.0,
        "de R$3.000,01 a R$6.000,00": 6000.0,
        "de R$6.000,01 a R$10.000,00": 10000.0,
        "Acima de R$10.000,00": float('inf') # Representa um valor muito alto
    }
    max_income = income_map.get(income, 0)

    # Regra 1: Valor do produto é muito alto para a renda declarada
    # Recusa se o valor do produto for maior que 60% da renda máxima da faixa.
    if product_value > (max_income * 0.6) and max_income != float('inf'):
        st.warning(f"Motivo da recusa: O valor do produto (R$ {product_value:.2f}) é considerado alto para a faixa de renda selecionada.")
        return False

    # Regra 2: Renda alta e idade baixa (possível inconsistência)
    # Recusa se a pessoa tiver entre 18-25 anos e declarar renda acima de 10k.
    if age == "de 18 a 25 anos" and income == "Acima de R$10.000,00":
        st.warning("Motivo da recusa: Perfil com potencial inconsistência entre faixa etária e renda declarada.")
        return False
        
    # Se passar por todas as regras, o perfil é aprovado.
    return True

# --- Configuração da Página ---
st.set_page_config(
    page_title="TMB | Venda de Infoprodutos",
    page_icon="💳",
    layout="wide"
)

# --- Injeção de CSS ---
st.markdown("""
<style>
    [data-testid="stChatInput"] div[data-baseweb="base-input"]:focus-within {
        border-color: #00A884;
        box-shadow: 0 0 0 1px #00A884;
    }
    .stButton>button {
        background-color: #00A884;
        color: white;
        border: 1px solid #00A884;
        transition: background-color 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #008a6e;
        border: 1px solid #008a6e;
    }
</style>
""", unsafe_allow_html=True)

# --- Carregamento Otimizado dos Dados dos Produtos ---
@st.cache_data
def load_and_format_products():
    print("Buscando produtos na base...")
    data_from_db = retrieveProductData()
    products_list = [dict(zip(data_from_db, t)) for t in zip(*data_from_db.values())]
    return products_list

products = load_and_format_products()

# --- Inicialização do Estado da Sessão ---
if "screen" not in st.session_state:
    st.session_state.screen = "products"
    st.session_state.selected_product = None
    st.session_state.messages = []
    st.session_state.conversation_stage = "start"
    st.session_state.customer_data = {}
    st.session_state.product_offer = {}


# --- TELA 1: VITRINE DE PRODUTOS ---
if st.session_state.screen == "products":
    st.header("Escolha um produto para comprar")
    st.write("---")
    cols = st.columns(len(products))
    for i, product in enumerate(products):
        with cols[i]:
            with st.container(border=True):
                st.subheader(product["nome_produto"])
                st.info(f"{product['tipo_produto']} - {product['modalidade_produto']}")
                st.metric(label="Valor", value=f"R$ {product['valor_produto']:.2f}")
                st.markdown(f"**Carga Horária:** {product['carga_horaria_produto']} Horas")
                st.markdown("")
                if st.button("Comprar", key=f"buy_{i}", use_container_width=True):
                    st.session_state.selected_product = product
                    st.session_state.screen = "risk_analysis"
                    # Reseta o estado do chat ao escolher um novo produto
                    st.session_state.messages = []
                    st.session_state.conversation_stage = "start"
                    st.session_state.customer_data = {}
                    st.session_state.product_offer = {}
                    st.rerun()

# --- [MODIFICADO] TELA INTERMEDIÁRIA: ANÁLISE DE PERFIL DE RISCO ---
elif st.session_state.screen == "risk_analysis":
    # Título alterado
    st.header("Análise de Perfil para Checkout")
    st.write(f"Você selecionou o produto: **{st.session_state.selected_product['nome_produto']}**")
    st.info("Para prosseguir, precisamos de algumas informações para simular uma análise de risco.")

    with st.form(key="risk_profile_form"):
        # --- Campos do Formulário (somente renda e idade) ---
        income = st.selectbox(
            "Qual sua faixa de renda mensal?",
            ("de 0 a R$1.000,00", "de R$1.000,01 a R$3.000,00", "de R$3.000,01 a R$6.000,00", "de R$6.000,01 a R$10.000,00", "Acima de R$10.000,00")
        )
        age = st.selectbox(
            "Qual sua faixa etária?",
            ("de 18 a 25 anos", "de 25 a 30 anos", "de 30 a 40 anos", "de 40 a 60 anos", "Acima de 60 anos")
        )
        
        submitted = st.form_submit_button("Analisar Perfil")

    if submitted:
        # Pega o valor do produto do estado da sessão
        product_value = st.session_state.selected_product['valor_produto']
        
        # Chama a função de simulação (sem sexo e gênero)
        with st.spinner("Analisando seu perfil..."):
            time.sleep(2) # Simula o tempo de processamento
            is_approved = model_predict(income, age, product_value)

        if is_approved:
            st.success("Perfil selecionado ✅, seguindo para checkout!")
            time.sleep(2) # Pausa para o usuário ler a mensagem
            st.session_state.screen = "chat" # Redireciona para o chat
            st.rerun()
        else:
            st.error("Perfil recusado. Infelizmente não podemos seguir para o checkout.")
            if st.button("Voltar para a vitrine"):
                st.session_state.screen = "products"
                st.rerun()


# --- TELA 2: CHAT DE CHECKOUT ---
elif st.session_state.screen == "chat":
    st.header(f"Checkout - {st.session_state.selected_product['nome_produto']}")

    if st.button("⬅️ Voltar para a vitrine"):
        st.session_state.screen = "products"
        st.rerun()

    # Inicializa o chat se for a primeira vez
    if st.session_state.conversation_stage == "start":
        # Estrutura da oferta
        st.session_state.product_offer = {
            "main_attributes": st.session_state.selected_product,
            "last_product_offer": {
                "offered_value": st.session_state.selected_product["valor_produto"],
                "discount": 0,
                "attempts": 0
            }
        }
        # 1. greetingsAgent
        with st.spinner("Conectando com nosso assistente..."):
            initial_message = greetingsAgent(productAttributes=st.session_state.selected_product)
        st.session_state.messages.append({"role": "assistant", "content": initial_message})
        st.session_state.conversation_stage = "awaiting_cpf"
        st.rerun()

    # Exibe o histórico de mensagens
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Container para o botão de finalizar compra
    button_container = st.container()
    with button_container:
        if st.session_state.conversation_stage == "in_purchase_flow":
            if st.button("✅ Finalizar compra"):
                st.session_state.messages.append({"role": "assistant", "content": "🎉 Parabéns pela sua compra! O processo foi finalizado com sucesso."})
                st.session_state.conversation_stage = "purchase_complete"
                st.rerun()

    # Lógica de interação principal
    if prompt := st.chat_input("Digite sua resposta...", disabled=(st.session_state.conversation_stage == "purchase_complete")):
        st.session_state.messages.append({"role": "user", "content": prompt})

        # --- FLUXO DE CONVERSA BASEADO NO ESTÁGIO ---
        # 2. Usuário insere o CPF
        if st.session_state.conversation_stage == "awaiting_cpf":
            with st.chat_message("assistant"):
                with st.spinner("Analisando..."):
                    is_valid = validateDocument(prompt)
                    if not is_valid:
                        st.session_state.messages.append({"role": "assistant", "content": "CPF inválido. Por favor, verifique os números e tente novamente."})
                    else:
                        customer = retrieveCustomerData(document=prompt)
                        # Cliente já existe
                        if customer:
                            st.session_state.customer_data = customer
                            st.session_state.conversation_stage = "in_purchase_flow"
                            offer = sellerAgent(
                                productAttributes=st.session_state.selected_product,
                                userName=customer["nome"],
                                lastProductOffer=st.session_state.product_offer["last_product_offer"],
                                acceptanceTime=0.0
                            )
                            agent_text = extractSellerAgentText(output=offer)
                            st.session_state.messages.append({"role": "assistant", "content": agent_text})
                        # Novo cliente
                        else:
                            st.session_state.customer_data['documento'] = prompt
                            st.session_state.conversation_stage = "awaiting_personal_info"
                            response = requestUserPersonalInfoAgent(productAttributes=st.session_state.selected_product)
                            st.session_state.messages.append({"role": "assistant", "content": response})

        # 4. Usuário insere dados pessoais
        elif st.session_state.conversation_stage == "awaiting_personal_info":
            with st.chat_message("assistant"):
                with st.spinner("Processando seus dados..."):
                    agent_response = gatherUserDataAgent(productAttributes=st.session_state.selected_product, userMsg=prompt)
                    new_user_data = extractUserData(agentResponse=agent_response)
                    try:
                        address_data = pycep_correios.get_address_from_cep(new_user_data["cep"])
                        st.session_state.customer_data.update(new_user_data)
                        new_customer_params = {
                            "documento": st.session_state.customer_data["documento"],
                            "nome": new_user_data["nome_completo"], "cep": new_user_data["cep"],
                            "email": new_user_data["email"], "nascimento": new_user_data["data_de_nascimento"],
                            "endereco_estado": address_data["uf"], "endereco_cidade": address_data["cidade"],
                            "endereco_bairro": address_data["bairro"], "endereco_logouro": address_data["logradouro"]
                        }
                        registerCustomerData(new_customer_params)
                        st.session_state.customer_data['nome'] = new_user_data['nome_completo']
                        st.session_state.messages.append({"role": "assistant", "content": "Ótimo, cadastro realizado com sucesso! Vamos à sua oferta exclusiva."})
                        st.session_state.conversation_stage = "in_purchase_flow"
                        offer = sellerAgent(
                            productAttributes=st.session_state.selected_product,
                            userName=st.session_state.customer_data["nome"],
                            lastProductOffer=st.session_state.product_offer["last_product_offer"],
                            acceptanceTime=0.0
                        )
                        agent_text = extractSellerAgentText(output=offer)
                        st.session_state.messages.append({"role": "assistant", "content": agent_text})
                    except Exception as e:
                        st.session_state.messages.append({"role": "assistant", "content": f"Houve um erro ao processar seus dados (especialmente o CEP). Por favor, verifique e envie novamente. Erro: {e}"})

        # 6. handlePurchaseFlow (negociação)
        elif st.session_state.conversation_stage == "in_purchase_flow":
            user_decision = prompt.lower()
            with st.chat_message("assistant"):
                with st.spinner("..."):
                    if any(word in user_decision for word in ['s', 'sim', 'aceito', 'comprar', 'quero']):
                        st.session_state.messages.append({"role": "assistant", "content": "🎉 Parabéns pela sua compra! O processo foi finalizado com sucesso."})
                        st.session_state.conversation_stage = "purchase_complete"
                    else:
                        st.session_state.product_offer["last_product_offer"]["attempts"] += 1
                        attempts = st.session_state.product_offer["last_product_offer"]["attempts"]
                        new_discount = calculate_discount(attempts)
                        st.session_state.product_offer["last_product_offer"]["discount"] = new_discount
                        original_value = st.session_state.selected_product["valor_produto"]
                        new_value = original_value * (1 - (new_discount / 100))
                        st.session_state.product_offer["last_product_offer"]["offered_value"] = new_value
                        offer = sellerAgent(
                            productAttributes=st.session_state.selected_product,
                            userName=st.session_state.customer_data["nome"],
                            lastProductOffer=st.session_state.product_offer["last_product_offer"],
                            acceptanceTime=0.0
                        )
                        agent_text = extractSellerAgentText(output=offer)
                        st.session_state.messages.append({"role": "assistant", "content": agent_text})
        
        st.rerun()