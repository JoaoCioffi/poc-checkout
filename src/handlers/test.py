import threading
import time
from kafka import KafkaProducer, KafkaConsumer
from kafka.admin import KafkaAdminClient, NewTopic
from kafka.errors import TopicAlreadyExistsError
import logging

# Configuração de logging para ver o que está acontecendo
logging.basicConfig(level=logging.WARNING)

# --- Configurações ---
BOOTSTRAP_SERVERS = '127.0.0.1:9092'
TOPIC_NAME = 'meu-topico-de-teste'
CONSUMER_GROUP_ID = 'meu-grupo-consumidor'

# --- 1. Função para criar o tópico ---
def criar_topico():
    """Cria o tópico no Kafka se ele não existir."""
    try:
        admin_client = KafkaAdminClient(
            bootstrap_servers=BOOTSTRAP_SERVERS,
            client_id='meu-admin'
        )

        topic_list = [NewTopic(
            name=TOPIC_NAME,
            num_partitions=1,
            replication_factor=1 # No seu docker-compose, você só tem 1 broker
        )]

        admin_client.create_topics(new_topics=topic_list, validate_only=False)
        logging.info(f"Tópico '{TOPIC_NAME}' criado com sucesso! ✅")

    except TopicAlreadyExistsError:
        logging.warning(f"Tópico '{TOPIC_NAME}' já existe. 👍")
    except Exception as e:
        logging.error(f"Ocorreu um erro ao criar o tópico: {e}")
    finally:
        if 'admin_client' in locals():
            admin_client.close()

# --- 2. Função do Publisher (Producer) ---
def publisher():
    """Envia 5 mensagens para o tópico Kafka."""
    # O value_serializer codifica as mensagens para bytes (formato que o Kafka espera)
    producer = KafkaProducer(
        bootstrap_servers=BOOTSTRAP_SERVERS,
        value_serializer=lambda v: v.encode('utf-8')
    )
    
    logging.info("Publisher iniciado... enviando mensagens. 📬")
    for i in range(5):
        message = f"Olá, Kafka! Esta é a mensagem número {i+1}"
        print(f"Enviando: '{message}'")
        producer.send(TOPIC_NAME, value=message)
        time.sleep(1) # Pequena pausa entre mensagens
    
    # Garante que todas as mensagens pendentes foram enviadas
    producer.flush()
    producer.close()
    logging.info("Publisher finalizou o envio. 📦")

# --- 3. Função do Subscriber (Consumer) ---
def subscriber():
    """Ouve e processa mensagens do tópico Kafka."""
    consumer = KafkaConsumer(
        TOPIC_NAME,
        bootstrap_servers=BOOTSTRAP_SERVERS,
        group_id=CONSUMER_GROUP_ID,
        # 'earliest' para consumir desde a primeira mensagem disponível no tópico
        auto_offset_reset='earliest'
    )
    
    logging.info("Subscriber iniciado... aguardando mensagens. 🎧")
    try:
        for message in consumer:
            # message.value é em bytes, então decodificamos para string
            print(f"Recebido: '{message.value.decode('utf-8')}' | "
                  f"Partição: {message.partition} | Offset: {message.offset}")
    except KeyboardInterrupt:
        logging.info("Subscriber interrompido pelo usuário.")
    finally:
        consumer.close()


if __name__ == "__main__":
    # Passo 1: Garantir que o tópico existe
    criar_topico()
    
    # Aguarda um momento para o tópico ser totalmente estabelecido no cluster
    time.sleep(2)

    # Passo 2: Iniciar o consumidor em uma thread separada para que ele
    # possa ouvir em segundo plano.
    # Usamos daemon=True para que a thread seja encerrada quando o script principal terminar.
    consumer_thread = threading.Thread(target=subscriber, daemon=True)
    consumer_thread.start()
    
    # Aguarda um pouco para garantir que o consumidor se conectou ao tópico
    time.sleep(3)

    # Passo 3: Executar o produtor para enviar as mensagens
    publisher()
    
    # Mantém o script principal vivo por mais alguns segundos para garantir
    # que o consumidor processe a última mensagem antes do encerramento.
    logging.info("Comunicação finalizada. O script será encerrado em 5 segundos.")
    time.sleep(5)