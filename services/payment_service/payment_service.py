from shared.event_bus import EventBus
from shared.delay_scheduler import DelayScheduler
import logging
import time
import uuid
import os
from concurrent.futures import ThreadPoolExecutor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

event_bus = EventBus()
scheduler = DelayScheduler()

# Reduce workers - payment processing is lightweight
WORKERS = int(os.getenv("PAYMENT_WORKERS", "16"))  # Reduced from 64
executor = ThreadPoolExecutor(max_workers=WORKERS, thread_name_prefix="PayWorker")

PAYMENT_DELAY_SEC = float(os.getenv("PAYMENT_DELAY_SEC", "2"))

def handle_inventory_reserved(event):
    """Handle incoming inventory.reserved events."""
    order_data = event['data']
    executor.submit(process_payment, order_data)

def process_payment(order_data):
    """Process payment for an order."""
    order_id = order_data['order_id']
    amount = order_data['total_amount']
    logger.info(f"Processing payment for order {order_id}, amount: ${amount}")
    
    # Immediate processing (no blocking)
    payment_successful = True  # Add your payment logic here
    
    if payment_successful:
        payload = {
            'order_id': order_id,
            'payment_id': str(uuid.uuid4()),
            'amount': amount,
            'timestamp': time.time()
        }
        # Non-blocking delayed event publication
        scheduler.call_later(
            PAYMENT_DELAY_SEC,
            event_bus.publish_event,
            'payment.processed',
            payload
        )
        logger.info(f"Payment processed for order {order_id}, event scheduled in {PAYMENT_DELAY_SEC}s")
    else:
        payload = {
            'order_id': order_id,
            'reason': 'Payment gateway error',
            'amount': amount,
            'timestamp': time.time()
        }
        scheduler.call_later(
            PAYMENT_DELAY_SEC,
            event_bus.publish_event,
            'payment.failed',
            payload
        )
        logger.warning(f"Payment failed for order {order_id}, event scheduled in {PAYMENT_DELAY_SEC}s")

def main():
    logger.info("Starting Payment Service...")
    event_bus.connect()
    event_bus.subscribe(
        ['inventory.reserved'],
        handle_inventory_reserved,
        queue_name='payment_service_queue'
    )
    logger.info(f"Payment Service ready (workers={WORKERS})")
    
    try:
        event_bus.start_consuming()
    except KeyboardInterrupt:
        logger.info("Shutting down Payment Service")
    finally:
        executor.shutdown(wait=True, timeout=10)
        scheduler.shutdown()
        event_bus.close()

if __name__ == '__main__':
    main()