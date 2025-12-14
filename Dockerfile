# Multi-stage build для оптимізації розміру образу
FROM python:3.11-slim AS builder

# Встановлюємо системні залежності для збірки
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Створюємо робочу директорію
WORKDIR /app

# Копіюємо файли залежностей
COPY requirements.txt .

# Встановлюємо Python залежності
RUN pip install --no-cache-dir --user -r requirements.txt

# Фінальний образ
FROM python:3.11-slim

# Встановлюємо тільки необхідні системні залежності
RUN apt-get update && apt-get install -y \
    postgresql-client \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Створюємо непривілейованого користувача
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app /app/logs /app/tmp && \
    chown -R appuser:appuser /app

# Копіюємо встановлені залежності з builder
COPY --from=builder /root/.local /home/appuser/.local

# Встановлюємо PATH для користувача
ENV PATH=/home/appuser/.local/bin:$PATH

# Встановлюємо робочу директорію
WORKDIR /app

# Копіюємо код додатку
COPY --chown=appuser:appuser . .

# Копіюємо та встановлюємо entrypoint скрипт
COPY --chown=appuser:appuser docker-entrypoint.sh /app/
RUN chmod +x /app/docker-entrypoint.sh

# Перемикаємося на непривілейованого користувача
USER appuser

# Відкриваємо порт
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

# Entrypoint
ENTRYPOINT ["/app/docker-entrypoint.sh"]

# Команда запуску
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

