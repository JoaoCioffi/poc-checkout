import re

def validateDocument(document:str) -> bool:
    """
    Valida um número de CPF brasileiro.
    A função primeiro limpa o input, removendo qualquer caractere não numérico.
    Em seguida, verifica se o CPF tem 11 dígitos e se não é uma sequência de 
    dígitos repetidos. Por fim, aplica o algoritmo de validação dos dígitos 
    verificadores para confirmar a validade do documento.
    Args:
        document (str): O CPF a ser validado, podendo conter pontos, traços ou espaços.
    Returns:
        bool: True se o CPF for válido, False caso contrário.
    """
    cpf=re.sub(r'\D','', document) # limpa a entrada, removendo tudo que não for dígito
    if len(cpf) != 11 or cpf==cpf[0] * 11: # verifica se a string tem 11 dígitos após a limpeza ou se todos os dígitos são iguais (ex: 111.111.111-11), o que é inválido
        return False
    # validação do primeiro dígito verificador
    try:
        soma=0
        for i in range(9): # multiplica os 9 primeiros dígitos pela sequência decrescente de 10 a 2
            soma += int(cpf[i]) * (10 - i)
        resto=soma % 11
        digito_verificador_1=0 if resto < 2 else 11 - resto
        if digito_verificador_1 != int(cpf[9]): # compara o dígito calculado com o dígito real (10º dígito do CPF)
            return False
    except (ValueError, IndexError):
        # captura erros caso o input não seja numérico ou tenha tamanho inesperado
        return False
    # validação do segundo dígito verificador
    try:
        soma=0
        for i in range(10): # multiplica os 10 primeiros dígitos pela sequência decrescente de 11 a 2
            soma += int(cpf[i]) * (11 - i)
        resto=soma % 11
        digito_verificador_2=0 if resto < 2 else 11 - resto
        if digito_verificador_2 != int(cpf[10]): # compara o dígito calculado com o dígito real (11º dígito do CPF)
            return False
    except (ValueError,IndexError):
        return False
    # se passou por todas as verificações, o CPF é válido
    return True

def extractUserData(agentResponse:str) -> dict:
    """
    Extrai o conteúdo do bloco userdata de uma resposta de LLM e retorna um dicionário.
    Args:
        agent_response (str): Resposta completa do agente contendo o bloco userdata
    Returns:
        dict: Dicionário com os campos extraídos, ou None se não encontrado
    """
    # Extrair o bloco userdata
    pattern= r'```userdata\s*(.*?)```'
    match=re.search(pattern,agentResponse,re.DOTALL)
    if not match:
        return None
    
    userDataContent=match.group(1)
    
    # Extrair cada campo
    result={}

    # Padrão para capturar: "- campo: valor;"
    fieldPattern=r'-\s*([^:]+):\s*([^;]+);'
    fields=re.findall(fieldPattern,userDataContent)

    for field_name,field_value in fields:
        # Limpar espaços e converter para snake_case
        clean_name=field_name.strip().replace(' ','_')
        result[clean_name]=field_value.strip()
    
    return result

def extractSellerAgentText(output:str) -> str:
    """
    Extrai o texto da mensagem do agente vendedor, removendo o bloco productoffer.
    Args:
        output: String completa retornada pelo LLM
    Returns:
        Texto da mensagem do agente sem o bloco productoffer
    """
    # Remove o bloco productoffer (incluindo as marcações ``` e o conteúdo)
    pattern=r'```productoffer.*?```'
    agent_text=re.sub(pattern,'',output,flags=re.DOTALL)
    # Remove espaços em branco extras no final
    return agent_text.strip()


def extractProductOffer(output:str) -> dict:
    """
    Extrai os dados da oferta do produto do bloco productoffer.
    Args:
        output: String completa retornada pelo LLM
    Returns:
        Dicionário com 'price' (float) e 'discount' (int), ou None se não encontrado
    """
    # Padrão para capturar o conteúdo do bloco productoffer
    pattern=r'```productoffer\s*\n\s*-\s*([\d.]+),\s*\n\s*-\s*(\d+),\s*\n```'
    match=re.search(pattern, output)
    if match:
        price=float(match.group(1))
        discount=int(match.group(2))
        return {
            'price': price,
            'discount': discount
        }
    return None