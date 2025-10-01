from src.utils.load_credentials import loadCredentials
from colorama import Fore,Back,Style,init
import openai
import logging
import json

# initialize colorama for terminal output
init(autoreset=True)

# load credentials (.env)
credentials=loadCredentials()

# OpenAI API params
client=openai.OpenAI(api_key=credentials["openai_api_key"])
logging.getLogger("httpx").setLevel(logging.WARNING) # supress logging for httpx on OpenAI API

# Agents functions
def greetingsAgent(productAttributes:dict) -> str:
    # ... (esta função permanece inalterada)
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
    # ... (esta função permanece inalterada)
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

    Peça todos esses dados, listando, mas no início coloque, "por favor, preciso que me forneça esses dados" ou algo do tipo.

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

def gatherUserDataAgent(productAttributes:dict,userMsg:str) -> str:
    # ... (esta função permanece inalterada)
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

def sellerAgent(productAttributes:dict,userName:str,lastProductOffer:dict,acceptanceTime:float) -> str:
    prompt=f"""
    Você é um agente de vendas da TMB, conversando com {userName} (chame-o pelo primeiro nome) sobre o produto: {productAttributes['nome_produto']}.
    Seu objetivo é ser persuasivo e manter a conversa fluida para fechar a venda.

    **Situação Atual da Oferta:**
    A oferta atual, já calculada e aprovada pela empresa, é a seguinte:
    {json.dumps(lastProductOffer, indent=2, ensure_ascii=False)}

    Sua tarefa é apresentar esta oferta de forma criativa e convincente.

    **Tom e Continuidade da Conversa:**
    Use o campo "attempts" para entender o momento da conversa e adaptar seu tom:
    - Se "attempts" for 0: Esta é a primeira abordagem de venda. Agradeça por ele ter fornecido os dados e apresente o produto e o valor inicial de forma atrativa.
    - Se "attempts" for 1 ou 2: Ele já recusou a oferta anterior. Adote um tom de acompanhamento amigável. Ex: "Olá, {userName}! Notei que ainda não prosseguimos. Para te ajudar a decidir, preparamos uma condição especial..."
    - Se "attempts" for maior que 2: O cliente está hesitante. Use um tom de reengajamento, talvez criando um senso de urgência ou destacando o principal benefício. Ex: "Oi, {userName}, ainda por aí? Não queria que você perdesse a chance de garantir sua vaga no {productAttributes['nome_produto']} com um benefício exclusivo que preparamos..."

    **Instruções Cruciais:**
    1.  **NÃO INVENTE VALORES:** Os valores de "offered_value" e "discount" no JSON que você recebeu são os valores corretos e finais. Use-os na sua mensagem para o cliente.
    2.  **SEJA PERSUASIVO:** Crie uma mensagem que destaque o valor do produto e justifique a oferta. Conecte o desconto (se houver) a um benefício para o cliente.
    3.  **MANTENHA A FLUIDEZ:** Sua resposta deve soar como a continuação da conversa, não como um novo começo.
    4.  **REPLIQUE A SAÍDA:** Ao final da sua mensagem, você DEVE replicar os dados da oferta no bloco de código, exatamente como os recebeu.

    **Formato de Saída Obrigatório:**
    [Sua mensagem de venda criativa para o usuário]

    ```lastproductoffer
    - {lastProductOffer['offered_value']},
    - {lastProductOffer['discount']},
    ```
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