from dotenv import load_dotenv
import json
import os

load_dotenv()

def loadCredentials() -> dict:
    db_config=json.loads(os.getenv("DB_CONFIG"))
    credentials={
        "host": db_config["host"],
        "port": db_config["port"],
        "user": db_config["user"],
        "password": db_config["password"],
        "database": db_config["database"],
        "openai_api_key": os.getenv("OPENAI_API_KEY"),
        "bootstrap_servers":os.getenv("BOOTSTRAP_SERVERS"),
    }
    return credentials