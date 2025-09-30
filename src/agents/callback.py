from src.utils.load_credentials import loadCredentials
from colorama import Fore,Back,Style,init
import openai
import logging

# initialize colorama for terminal output
init(autoreset=True)

# load credentials (.env)
credentials=loadCredentials()

# OpenAI API params
client=openai.OpenAI(api_key=credentials["openai_api_key"])
logging.getLogger("httpx").setLevel(logging.WARNING) # supress logging for httpx on OpenAI API

# Agents functions
def greetingsAgent(productAttributes:dict) -> str:
    prompt=f"""
    Você é um agente LLM da TMB responsável por interagir com potenciais clientes compradores de infoprodutos.

    Sobre a TMB:
    "Que tal dar mais acesso ao seu infoproduto?
    Para ter mais resultado, tudo o que você precisar fazer é dar oportunidade a quem precisa. 
    Muitas pessoas gostariam de comprar o seu infoproduto, mas são conseguem por conta de meios de pagamentos engessados.
    Mas quando existe uma forma de pagamento parcelada e facilitada, você vai mais longe. 
    O boleto parcelado dá oportunidade a essas pessoas que querem acesso ao aprendizado e traz mais faturamento para o seu bolso!"

    Você sabe que o usuário selecionou pelo streamlit o produto definido por:
    {productAttributes}

    Crie um texto de saudação, de forma que você pretenda vender o produto para ele.
    Você deve solicitar, numa linguagem humana, em português PT-BR, o CPF do usuário para dar prosseguimento com a compra.
    
    Importante:
        - Dê dicas atrativas. Ex: "você sabia que é possível parcelar o boleto com a TMB?" direcionado ao ALUNO do infoproduto.
        - Use (poucos) emojis, para criar uma experiência user-friendly mas minimalista.
        - Não encerre o discurso com "até mais!", "aguardo sua resposta", coisas do tipo, pois não será o encerramento do chat a partir deste ponto.
        - Nunca utilize "estou aqui para ajudar", "no que mais posso te ajudar", coisas do tipo, você não irá sanar dúvidas do usuário, apenas conduzi-lo na jornada de aquisição do produto.
        - Não encerre com "vamos juntos nessa jornada", "estamos juntos nessa", coisas do tipo, você apenas deve esperar pelo usuário para que ele mesmo informe o CPF
    """
    agentResponse=client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{
            "role":"user",
            "content":prompt
        }],
        temperature=1.2
    ).choices[0].message.content
    print(f"\n{Fore.LIGHTMAGENTA_EX}{Back.BLACK}[Greetings Agent]{Style.RESET_ALL}\n")
    return agentResponse

def requestUserPersonalInfoAgent(productAttributes:dict) -> str:
    prompt=f"""
    Você é um agente LLM da TMB responsável por interagir com potenciais clientes compradores de infoprodutos.

    Sobre a TMB:
    "Que tal dar mais acesso ao seu infoproduto?
    Para ter mais resultado, tudo o que você precisar fazer é dar oportunidade a quem precisa. 
    Muitas pessoas gostariam de comprar o seu infoproduto, mas são conseguem por conta de meios de pagamentos engessados.
    Mas quando existe uma forma de pagamento parcelada e facilitada, você vai mais longe. 
    O boleto parcelado dá oportunidade a essas pessoas que querem acesso ao aprendizado e traz mais faturamento para o seu bolso!"

    Você sabe que o usuário selecionou pelo streamlit o produto definido por:
    {productAttributes}

    
    Os dados necessários para cadastro do usuário são:
    - nome completo,
    - cep,
    - data de nascimento,
    - email,

    Peça todos esses dados (você pode usar esse parágrafo como exemplo: "preciso do seu nome completo, CEP, data de nascimento e email por favor").

    Importante! Não comece por "Olá", pois você é a segunda etapa (pós informe do CPF pelo usuário), comece por "obrigado por informar". Você deve interagir normalmente
    como continuação das etapas do processo. Use sempre linguagem humana, em português PT-BR.
    """
    agentResponse=client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{
            "role":"user",
            "content":prompt
        }],
        temperature=1.2
    ).choices[0].message.content
    print(f"\n{Fore.LIGHTMAGENTA_EX}{Back.BLACK}[Request User Personal Info Agent]{Style.RESET_ALL}\n")
    return agentResponse

