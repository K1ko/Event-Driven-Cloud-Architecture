from shared.event_bus import EventBus
import logging
import time
import random
import uuid
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

event_bus = EventBus()


def process_payment(order_data):
    order_id = order_data['order_id']
    amount = order_data['total_amount']

    logger.info(f"Processing payment for order {order_id}, amount: ${amount}")
    time.sleep(2)

    payment_successful = random.random() > 0.1

    if payment_successful:
        payment_id = str(uuid.uuid4())
        event_bus.publish_event('payment.processed', {
            'order_id': order_id,
            'payment_id': payment_id,
            'amount': amount,
            'timestamp': time.time()
        })
        logger.info(f"Payment processed successfully for order {order_id}")
    else:
        event_bus.publish_event('payment.failed', {
            'order_id': order_id,
            'reason': 'Payment gateway error',
            'amount': amount,
            'timestamp': time.time()
        })
        logger.warning(f"Payment failed for order {order_id}")


def handle_inventory_reserved(event):
    order_data = event['data']
    process_payment(order_data)


def main():
    logger.info("Starting Payment Service...")
    event_bus.connect()
    event_bus.subscribe(
        ['inventory.reserved'],
        handle_inventory_reserved,
        queue_name='payment_service_queue'
    )
    logger.info("Payment Service is ready and listening for events")
    event_bus.start_consuming()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Shutting down Payment Service")
        event_bus.close()