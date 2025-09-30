from src.agents.callback import greetingsAgent,requestUserPersonalInfoAgent,gatherUserDataAgent,sellerAgent
from src.utils.helpers import validateDocument,extractUserData,extractSellerAgentText,extractProductOffer
from src.utils.db_functions import retrieveCustomerData,registerCustomerData
from colorama import Fore,Back,Style,init
import pycep_correios

# initialize colorama for terminal output
init(autoreset=True)

# 1. Usuário seleciona produto
desiredProduct={
    "tipo_produto":"Infoproduto",
    "modalidade_produto":"Online",
    "nome_produto":"Licensed Steel Fish",
    "valor_produto":1000.0,
    "carga_horaria_produto":"40 horas"
}

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
    
    if bool(customerExists)==False: # método bool(dict) é False para dicionário vazio: se o CPF informado não existe, prosseguir com cadastro
        print(f"\n{Fore.LIGHTGREEN_EX}{Back.BLACK}[INFO]{Style.RESET_ALL} CPF não encontrado. Iniciando processo para registrar novo cliente...\n")

        # solicita dados
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
        del newUserData,addressData # limpando memória

        print(f"\n{Fore.LIGHTGREEN_EX}{Back.BLACK}[INFO]{Style.RESET_ALL} Dados coletados! Registrando novo cliente na base...\n")
        print(registerCustomerData(newCustomerParams))

        print(f"\n{Fore.LIGHTGREEN_EX}{Back.BLACK}[INFO]{Style.RESET_ALL} Prosseguindo para compra...\n")
        offer=sellerAgent(productAttributes=desiredProduct,userName=newCustomerParams["nome"])
        print(extractSellerAgentText(output=offer))
        print(extractProductOffer(output=offer))

    else:
        print(f"\n{Fore.LIGHTGREEN_EX}{Back.BLACK}[INFO]{Style.RESET_ALL} CPF existente! Recuperando informações do cliente...\n")
        print(customerExists)

        print(f"\n{Fore.LIGHTGREEN_EX}{Back.BLACK}[INFO]{Style.RESET_ALL} Prosseguindo para compra...\n")
        offer=sellerAgent(productAttributes=desiredProduct,userName=customerExists["nome"])
        print(extractSellerAgentText(output=offer))
        print(extractProductOffer(output=offer))
else:
    print("\n[INFO] CPF Inválido!")