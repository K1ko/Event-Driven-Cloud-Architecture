FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# Copy shared module
COPY shared/ ./shared/
COPY services/ ./services/
ENV PYTHONPATH=/app
EXPOSE 8001
CMD ["python", "services/order_service/order_service.py"]