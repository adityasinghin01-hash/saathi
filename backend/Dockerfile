FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DATABASE_URL=sqlite:////app/data/refill_loop.db
WORKDIR /app
COPY pyproject.toml README.md ./
COPY app ./app
COPY eval ./eval
RUN pip install --no-cache-dir . && mkdir -p /app/data
EXPOSE 8080
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
