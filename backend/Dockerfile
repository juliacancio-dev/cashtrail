FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Migrations rodam na subida do container: o banco não precisa ficar exposto ao
# runner do GitHub. Seguro enquanto o Container App tiver no máximo 1 réplica.
CMD ["sh", "-c", "alembic upgrade head && exec uvicorn src.main:app --host 0.0.0.0 --port 8000"]
