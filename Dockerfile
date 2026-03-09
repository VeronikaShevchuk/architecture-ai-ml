FROM python:3.9-slim

WORKDIR /app

# Копируем специальный requirements с фиксированными версиями
COPY rag_bot/requirements-docker.txt ./requirements.txt

# Устанавливаем конкретные версии, совместимые друг с другом
RUN pip install --no-cache-dir torch==2.0.1 \
    && pip install --no-cache-dir transformers==4.30.0 \
    && pip install --no-cache-dir sentence-transformers==2.2.2 \
    && pip install --no-cache-dir huggingface-hub==0.16.4 \
    && pip install --no-cache-dir faiss-cpu==1.7.4 \
    && pip install --no-cache-dir numpy==1.24.3 \
    && pip install --no-cache-dir python-telegram-bot==20.7 \
    && pip install --no-cache-dir python-dotenv==1.0.0

# Копируем все файлы проекта
COPY rag_bot/ ./rag_bot/
COPY .env .

WORKDIR /app/rag_bot

# Запускаем защищенную версию
CMD ["python", "telegram_bot_secure.py"]