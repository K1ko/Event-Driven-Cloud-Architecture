# Event-Driven Cloud Architecture

Tento repozitár demonštruje **event-driven (udalostne riadenú)** architektúru v prostredí cloudu.  
Každá služba funguje ako nezávislá jednotka, ktorá reaguje na prijaté udalosti a publikuje nové.  

---
## Microservices
1. Order Service (order-service)

   - REST API pre vytváranie objednávok
   - Vytvára order.created udalosti
   - Maintains order state 
   - Port: 8001


2. Inventory Service (inventory-service)

   - Počúva order.created udalosti
   - Validuje dostupnosť zásob
   - Publikuje inventory.reserved alebo inventory.failed udalosti


3. Payment Service (payment-service)

   - Počúva inventory.reserved udalosti
   - Spracováva platby
   - Publikuje payment.completed alebo payment.failed udalosti


4. Notification Service (notification-service)

   - Počúva na všetky udalosti
   - Posiela notifikácie zákazníkom
   - Decoupled od ostatných služieb


5. Message Broker (RabbitMQ)

   - Zaoberá sa smeraním udalostí medzi službami
   - Zabezpečuje spoľahlivú komunikáciu
   - Ports: 5672 (AMQP), 15672 (Management UI)

## Prerekvizity
Pred začatím sa uistite, že máte nainštalované nasledujúce nástroje:

* Docker Desktop (v24.0+)
* Docker Compose (v2.0+) - Súčasť Docker Desktop
* Python (3.8+) - Pre spustenie mikroservisov
* Git - Na klonovanie repozitára

## Overenie inštalácie
Overte inštaláciu Dockeru a Docker Compose príkazmi:
```bash
docker --version
docker-compose --version
```
Ak sú príkazy úspešné, ste pripravení pokračovať.
## Inštalácia
1. Klonujte repozitár:
```bash
    git clone https://github.com/K1ko/Event-Driven-Cloud-Architecture.git
    cd Event-Driven-Cloud-Architecture
```
2. Projektová štruktúra:
```
event-driven-order-system/
│
├── README.md                    # Tento súbor
├── requirements.txt             # Python závislosti
├── docker-compose.yml           # Docker orchestration
│
├── shared/                      # Zdieľané moduly
│   ├── __init__.py
│   └── event_bus.py            # Event bus
│
├── services/                    # Microservices
│   ├── order_service/
│   │   ├── Dockerfile
│   │   └── order_service.py    # Order management API
│   │
│   ├── inventory_service/
│   │   ├── Dockerfile
│   │   └── inventory_service.py # Inventory validation
│   │
│   ├── payment_service/
│   │   ├── Dockerfile
│   │   └── payment_service.py  # Payment processing
│   │
│   └── notification_service/
│       ├── Dockerfile
│       └── notification_service.py # Notifications
│
└── test_client.py              # Test automation
   ```

3. Spuste systém pomocou Docker Compose:
```bash
    docker-compose up --build
# Alebo na pozadí:
    docker-compose up -d --build
```
4. Overte, či bežia všetky služby:
```bash
    docker-compose ps
```
Mali by ste vidieť všetky služby v stave "Up".

## Použitie
1. Vytvorte objednávku pomocou testovacieho klienta:

Otvorte nový terminál a spustite:
```bash
    python test_client.py
```
2. Použitie cURL na vytvorenie objednávky:
```bash
    curl -X POST http://localhost:8001/orders \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "customer_001",
    "items": [
      {
        "item_id": "item_001",
        "name": "Laptop",
        "quantity": 1,
        "price": 1200.00
      }
    ]
  }'
```

