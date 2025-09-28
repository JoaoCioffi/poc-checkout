from src.utils.load_credentials import loadCredentials
from colorama import Fore,Back,Style,init
from openai import OpenAI

# initialize colorama for terminal output
init(autoreset=True)

def get_openai_client():
    global _client
    if _client is None:
        credentials = loadCredentials()
        _client = OpenAI(api_key=credentials["OPENAI_API_KEY"])
    return _client

# --- Example usage --- #

# Creates agent instance
client = get_openai_client()
prompt="Hello, how are you?"
agent_response=client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role":"user","content":prompt}],
    temperature=1.2
).choices[0].message.content
print(f"\n{Fore.LIGHTMAGENTA_EX}{Back.BLACK}[TEST]{Style.RESET_ALL} Agent response:\n{agent_response}\n")