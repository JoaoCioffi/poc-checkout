from src.agents.callback import greetingsAgent,requestUserPersonalInfoAgent,gatherUserDataAgent,sellerAgent
from src.utils.helpers import validateDocument,extractUserData,extractSellerAgentText,extractProductOffer
from src.utils.db_functions import retrieveProductData,retrieveCustomerData,registerCustomerData
from colorama import Fore,Back,Style,init
from datetime import datetime
import pycep_correios
import json
import time

# initialize colorama for terminal output
init(autoreset=True)

# NOVA FUNÇÃO para centralizar a lógica de negócio dos descontos
def calculate_discount(attempts: int, acceptance_time: float, time_limit: float = 10.0) -> int:
    """
    Calcula o percentual de desconto com base nas regras de negócio.
    """
    # Regra 5: Acima da 4ª tentativa com tempo de aceite alto, aplica 10%
    if attempts >= 4 and acceptance_time > time_limit:
        return 10
    
    # Regra 3: Acima de 6 tentativas, o desconto é sempre 10%
    if attempts > 6:
        return 10
    
    # Regra 2: Entre 4 e 6 tentativas
    if 4 <= attempts <= 6:
        # A lógica pode ser simples (ex: 7%) ou mais complexa. Vamos usar 7% como padrão.
        return 7
    
    # Regra 1 e 4: Até 3 tentativas (independente do tempo), o desconto é de até 5%
    if attempts <= 3:
        # Pode ser progressivo, ex: 0% na 1ª, 3% na 2ª, 5% na 3ª
        if attempts == 0:
            return 0
        if attempts == 1:
            return 3
        if attempts >= 2: # Tentativas 2 e 3
            return 5
            
    return 0 # Padrão de segurança

def handlePurchaseFlow(product_data: dict, customer_name: str, product_attributes: dict):
    """
    Gerencia o loop de interação, aplicando a lógica de negócio para descontos
    e passando a oferta definida para o sellerAgent.
    """
    acceptance_time = 0.0
    
    while True:
        if product_data["last_product_offer"]["attempts"] > 0:
            product_data["updated_at"] = datetime.now().isoformat()
        
        # 1. CALCULAR O DESCONTO USANDO A LÓGICA PYTHON
        current_attempts = product_data["last_product_offer"]["attempts"]
        new_discount = calculate_discount(current_attempts, acceptance_time)
        
        # 2. ATUALIZAR O ESTADO DA OFERTA ANTES DE CHAMAR O AGENTE
        product_data["last_product_offer"]["discount"] = new_discount
        original_value = product_data["main_attributes"]["valor_produto"]
        new_value = original_value * (1 - (new_discount / 100))
        product_data["last_product_offer"]["offered_value"] = new_value

        # 3. CHAMAR O AGENTE, QUE AGORA APENAS FORMATA A MENSAGEM
        offer = sellerAgent(
            productAttributes=product_attributes,
            userName=customer_name,
            lastProductOffer=product_data["last_product_offer"], # Passa a oferta já calculada
            acceptanceTime=acceptance_time
        )
        
        agent_text = extractSellerAgentText(output=offer)
        print(agent_text)

        # Extrai para confirmar, mas a lógica principal já foi feita em Python
        new_offer_data = extractProductOffer(output=offer)
        if new_offer_data:
            # Apenas para fins de log, pois o valor já foi definido
            print(f"\n{Fore.CYAN}[INFO]{Style.RESET_ALL} Oferta Apresentada: Valor R$ {new_offer_data['price']:.2f}, Desconto {new_offer_data['discount']}%")

        print(f"\n{Fore.MAGENTA}[DEBUG]{Style.RESET_ALL} Estado atual do produto:\n{json.dumps(product_data, indent=2, default=str, ensure_ascii=False)}")

        start_time = time.time()
        purchase_decision = input("\nVocê deseja prosseguir com a compra? (S/N): ")
        end_time = time.time()
        
        acceptance_time = end_time - start_time
        
        if purchase_decision.lower() == 's':
            print(f"\n{Fore.GREEN}Parabéns pela sua compra! Processo finalizado.{Style.RESET_ALL}")
            break
        
        # A lógica de mensagem de info é baseada no tempo, mas o cálculo do próximo desconto não será
        if acceptance_time > 10.0:
            print(f"\n{Fore.YELLOW}[INFO]{Style.RESET_ALL} Tempo de resposta ({acceptance_time:.1f}s) muito alto. Vamos tentar uma nova abordagem...")
        else:
            print(f"\n{Fore.YELLOW}[INFO]{Style.RESET_ALL} Entendido. O vendedor tentará uma nova oferta.")
        
        product_data["last_product_offer"]["attempts"] += 1
        time.sleep(1)

# O restante do arquivo main.py permanece inalterado...
# 1. Busca e seleção de produto pelo usuário
print(f"\n{Fore.LIGHTGREEN_EX}{Back.BLACK}[INFO]{Style.RESET_ALL} Buscando produtos disponíveis...")
products_data=retrieveProductData()

