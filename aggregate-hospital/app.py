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


def consume_messages():
    create_topic(RESPONSE_TOPIC)

    consumer = KafkaConsumer(
        RESPONSE_TOPIC,
        bootstrap_servers=[KAFKA_BROKER],
        group_id=GROUP_ID,
        value_deserializer=lambda v: v.decode("utf-8"),
        enable_auto_commit=True,
        auto_offset_reset="earliest",
    )

    logging.info(f"Listening on topic: {RESPONSE_TOPIC}")

    messages = []

    message_pack = consumer.poll(timeout_ms=5000)
    for tp, messages_pack in message_pack.items():
        for message in messages_pack:
            messages.append(json.loads(message.value))

    consumer.commit()
    consumer.close()

    return messages


@app.route("/api/hospital", methods=["GET"])
def api_hospital():
    """
    Endpoint to consume and return aggregated messages from Kafka.
    """
    try:
        messages = consume_messages()
        return jsonify({"hospitals": messages})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
