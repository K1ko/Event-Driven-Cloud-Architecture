from shared.event_bus import EventBus
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

event_bus = EventBus()


def send_notification(customer_id, message):
    logger.info(f"NOTIFICATION to customer {customer_id}: {message}")


def handle_event(event):
    event_type = event['event_type']
    order_data = event['data']

    if event_type == 'order.created':
        send_notification(
            order_data['customer_id'],
            f"Order {order_data['order_id']} received and is being processed"
        )
    elif event_type == 'inventory.insufficient':
        send_notification(
            'system',
            f"Order {order_data['order_id']} failed: {order_data['reason']}"
        )
        event_bus.publish_event('order.final', order_data)
    elif event_type == 'payment.processed':
        send_notification(
            'system',
            f"Payment successful! Order {order_data['order_id']} confirmed"
        )
        event_bus.publish_event('order.final', order_data)
    elif event_type == 'payment.failed':
        send_notification(
            'system',
            f"Payment failed for order {order_data['order_id']}"
        )
        event_bus.publish_event('order.final', order_data)


def main():
    logger.info("Starting Notification Service...")
    event_bus.connect()
    event_bus.subscribe(
        ['order.created', 'inventory.insufficient',
         'payment.processed', 'payment.failed'],
        handle_event,
        queue_name='notification_service_queue'
    )
    logger.info("Notification Service is ready and listening for events")
    event_bus.start_consuming()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Shutting down Notification Service")
        event_bus.close()