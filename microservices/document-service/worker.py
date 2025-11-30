import json
import logging
import os
import time
import pika
from main import process_document_task, update_document_step, redis_client
from rabbitmq import get_rabbitmq_connection, QUEUE_NAME

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def callback(ch, method, properties, body):
    """Callback function to process messages from the queue"""
    try:
        message = json.loads(body)
        document_id = message.get("document_id")
        
        if not document_id:
            logger.error("Received message without document_id")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        logger.info(f"Received processing task for document {document_id}")
        
        # Update step to indicate queued status
        update_document_step(document_id, "Picked up by worker")
        
        # Process the document
        # We reuse the existing logic from main.py
        # Note: process_document_task handles its own DB connections and error handling
        process_document_task(document_id)
        
        logger.info(f"Successfully processed document {document_id}")
        ch.basic_ack(delivery_tag=method.delivery_tag)
        
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        # Negative acknowledgement - requeue if transient, or dead-letter if persistent failure
        # For now, we'll ack to prevent infinite loops on bad data, but log the error
        ch.basic_ack(delivery_tag=method.delivery_tag)

def start_worker():
    """Start the RabbitMQ worker"""
    logger.info("Starting Document Worker...")
    
    connection = get_rabbitmq_connection()
    if not connection:
        logger.error("Failed to connect to RabbitMQ. Exiting.")
        return

    # Debug Redis connection
    if redis_client:
        logger.info(f"Redis client initialized: {redis_client}")
        try:
            redis_client.ping()
            logger.info("Redis connection successful")
        except Exception as e:
            logger.error(f"Redis ping failed: {e}")
    else:
        logger.error("Redis client is None!")

    channel = connection.channel()
    channel.queue_declare(queue=QUEUE_NAME, durable=True)
    
    # Fair dispatch
    channel.basic_qos(prefetch_count=1)
    
    channel.basic_consume(queue=QUEUE_NAME, on_message_callback=callback)
    
    logger.info("Worker started. Waiting for messages...")
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        channel.stop_consuming()
        connection.close()
    except Exception as e:
        logger.error(f"Worker crashed: {e}")
        if connection and not connection.is_closed:
            connection.close()

if __name__ == "__main__":
    # Wait for other services to be ready
    time.sleep(10)
    start_worker()
