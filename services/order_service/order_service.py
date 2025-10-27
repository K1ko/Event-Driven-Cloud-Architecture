from flask import Flask, request, jsonify
from shared.event_bus import EventBus
import uuid
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
event_bus = EventBus()
event_bus.connect()

orders = {}


@app.route('/orders', methods=['POST'])
def create_order():
    try:
        data = request.json
        order_id = str(uuid.uuid4())

        if not data.get('customer_id') or not data.get('items'):
            return jsonify({'error': 'Missing required fields'}), 400

        order = {
            'order_id': order_id,
            'customer_id': data['customer_id'],
            'items': data['items'],
            'total_amount': sum(item['price'] * item['quantity'] for item in data['items']),
            'status': 'pending'
        }

        orders[order_id] = order
        event_bus.publish_event('order.created', order)

        logger.info(f"Order created: {order_id}")

        return jsonify({
            'order_id': order_id,
            'status': 'pending',
            'message': 'Order is being processed'
        }), 202

    except Exception as e:
        logger.error(f"Error creating order: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/orders/<order_id>', methods=['GET'])
def get_order_status(order_id):
    order = orders.get(order_id)
    if not order:
        return jsonify({'error': 'Order not found'}), 404
    return jsonify(order)


def handle_inventory_events(event):
    order_id = event['data']['order_id']

    if order_id not in orders:
        return

    if event['event_type'] == 'inventory.reserved':
        orders[order_id]['status'] = 'inventory_reserved'
        logger.info(f"Order {order_id}: Inventory reserved")

    elif event['event_type'] == 'inventory.insufficient':
        orders[order_id]['status'] = 'failed'
        orders[order_id]['failure_reason'] = 'Insufficient inventory'
        logger.info(f"Order {order_id}: Insufficient inventory")


def handle_payment_events(event):
    order_id = event['data']['order_id']

    if order_id not in orders:
        return

    if event['event_type'] == 'payment.processed':
        orders[order_id]['status'] = 'completed'
        orders[order_id]['payment_id'] = event['data'].get('payment_id')
        logger.info(f"Order {order_id}: Payment processed successfully")

    elif event['event_type'] == 'payment.failed':
        orders[order_id]['status'] = 'payment_failed'
        orders[order_id]['failure_reason'] = event['data'].get('reason', 'Unknown')
        logger.info(f"Order {order_id}: Payment failed")


def start_event_listeners():
    import threading

    def listen():
        listener_bus = EventBus()
        listener_bus.connect()
        listener_bus.subscribe(
            ['inventory.reserved', 'inventory.insufficient',
             'payment.processed', 'payment.failed'],
            lambda event: (
                handle_inventory_events(event) if 'inventory' in event['event_type']
                else handle_payment_events(event)
            ),
            queue_name='order_service_queue'
        )
        listener_bus.start_consuming()

    listener_thread = threading.Thread(target=listen, daemon=True)
    listener_thread.start()


if __name__ == '__main__':
    start_event_listeners()
    app.run(host='0.0.0.0', port=8001, debug=False)