from src.utils.db_functions import retrieveProductData
from src.utils.load_credentials import loadCredentials
from kafka import KafkaProducer, KafkaConsumer
from datetime import datetime
import streamlit as st
import random
import json
import time

# load credentials (.env)
credentials=loadCredentials()

# --- Configuração do Kafka Producer ---
try:
    producer = KafkaProducer(
        bootstrap_servers=credentials["bootstrap_servers"],
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )
    kafka_available = True
except Exception as e:
    kafka_available = False
    st.warning(f"⚠️ Não foi possível conectar ao Kafka como Producer. Erro: {e}")

# --- Configuração da Página ---
st.set_page_config(page_title="[TMB] Checkout - PoC", page_icon="💳", layout="wide")

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
    }
    .stButton>button:hover {
        background-color: #008a6e;
        border: 1px solid #008a6e;
        color: white;
    }
    .stButton>button:focus {
        box-shadow: none !important;
    }
</style>
""", unsafe_allow_html=True)


# --- Carregamento dos Dados dos Produtos ---
@st.cache_data
def format_product_data():
    print("\nBuscando produtos na base...")
    data_from_db = retrieveProductData()
    products_list = []
    num_products = len(data_from_db['nome_produto'])
    for i in range(num_products):
        product = {k: v[i] for k, v in data_from_db.items()}
        products_list.append(product)
    return products_list
products = format_product_data()

# --- Funções Auxiliares ---
def get_bot_response(user_message):
    """Simula uma resposta automática do contato."""
    responses = ["Ok, entendido!", "Recebido. Vou verificar."]
    return random.choice(responses)

# --- Inicialização do Estado da Sessão ---
if "screen" not in st.session_state:
    st.session_state.screen = "products"
    st.session_state.selected_product = None
    st.session_state.messages = []

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
                st.markdown(f"**Carga Horária:** {product['carga_horaria_produto']}")
                
                if st.button("Comprar", key=f"buy_{i}", use_container_width=True):
                    if kafka_available:
                        # Evento de clique
                        click_event = {
                            "action":"click-button",
                            "type":"buy-product",
                            "created_at":datetime.now().isoformat(),
                        }
                        producer.send('streamlit_events', click_event)
                        
                        # Informações do produto
                        product_info_message = {
                            "main_attributes":product,
                            "product_offer":{
                                 "offered_value":product["valor_produto"],
                                 "discount": 0,
                                 "attempts": 0,
                              },
                            "created_at":datetime.now().isoformat(),
                            "updated_at":"",
                        }
                        producer.send('product_info', product_info_message)
                        producer.flush()
                        
                    st.session_state.selected_product = product
                    st.session_state.screen = "chat" 
                    st.rerun()

# --- TELA 2: CHAT DE CHECKOUT ---
elif st.session_state.screen == "chat":

    # **CORREÇÃO APLICADA AQUI**
    # Primeiro, verificamos se a sessão de chat já foi inicializada (se já temos mensagens).
    # Se a lista de mensagens estiver vazia, significa que precisamos conectar ao Kafka.
    if not st.session_state.messages:
        # Ao rodar o spinner em uma tela "vazia", evitamos a sobreposição.
        with st.spinner("Conectando com nosso assistente virtual..."):
            try:
                consumer = KafkaConsumer(
                    'agent_msg',
                    bootstrap_servers=credentials["bootstrap_servers"],
                    auto_offset_reset='earliest',
                    consumer_timeout_ms=15000, # 15 segundos
                    value_deserializer=lambda v: json.loads(v.decode('utf-8'))
                )
                
                first_message = next(consumer, None)
                consumer.close()

                if first_message:
                    agent_response = first_message.value
                    st.session_state.messages = [
                        {
                            "role": "Jarvis", 
                            "content": agent_response['message'], 
                            "avatar": "🤖"
                        }
                    ]
                else:
                    # Se der timeout, adicionamos uma mensagem de erro ao chat
                    st.session_state.messages = [
                        {
                            "role": "Jarvis",
                            "content": "😥 Desculpe, não consegui me conectar. Por favor, tente voltar e selecionar o produto novamente.",
                            "avatar": "🤖"
                        }
                    ]
            except Exception as e:
                # Se der um erro de conexão, adicionamos uma mensagem de erro ao chat
                st.session_state.messages = [
                    {
                        "role": "Jarvis",
                        "content": f"😥 Ocorreu um erro de conexão: {e}. Por favor, tente voltar e selecionar o produto novamente.",
                        "avatar": "🤖"
                    }
                ]
        st.rerun() # Recarrega a página para agora exibir a interface de chat com a primeira mensagem

    # Se a lista de mensagens NÃO estiver vazia, desenhamos a interface completa do chat.
    else:
        st.header(f"Checkout - {st.session_state.selected_product['nome_produto']}")

        # Botão para voltar
        if st.button("⬅️ Voltar para a vitrine"):
            st.session_state.screen = "products"
            st.session_state.messages = []
            st.session_state.selected_product = None
            st.rerun()

        message_container = st.container()
        with message_container:
            for message in st.session_state.messages:
                with st.chat_message(message["role"], avatar=message.get("avatar")):
                    st.markdown(message["content"])

        if prompt := st.chat_input("Digite sua mensagem..."):
            st.session_state.messages.append({"role": "Você", "content": prompt, "avatar": "👤"})
            with st.chat_message("Você", avatar="👤"):
                st.markdown(prompt)

            with st.chat_message("Jarvis", avatar="🤖"):
                with st.spinner("Digitando..."):
                    time.sleep(random.uniform(0.5, 1.5))
                    bot_response = get_bot_response(prompt)
                    st.markdown(bot_response)
            
            st.session_state.messages.append({"role": "Jarvis", "content": bot_response, "avatar": "🤖"})
            st.rerun()