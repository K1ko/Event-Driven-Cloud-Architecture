FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY shared/ ./shared/
COPY services/ ./services/
ENV PYTHONPATH=/app
CMD ["python", "services/notification_service/notification_service.py"]