from src.agents.callback import greetingsAgent,requestUserPersonalInfoAgent,gatherUserDataAgent
from src.utils.db_functions import retrieveCustomerData,registerCustomerData
from src.utils.helpers import validateDocument,extractUserData
import pycep_correios

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
doc='22985068843'
customerExists=retrieveCustomerData(document=doc)
if bool(customerExists)==False: # método bool(dict) é False para dicionário vazio: se o CPF informado não existe, prosseguir com cadastro
    isDocumentValid=validateDocument(doc)
    if isDocumentValid==True:
        
        # solicita dados
        requestUserPersonalInfoAgentResponse=requestUserPersonalInfoAgent(productAttributes=desiredProduct)
        print(requestUserPersonalInfoAgentResponse)

        userMsg=f"Oi, claro. Meu nome é zain bolt, meu cep é 15990010 nascido em 02/09/97. Email teste@teste.com.br"
        gatherUserDataAgentResponse=gatherUserDataAgent(productAttributes=desiredProduct,userMsg=userMsg)
        userData=extractUserData(agentResponse=gatherUserDataAgentResponse)
        addressData=pycep_correios.get_address_from_cep(userData["cep"])

        customerParams={
            "documento":doc,
            "nome":userData["nome_completo"],
            "cep":userData["cep"],
            "email":userData["email"],
            "nascimento":userData["data_de_nascimento"],
            "endereco_estado":addressData["uf"],
            "endereco_cidade":addressData["cidade"],
            "endereco_bairro":addressData["bairro"],
            "endereco_logradouro":addressData["logradouro"]
        }
        print(customerParams)
        print(registerCustomerData(customerParams))
    else:
        # TODO: trazer agente informando que o documento inserido não é válido
        pass
else:
    # TODO: inserir os dados lidos diretamente base no prompt do agente
    pass
    
# 4. Dados registrados ou rebuscados, prosseguir para oferta e compra
# TODO