# Transforma o dicionário de listas em uma lista de dicionários de produtos
products_list=[dict(zip(products_data, t)) for t in zip(*products_data.values())]

print("\nOlá! Bem-vindo à TMB. Temos os seguintes produtos disponíveis para você:\n")
for index, product in enumerate(products_list):
    print(f"  {Fore.YELLOW}{index + 1}. {product['nome_produto']}{Style.RESET_ALL} (Valor: R$ {product['valor_produto']:.2f})")

# Loop para garantir que o usuário escolha uma opção válida
choice=0
while choice < 1 or choice > len(products_list):
    try:
        raw_choice=input(f"\nPor favor, digite o número do produto que você deseja (1 a {len(products_list)}): ")
        choice=int(raw_choice)
        if choice < 1 or choice > len(products_list):
            print(f"{Fore.RED}Opção inválida. Por favor, escolha um número da lista.{Style.RESET_ALL}")
    except (ValueError, TypeError):
        print(f"{Fore.RED}Entrada inválida. Por favor, digite apenas o número correspondente ao produto.{Style.RESET_ALL}")

# Define o 'desiredProduct' com base na escolha do usuário (o resto do script usará esta variável)
desiredProduct=products_list[choice - 1]
product={
    "main_attributes":desiredProduct,
    "last_product_offer":{
        "offered_value":desiredProduct["valor_produto"],
        "discount":0,
        "attempts":0
    },
    "created_at":datetime.now().isoformat(),
    "updated_at":"",
}
print(f"\n{Fore.LIGHTGREEN_EX}{Back.BLACK}[INFO]{Style.RESET_ALL} Ótima escolha! Você selecionou: {desiredProduct['nome_produto']}\n")

# 2. LLM instrui e solicita CPF
greetingsAgentResponse=greetingsAgent(productAttributes=desiredProduct)
print(greetingsAgentResponse)

# 3. Busca na base
doc=input("\nInsira seu CPF: ")
print(f"\n{Fore.LIGHTGREEN_EX}{Back.BLACK}[INFO]{Style.RESET_ALL} Validando CPF...\n")
isDocumentValid=validateDocument(doc)

if isDocumentValid==True:
    print(f"\n{Fore.LIGHTGREEN_EX}{Back.BLACK}[INFO]{Style.RESET_ALL} CPF Válido! Consultando registro na base...\n")
    customerExists=retrieveCustomerData(document=doc)
    
    if bool(customerExists)==False:
        print(f"\n{Fore.LIGHTGREEN_EX}{Back.BLACK}[INFO]{Style.RESET_ALL} CPF não encontrado. Iniciando processo para registrar novo cliente...\n")

        requestUserPersonalInfoAgentResponse=requestUserPersonalInfoAgent(productAttributes=desiredProduct)
        print(requestUserPersonalInfoAgentResponse)
        userMsg=input("\nInsira seu nome completo, CEP, data de nascimento (formato Dia/Mês/Ano) e seu email para contato: ")

        print(f"\n{Fore.LIGHTGREEN_EX}{Back.BLACK}[INFO]{Style.RESET_ALL} Resposta Registrada! Coletando informações pessoais...\n")
        gatherUserDataAgentResponse=gatherUserDataAgent(productAttributes=desiredProduct,userMsg=userMsg)
        newUserData=extractUserData(agentResponse=gatherUserDataAgentResponse)

        print(f"\n{Fore.LIGHTGREEN_EX}{Back.BLACK}[INFO]{Style.RESET_ALL} Consultado CEP...\n")
        addressData=pycep_correios.get_address_from_cep(newUserData["cep"])

        newCustomerParams={
            "documento":doc,
            "nome":newUserData["nome_completo"],
            "cep":newUserData["cep"],
            "email":newUserData["email"],
            "nascimento":newUserData["data_de_nascimento"],
            "endereco_estado":addressData["uf"],
            "endereco_cidade":addressData["cidade"],
            "endereco_bairro":addressData["bairro"],
            "endereco_logradouro":addressData["logradouro"]
        }
        del newUserData,addressData

        print(f"\n{Fore.LIGHTGREEN_EX}{Back.BLACK}[INFO]{Style.RESET_ALL} Dados coletados! Registrando novo cliente na base...\n")
        print(registerCustomerData(newCustomerParams))

        print(f"\n{Fore.LIGHTGREEN_EX}{Back.BLACK}[INFO]{Style.RESET_ALL} Prosseguindo para compra...\n")
        handlePurchaseFlow(product, newCustomerParams["nome"], desiredProduct)

    else:
        print(f"\n{Fore.LIGHTGREEN_EX}{Back.BLACK}[INFO]{Style.RESET_ALL} CPF existente! Recuperando informações do cliente...\n")
        print(customerExists)

        print(f"\n{Fore.LIGHTGREEN_EX}{Back.BLACK}[INFO]{Style.RESET_ALL} Prosseguindo para compra...\n")
        handlePurchaseFlow(product, customerExists["nome"], desiredProduct)
else:
    print("\n[INFO] CPF Inválido!")