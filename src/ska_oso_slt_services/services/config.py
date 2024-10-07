import os
import socket


class KafkaConfig:
    # BOOTSTRAP_SERVER = os.getenv("BOOTSTRAP_SERVER"
    # ,"kafka-cluster-kafka-bootstrap:9092")
    BOOTSTRAP_SERVER = os.getenv("BOOTSTRAP_SERVER", "192.168.49.2:30616")
    GROUP_ID = os.getenv("GROUP_ID", "my_consumer_group")
    AUTO_OFFSET_RESET = os.getenv("AUTO_OFFSET_RESET", "latest")
    CLIEND_ID = os.getenv("CLIEND_ID", socket.gethostname())
    CONSUMER_TOPIC = os.getenv("CONSUMER_TOPIC", "oda-to-slt-topic")
    PRODUCER_TOPIC = os.getenv("Producer_TOPIC", "slt-to-frontend-topic")
    TOPIC_POLL_TIME = os.getenv("Producer_TOPIC", "1.0")
