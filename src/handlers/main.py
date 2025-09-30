from src.agents.callback import greetingsAgent, requestUserPersonalInfoAgent, gatherUserDataAgent, sellerAgent
from src.utils.helpers import validateDocument, extractUserData, extractSellerAgentText, extractProductOffer
from src.utils.db_functions import retrieveCustomerData, registerCustomerData
from src.utils.load_credentials import loadCredentials
from kafka import KafkaConsumer, KafkaProducer
from colorama import Fore, Back, Style, init
from datetime import datetime
import pycep_correios
import logging
import json

# initialize colorama for terminal output
init(autoreset=True)

# load credentials (.env)
credentials = loadCredentials()

# --- Configuração dos Clientes Kafka ---
logging.getLogger("kafka").setLevel(logging.ERROR) # configuração para suprimir logs de INFO do Kafka: os níveis são DEBUG,INFO,WARNING,ERROR,CRITICAL -> setLevel(logging.ERROR) instrui o logger a ignorar DEBUG, INFO e WARNING (ou seja, todos os anteriores a ele)
consumer = KafkaConsumer(
    'product_info',
    bootstrap_servers=credentials["bootstrap_servers"],
    auto_offset_reset='earliest',
    group_id='checkout-processor-group',
    value_deserializer=lambda v: json.loads(v.decode('utf-8'))
)

# Adicionamos um Producer para enviar as mensagens do agente
producer = KafkaProducer(
    bootstrap_servers=credentials["bootstrap_servers"],
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# --- Loop Principal do Processador de Checkout ---
print(f"{Fore.CYAN}🚀 Backend iniciado. Aguardando por seleção de produtos no tópico 'product_info'...{Style.RESET_ALL}\n")

for message in consumer:
    # 1. Mensagem recebida do Kafka
    full_product_info = message.value
    desiredProduct = full_product_info['main_attributes']

    print(f"{Fore.GREEN}🛒 Novo produto selecionado! Iniciando processo de checkout...{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Dados do produto:{Style.RESET_ALL} {json.dumps(desiredProduct, indent=2)}\n")
    
    # 2. LLM gera a saudação
    greetingsAgentResponse = greetingsAgent(productAttributes=desiredProduct)
    print(greetingsAgentResponse) # Mantém o log no backend

    # 2.1. Envia a saudação para o tópico do agente para o Streamlit consumir
    agent_message = {
        "agent": "greetings",
        "message": greetingsAgentResponse,
        "created_at": datetime.now().isoformat(),
    }
    producer.send('agent_msg', agent_message)
    producer.flush()
    print(f"\n{Fore.MAGENTA}[KAFKA]{Style.RESET_ALL} Mensagem de saudação enviada para o tópico 'agent_msg'.\n")

    # 3. Busca na base
    doc = input("\nInsira seu CPF: ")
    print(f"\n{Fore.LIGHTGREEN_EX}{Back.BLACK}[INFO]{Style.RESET_ALL} Validando CPF...\n")
    isDocumentValid = validateDocument(doc)

    if isDocumentValid:
        print(f"\n{Fore.LIGHTGREEN_EX}{Back.BLACK}[INFO]{Style.RESET_ALL} CPF Válido! Consultando registro na base...\n")
        customerExists = retrieveCustomerData(document=doc)
        
        if not customerExists:
            print(f"\n{Fore.LIGHTGREEN_EX}{Back.BLACK}[INFO]{Style.RESET_ALL} CPF não encontrado. Iniciando processo para registrar novo cliente...\n")

            requestUserPersonalInfoAgentResponse = requestUserPersonalInfoAgent(productAttributes=desiredProduct)
            print(requestUserPersonalInfoAgentResponse)
            userMsg = input("\nInsira seu nome completo, CEP, data de nascimento (formato Dia/Mês/Ano) e seu email para contato: ")

            print(f"\n{Fore.LIGHTGREEN_EX}{Back.BLACK}[INFO]{Style.RESET_ALL} Resposta Registrada! Coletando informações pessoais...\n")
            gatherUserDataAgentResponse = gatherUserDataAgent(productAttributes=desiredProduct, userMsg=userMsg)
            newUserData = extractUserData(agentResponse=gatherUserDataAgentResponse)

            try:
                print(f"\n{Fore.LIGHTGREEN_EX}{Back.BLACK}[INFO]{Style.RESET_ALL} Consultando CEP...\n")
                addressData = pycep_correios.get_address_from_cep(newUserData["cep"])

                newCustomerParams = {
                    "documento": doc,
                    "nome": newUserData["nome_completo"],
                    "cep": newUserData["cep"],
                    "email": newUserData["email"],
                    "nascimento": newUserData["data_de_nascimento"],
                    "endereco_estado": addressData["uf"],
                    "endereco_cidade": addressData["cidade"],
                    "endereco_bairro": addressData["bairro"],
                    "endereco_logradouro": addressData["logradouro"]
                }
                del newUserData, addressData

                print(f"\n{Fore.LIGHTGREEN_EX}{Back.BLACK}[INFO]{Style.RESET_ALL} Dados coletados! Registrando novo cliente na base...\n")
                print(registerCustomerData(newCustomerParams))

                print(f"\n{Fore.LIGHTGREEN_EX}{Back.BLACK}[INFO]{Style.RESET_ALL} Prosseguindo para compra...\n")
                offer = sellerAgent(productAttributes=desiredProduct, userName=newCustomerParams["nome"])
                print(extractSellerAgentText(output=offer))
                print(extractProductOffer(output=offer))

            except Exception as e:
                print(f"{Fore.RED}[ERRO] Não foi possível consultar o CEP ou processar os dados do cliente. Erro: {e}{Style.RESET_ALL}")

        else:
            print(f"\n{Fore.LIGHTGREEN_EX}{Back.BLACK}[INFO]{Style.RESET_ALL} CPF existente! Recuperando informações do cliente...\n")
            print(customerExists)

            print(f"\n{Fore.LIGHTGREEN_EX}{Back.BLACK}[INFO]{Style.RESET_ALL} Prosseguindo para compra...\n")
            offer = sellerAgent(productAttributes=desiredProduct, userName=customerExists["nome"])
            print(extractSellerAgentText(output=offer))
            print(extractProductOffer(output=offer))
    else:
        print(f"\n{Fore.RED}[ERRO] CPF Inválido!{Style.RESET_ALL}")

    print("-" * 50)
    print(f"\n{Fore.CYAN}✅ Processo finalizado. Aguardando por um novo produto...{Style.RESET_ALL}\n")