def gatherUserDataAgent(productAttributes:dict,userMsg:str,retry=None) -> str:
    prompt=f"""
    Você é um agente LLM da TMB responsável por interagir com potenciais clientes compradores de infoprodutos.

    Sobre a TMB:
    "Que tal dar mais acesso ao seu infoproduto?
    Para ter mais resultado, tudo o que você precisar fazer é dar oportunidade a quem precisa. 
    Muitas pessoas gostariam de comprar o seu infoproduto, mas são conseguem por conta de meios de pagamentos engessados.
    Mas quando existe uma forma de pagamento parcelada e facilitada, você vai mais longe. 
    O boleto parcelado dá oportunidade a essas pessoas que querem acesso ao aprendizado e traz mais faturamento para o seu bolso!"

    Você sabe que o usuário selecionou pelo streamlit o produto definido por:
    {productAttributes}

    Após a solicitar dados do usuário como nome completo, CEP e data de nascimento no texto a seguir vindo do usuário:
    {userMsg}

    Tente extrair esses dados colocando no formato abaixo (estruturando em lista, SEMPRE nesta ordem):
    ```userdata
    - nome completo: <nome informado aqui>;
    - cep: <cep informado aqui>;
    - data de nascimento: <data de nascimento informada aqui>;
    - email: <email informado aqui>;
    ```
    
    Lembre-se que o usuário irá enviar isso através de um chat whatsapp, portanto ele poderá colocar informações ou palavras, até mesmo dados irrelevantes,
    ou até mesmo fora de ordem. Seu objetivo é extrair esses dados com precisão desse texto.

    Importante! Não comece por "Olá", pois você é a terceira etapa. Você deve apenas gerar esses dados no formato userdata esperado.
    - Nome SEMPRE com iniciais maiúsculas
    - retorne o CEP sem pontos ou traços, somente o CEP inteiro e sem espaçamento
    - retorne a data de nascimento no formato AAAA-MM-DD
    """
    agentResponse=client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{
            "role":"user",
            "content":prompt
        }],
        temperature=1.2
    ).choices[0].message.content
    print(f"\n{Fore.LIGHTMAGENTA_EX}{Back.BLACK}[Gather User Data Agent]{Style.RESET_ALL}\n")
    return agentResponse

def sellerAgent(productAttributes:dict,userName:str,streamlitData=None,lastProductOffer:dict=None) -> str:
    prompt=f"""
    Você é um agente LLM da TMB responsável por interagir com potenciais clientes compradores de infoprodutos.

    Sobre a TMB:
    "Que tal dar mais acesso ao seu infoproduto?
    Para ter mais resultado, tudo o que você precisar fazer é dar oportunidade a quem precisa. 
    Muitas pessoas gostariam de comprar o seu infoproduto, mas são conseguem por conta de meios de pagamentos engessados.
    Mas quando existe uma forma de pagamento parcelada e facilitada, você vai mais longe. 
    O boleto parcelado dá oportunidade a essas pessoas que querem acesso ao aprendizado e traz mais faturamento para o seu bolso!"

    Você sabe que o usuário {userName} (chame-o de uma forma amigável, pelo primeiro nome) selecionou pelo streamlit o produto definido por:
    {productAttributes}

    Seu objetivo é dar continuidade ao processo de aquisição do produto pelo usuário. Você sabe que anteriormente ele forneceu os dados, então
    deve começar agradecendo de uma forma amigável o usuário por fonecer e gerar uma mensagem atrativa ao processo de compra. Seu objetivo
    é vender o produto da melhor forma possível.

    Importante:
        - Não explique novamente sobre a TMB e sobre os meios de pagamento, isso já foi esclarecido anteriormente
        - Não explique novamente sobre o produto (ex: modalidade, carga horária, etc), esses dados já foram informados anteriormente para o usuário
        - Seja o mais direcionado possível para a venda.
        - O usuário já sabe do produto, então você apenas deve "insistir" (de uma forma amigável) para que ele compre
        - regra de negócio: o desconto NUNCA deve exceder 10% do valor original, mas os descontos devem ser começados aos poucos
        - termine com algo como "vamos efetuar a compra?" (porém nunca com essas palavras, seja amigável e tente sempre gerar uma nova abordagem final)
        - nunca use "estou aqui para tirar dúvidas" ou coisas do tipo, você somente deve interagir com o usuário afim de fechar a aquisição do produto.

    Por favor, retorne o desconto (percentual) e o valor no formato:
    ```productoffer
    - <valor_ofertado>,
    - <desconto_condicionado_percentual>,
    ```

    para que o sistema seja capaz de coletar isso e aplicar no processo de compra. Além disso, explique ao usuário que ele pode informar quando deseja prosseguir com a compra.
    """
    agentResponse=client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{
            "role":"user",
            "content":prompt
        }],
        temperature=1.2
    ).choices[0].message.content
    print(f"\n{Fore.LIGHTMAGENTA_EX}{Back.BLACK}[Seller Agent]{Style.RESET_ALL}\n")
    return agentResponse