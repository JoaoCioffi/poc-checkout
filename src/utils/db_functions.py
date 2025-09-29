from src.utils.load_credentials import loadCredentials
import pandas as pd
import psycopg2
import warnings

# Ignora os avisos específicos do SQLAlchemy sobre tipos não reconhecidos
warnings.filterwarnings("ignore", category=UserWarning)

# Load credentials (.env)
credentials=loadCredentials()

# Connection params
conn=psycopg2.connect(
    host=credentials["host"],
    port=credentials["port"],
    dbname=credentials["database"],
    user=credentials["user"],
    password=credentials["password"]
)
conn.set_client_encoding('UTF8')

def retrieveProductData(conn=conn) -> dict:
    query="""
    select 
        tprod.titulo as tipo_produto,
        mprod.titulo as modalidade_produto,
        prod.produto as nome_produto,
        prod.valor as valor_produto,
        prod.carga_horaria as carga_horaria_produto
    from produtos prod
    left join tipo_produto tprod on tprod.id=prod.tipo_produto
    left join modalidade_produto mprod on mprod.id=prod.modalidade_produto
    where lower(prod.produto) not like '%test%';
    """
    df=pd.read_sql(query,conn).sample(n=3)
    product=df.to_dict(orient="list")
    return product

def retrieveCustomerData(document:str,conn=conn) -> dict:
    query=f"""
    select
        clt.documento,
        clt.nome,
        clt.email,
        clt.nascimento,
        clt.genero,
        clt.cep
    from clientes clt
    where clt.documento='{document}'
    """
    df=pd.read_sql(query,conn)
    if not df.empty:
        customer={
            "documento":df["documento"].values[0],
            "nome":df["nome"].values[0],
            "email":df["email"].values[0],
            "nascimento":df["nascimento"].values[0],
            "genero":df["genero"].values[0],
            "cep":df["cep"].values[0],
        }
        return customer
    else:
        customer={}
        return customer

def registerCustomerData(customerParams:dict,conn=conn):
    query=f"""

    """