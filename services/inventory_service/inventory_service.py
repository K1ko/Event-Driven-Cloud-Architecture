from shared.event_bus import EventBus
import logging
import time
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

inventory = {
    'item_001': {'name': 'Laptop', 'quantity': 10},
    'item_002': {'name': 'Mouse', 'quantity': 50},
    'item_003': {'name': 'Keyboard', 'quantity': 30},
    'item_004': {'name': 'Monitor', 'quantity': 5},
}

event_bus = EventBus()


def check_and_reserve_inventory(order_data):
    order_id = order_data['order_id']
    items = order_data['items']

    logger.info(f"Checking inventory for order {order_id}")
    time.sleep(1)

    for item in items:
        item_id = item['item_id']
        quantity_needed = item['quantity']

        if item_id not in inventory:
            logger.warning(f"Item {item_id} not found in inventory")
            event_bus.publish_event('inventory.insufficient', {
                'order_id': order_id,
                'reason': f'Item {item_id} not found'
            })
            return

        if inventory[item_id]['quantity'] < quantity_needed:
            logger.warning(f"Insufficient quantity for item {item_id}")
            event_bus.publish_event('inventory.insufficient', {
                'order_id': order_id,
                'reason': f'Insufficient quantity for {item_id}'
            })
            return

    for item in items:
        item_id = item['item_id']
        quantity_needed = item['quantity']
        inventory[item_id]['quantity'] -= quantity_needed
        logger.info(f"Reserved {quantity_needed}x {item_id} for order {order_id}")

    event_bus.publish_event('inventory.reserved', order_data)

    logger.info(f"Inventory reserved for order {order_id}")


def handle_order_created(event):
    order_data = event['data']
    check_and_reserve_inventory(order_data)


def main():
    logger.info("Starting Inventory Service...")
    event_bus.connect()
    event_bus.subscribe(
        ['order.created'],
        handle_order_created,
        queue_name='inventory_service_queue'
    )
    logger.info("Inventory Service is ready and listening for events")
    event_bus.start_consuming()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Shutting down Inventory Service")
        event_bus.close()