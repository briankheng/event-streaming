import json
import logging
import os

from flask import Flask, jsonify
from kafka import KafkaAdminClient, KafkaConsumer, KafkaProducer
from kafka.admin import NewTopic

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)

# Kafka configurations from environment variables
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "kafka:9092")
REQUEST_TOPIC = os.getenv("REQUEST_TOPIC", "request-topic")
RESPONSE_TOPIC = os.getenv("RESPONSE_TOPIC", "response-topic")
GROUP_ID = os.getenv("GROUP_ID", "aggregate-hospital-group")


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


@app.route("/api/hospital", methods=["GET"])
def api_hospital():
    """
    Endpoint to get hospital data from Pine Valley Hospital and Grand Oak Hospital.
    """
    try:
        create_topic(REQUEST_TOPIC)
        create_topic(RESPONSE_TOPIC)

        consumer = KafkaConsumer(
            RESPONSE_TOPIC,
            bootstrap_servers=[KAFKA_BROKER],
            group_id=GROUP_ID,
            value_deserializer=lambda v: v.decode("utf-8"),
            enable_auto_commit=True,
            auto_offset_reset="earliest",
        )

        producer = KafkaProducer(
            bootstrap_servers=[KAFKA_BROKER],
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        )

        logging.info(f"Listening on topic: {RESPONSE_TOPIC}")

        producer.send(REQUEST_TOPIC, "Requesting hospital data")
        logging.info(f"Published request to {REQUEST_TOPIC}")

        messages = []

        for message in consumer:
            logging.info(f"Received message: {message.value}")
            messages.append(json.loads(message.value))

            if len(messages) == 2:
                consumer.close()
                break

        return jsonify({"hospitals": messages})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
