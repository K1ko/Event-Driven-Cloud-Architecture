import requests
import time
import json

BASE_URL = "http://localhost:8001"


def create_order(customer_id, items):
    print(f"\n{'=' * 60}")
    print(f"Creating order for customer: {customer_id}")
    print(f"{'=' * 60}")

    order_data = {"customer_id": customer_id, "items": items}
    response = requests.post(f"{BASE_URL}/orders", json=order_data)

    if response.status_code == 202:
        result = response.json()
        order_id = result['order_id']
        print(f"✓ Order created successfully!")
        print(f"  Order ID: {order_id}")
        print(f"  Status: {result['status']}")
        return order_id
    else:
        print(f"✗ Error: {response.json()}")
        return None


def check_order_status(order_id):
    print(f"\nChecking order status...")

    for attempt in range(10):
        time.sleep(2)
        response = requests.get(f"{BASE_URL}/orders/{order_id}")

        if response.status_code == 200:
            order = response.json()
            status = order['status']
            print(f"  [{attempt + 1}/10] Status: {status}")

            if status in ['completed', 'failed', 'payment_failed']:
                print(f"\n{'=' * 60}")
                print("Final Order Status:")
                print(json.dumps(order, indent=2))
                print(f"{'=' * 60}")
                return order


if __name__ == "__main__":
    print("\nEVENT-DRIVEN ORDER SYSTEM - TEST CLIENT\n")

    # Test 1: Successful order
    order_id = create_order(
        "customer_001",
        [{"item_id": "item_001", "name": "Laptop", "quantity": 1, "price": 1200}]
    )
    if order_id:
        check_order_status(order_id)