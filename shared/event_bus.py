import json
import pika
from typing import Callable, Dict, Any
from datetime import datetime
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EventBus:
    """Central event bus for publishing and consuming events"""

    def __init__(self, host: str = None):
        if host is None:
            host = os.getenv('RABBITMQ_HOST', 'localhost')
        self.host = host
        self.username = os.getenv('RABBITMQ_USER', 'admin')
        self.password = os.getenv('RABBITMQ_PASS', 'admin')
        self.connection = None
        self.channel = None
        self.exchange_name = 'order_events'

    def connect(self):
        """Establish connection to RabbitMQ"""
        credentials = pika.PlainCredentials(self.username, self.password)
        parameters = pika.ConnectionParameters(
            host=self.host,
            credentials=credentials,
            heartbeat=600,
            blocked_connection_timeout=300
        )

        self.connection = pika.BlockingConnection(parameters)
        self.channel = self.connection.channel()

        # Declare exchange for pub/sub pattern
        self.channel.exchange_declare(
            exchange=self.exchange_name,
            exchange_type='topic',
            durable=True
        )
        logger.info(f"Connected to EventBus at {self.host}")

    def publish_event(self, event_type: str, event_data: Dict[str, Any]):
        """Publish an event to the bus"""
        if not self.channel:
            self.connect()

        event = {
            'event_type': event_type,
            'event_id': f"{event_type}_{datetime.utcnow().timestamp()}",
            'timestamp': datetime.utcnow().isoformat(),
            'data': event_data
        }

        self.channel.basic_publish(
            exchange=self.exchange_name,
            routing_key=event_type,
            body=json.dumps(event),
            properties=pika.BasicProperties(
                delivery_mode=2,
                content_type='application/json'
            )
        )
        logger.info(f"Published event: {event_type} - {event['event_id']}")

    def subscribe(self, event_types: list, callback: Callable, queue_name: str):
        """Subscribe to specific event types"""
        if not self.channel:
            self.connect()

        self.channel.queue_declare(queue=queue_name, durable=True)

        for event_type in event_types:
            self.channel.queue_bind(
                exchange=self.exchange_name,
                queue=queue_name,
                routing_key=event_type
            )

        def on_message(ch, method, properties, body):
            try:
                event = json.loads(body)
                logger.info(f"Received event: {event['event_type']}")
                callback(event)
                ch.basic_ack(delivery_tag=method.delivery_tag)
            except Exception as e:
                logger.error(f"Error processing event: {e}")
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(
            queue=queue_name,
            on_message_callback=on_message
        )

        logger.info(f"Subscribed to events: {event_types} on queue: {queue_name}")

    def start_consuming(self):
        """Start consuming messages"""
        logger.info("Starting to consume messages...")
        self.channel.start_consuming()

    def close(self):
        """Close connection"""
        if self.connection:
            self.connection.close()
            logger.info("EventBus connection closed")