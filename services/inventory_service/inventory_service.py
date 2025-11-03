from shared.event_bus import EventBus
from shared.delay_scheduler import DelayScheduler
import logging
import os
from concurrent.futures import ThreadPoolExecutor
import threading
from collections import defaultdict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Thread-safe inventory with locks per item for better concurrency
class InventoryStore:
    def __init__(self):
        self._inventory = {
            'item_001': {'name': 'Laptop', 'quantity': 9999999},
            'item_002': {'name': 'Mouse', 'quantity': 9999999},
            'item_003': {'name': 'Keyboard', 'quantity': 9999999},
            'item_004': {'name': 'Monitor', 'quantity': 9999999},
        }
        # Fine-grained locks per item for better concurrency
        self._locks = defaultdict(threading.RLock)
    
    def check_and_reserve(self, items):
        """
        Atomically check and reserve inventory for all items.
        Returns (success, reason) tuple.
        """
        # Phase 1: Acquire all locks in sorted order to prevent deadlocks
        item_ids = sorted(set(item['item_id'] for item in items))
        locks = [self._locks[item_id] for item_id in item_ids]
        
        # Acquire all locks
        for lock in locks:
            lock.acquire()
        
        try:
            # Phase 2: Validate availability
            for item in items:
                item_id = item['item_id']
                quantity_needed = item['quantity']
                
                if item_id not in self._inventory:
                    return False, f'Item {item_id} not found'
                
                if self._inventory[item_id]['quantity'] < quantity_needed:
                    return False, f'Insufficient quantity for {item_id}'
            
            # Phase 3: Reserve (only if all items available)
            for item in items:
                item_id = item['item_id']
                quantity_needed = item['quantity']
                self._inventory[item_id]['quantity'] -= quantity_needed
                logger.info(f"Reserved {quantity_needed}x {item_id}")
            
            return True, None
        finally:
            # Always release locks
            for lock in locks:
                lock.release()
    
    def get_quantity(self, item_id):
        """Get current quantity for an item (thread-safe read)."""
        with self._locks[item_id]:
            return self._inventory.get(item_id, {}).get('quantity', 0)

inventory_store = InventoryStore()
event_bus = EventBus()
scheduler = DelayScheduler()

# Reduce workers - most work is non-blocking scheduling
WORKERS = int(os.getenv("INVENTORY_WORKERS", "16"))  # Reduced from 64
executor = ThreadPoolExecutor(max_workers=WORKERS, thread_name_prefix="InvWorker")

INVENTORY_DELAY_SEC = float(os.getenv("INVENTORY_DELAY_SEC", "1"))

def handle_order_created(event):
    """Handle incoming order.created events."""
    order_data = event['data']
    executor.submit(check_and_reserve_inventory, order_data)

def check_and_reserve_inventory(order_data):
    """Check inventory and reserve items for an order."""
    order_id = order_data['order_id']
    items = order_data['items']
    logger.info(f"Checking inventory for order {order_id}")
    
    # Atomic check and reserve operation
    success, reason = inventory_store.check_and_reserve(items)
    
    if not success:
        logger.warning(f"Order {order_id} failed: {reason}")
        event_bus.publish_event('inventory.insufficient', {
            'order_id': order_id,
            'reason': reason
        })
        return
    
    # Schedule the success event with delay (non-blocking)
    scheduler.call_later(
        INVENTORY_DELAY_SEC,
        event_bus.publish_event,
        'inventory.reserved',
        order_data
    )
    logger.info(f"Inventory reserved for order {order_id}, event scheduled in {INVENTORY_DELAY_SEC}s")

def main():
    logger.info("Starting Inventory Service...")
    event_bus.connect()
    event_bus.subscribe(
        ['order.created'],
        handle_order_created,
        queue_name='inventory_service_queue'
    )
    logger.info(f"Inventory Service ready (workers={WORKERS})")
    
    try:
        event_bus.start_consuming()
    except KeyboardInterrupt:
        logger.info("Shutting down Inventory Service")
    finally:
        executor.shutdown(wait=True, timeout=10)
        scheduler.shutdown()
        event_bus.close()

if __name__ == '__main__':
    main()