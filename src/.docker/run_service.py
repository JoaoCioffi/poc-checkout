import subprocess
import time

def docker_compose_up():
    print("\n🐳 Iniciando containers via Docker Compose...\n")
    try:
        subprocess.run(["docker", "compose", "up", "-d"], check=True)
        print("\n🟢 Containers iniciados.")
        print("🔗 Kafka UI: http://localhost:8080\n")
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Falha ao iniciar containers: {e}")
        return False
    return True

def docker_compose_down():
    print("\n🧹 Encerrando containers...\n")
    try:
        subprocess.run(["docker", "compose", "down"], check=True)
        print("\n[INFO] Containers finalizados com sucesso.\n")
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Erro ao parar containers: {e}")

if __name__ == "__main__":
    if docker_compose_up():
        try:
            print("\n⏳ Pressione CTRL+C para parar os containers.\n")
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            docker_compose_down()