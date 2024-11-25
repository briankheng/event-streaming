import json
import logging
import os
import time

from kafka import KafkaAdminClient, KafkaConsumer, KafkaProducer
from kafka.admin import NewTopic

# Configure logging
logging.basicConfig(level=logging.INFO)

# Kafka configurations from environment variables
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "kafka:9092")
REQUEST_TOPIC = os.getenv("REQUEST_TOPIC", "request-topic")
RESPONSE_TOPIC = os.getenv("RESPONSE_TOPIC", "response-topic")
GROUP_ID = os.getenv("GROUP_ID", "grand-oak-hospital-group")


# Kafka topic creation function
def create_topic(topic_name):
    admin_client = KafkaAdminClient(bootstrap_servers=KAFKA_BROKER)
    try:
        admin_client.create_topics(
            [NewTopic(name=topic_name, num_partitions=3, replication_factor=1)]
        )
        logging.info(f"Created topic: {topic_name}")
    except Exception as e:
        logging.info(f"Topic {topic_name} already exists or error occurred: {e}")


# Initialize Kafka producer and consumer
def main():
    create_topic(REQUEST_TOPIC)
    create_topic(RESPONSE_TOPIC)

    consumer = KafkaConsumer(
        REQUEST_TOPIC,
        bootstrap_servers=[KAFKA_BROKER],
        group_id=GROUP_ID,
        value_deserializer=lambda v: v.decode("utf-8"),
        auto_offset_reset="earliest",
    )

    producer = KafkaProducer(
        bootstrap_servers=[KAFKA_BROKER],
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )

    logging.info(f"Listening on topic: {REQUEST_TOPIC}")

    for message in consumer:
        logging.info(f"Received message: {message.value}")

        # Process the message
        processed_data = {
            "hospital": "Grand Oak Hospital",
            "address": "123 Grand Oak Street, Springfield",
            "contact": "555-1234",
        }

        # Publish the result to response-topic
        producer.send(RESPONSE_TOPIC, processed_data)
        logging.info(f"Published result to {RESPONSE_TOPIC}: {processed_data}")


if __name__ == "__main__":
    while True:
        try:
            main()
        except Exception as e:
            logging.error(f"Error occurred: {e}")
            time.sleep(5)  # Retry in case of failure
