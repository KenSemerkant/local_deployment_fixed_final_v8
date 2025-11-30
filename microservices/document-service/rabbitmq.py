import os
import pika
import json
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
QUEUE_NAME = "document_processing_queue"

def get_rabbitmq_connection():
    """Establish a connection to RabbitMQ with retries"""
    retries = 5
    while retries > 0:
        try:
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=RABBITMQ_HOST)
            )
            return connection
        except pika.exceptions.AMQPConnectionError as e:
            logger.warning(f"Failed to connect to RabbitMQ: {e}. Retrying in 5 seconds...")
            retries -= 1
            time.sleep(5)
    
    logger.error("Could not connect to RabbitMQ after multiple retries.")
    return None

def publish_message(message: dict):
    """Publish a message to the queue"""
    connection = get_rabbitmq_connection()
    if not connection:
        logger.error("Failed to publish message: No RabbitMQ connection")
        return False

    try:
        channel = connection.channel()
        channel.queue_declare(queue=QUEUE_NAME, durable=True)
        
        channel.basic_publish(
            exchange='',
            routing_key=QUEUE_NAME,
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=2,  # make message persistent
            )
        )
        logger.info(f"Published message to {QUEUE_NAME}: {message}")
        connection.close()
        return True
    except Exception as e:
        logger.error(f"Error publishing message: {e}")
        if connection:
            connection.close()
        return False
