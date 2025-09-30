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

def wait_for_kafka(max_attempts=30):
    print("\n⏳ Aguardando Kafka ficar pronto...\n")
    for attempt in range(max_attempts):
        try:
            result = subprocess.run(
                ["docker", "exec", "kafka", "kafka-broker-api-versions", 
                 "--bootstrap-server", "localhost:9092"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                print("\n✅ Kafka está pronto!\n")
                return True
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
            pass
        
        time.sleep(2)
        print(f"   Tentativa {attempt + 1}/{max_attempts}...")
    
    print("[ERROR] Kafka não ficou pronto a tempo.")
    return False

def create_kafka_topics():
    topics = ["user_msg","agent_msg","product_info","streamlit_events"]
    
    print("📝 Criando tópicos no Kafka...\n")
    
    for topic in topics:
        try:
            result = subprocess.run(
                ["docker", "exec", "kafka", "kafka-topics", 
                 "--create", 
                 "--topic", topic,
                 "--bootstrap-server", "localhost:9092",
                 "--partitions", "1",
                 "--replication-factor", "1"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print(f"Tópico '{topic}' criado com sucesso")
            elif "already exists" in result.stderr:
                print(f"Tópico '{topic}' já existe")
            else:
                print(f"\n⚠️ Erro ao criar tópico '{topic}': {result.stderr}")
                
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] Falha ao criar tópico '{topic}': {e}")

def docker_compose_down():
    print("\n🧹 Encerrando containers...\n")
    try:
        subprocess.run(["docker", "compose", "down"], check=True)
        print("\n[INFO] Containers finalizados com sucesso.\n")
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Erro ao parar containers: {e}")

if __name__ == "__main__":
    if docker_compose_up():
        if wait_for_kafka():
            create_kafka_topics()
            
            try:
                print("\n⏳ Pressione CTRL+C para parar os containers.\n")
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                docker_compose_down()
        else:
            print("\n[ERROR] Encerrando devido a falha na inicialização do Kafka.")
            docker_compose_down()