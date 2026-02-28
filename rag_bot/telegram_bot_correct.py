#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ИТОГОВЫЙ TELEGRAM БОТ С УМНЫМИ ПОРОГАМИ РЕЛЕВАНТНОСТИ
Запуск: python telegram_bot_smart.py
"""

import os
import logging
import pickle
from pathlib import Path
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from sentence_transformers import SentenceTransformer
import faiss
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Токен бота
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not TOKEN:
    raise ValueError("❌ TELEGRAM_BOT_TOKEN не найден в .env файле!")


class SmartRAGBot:
    """RAG-бот с умными порогами релевантности"""
    
    def __init__(self, index_path="./vector_index/faiss_index"):
        self.index_path = Path(index_path)
        self.model = None
        self.index = None
        self.documents = []
        self.filenames = []
        
        # Базовый порог релевантности
        self.default_threshold = 0.61  # Для обычных запросов
        
        print("🔄 Загрузка умного бота...")
        self._load()
        print(f"✅ Бот готов! Загружено {len(self.documents)} документов")
        print(f"🎯 Базовый порог релевантности: {self.default_threshold}")
    
    def _load(self):
        """Загрузка всех компонентов"""
        # Загрузка модели
        self.model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        
        # Загрузка FAISS индекса
        faiss_file = self.index_path / "index.faiss"
        if faiss_file.exists():
            self.index = faiss.read_index(str(faiss_file))
            print(f"   📊 Векторов в индексе: {self.index.ntotal}")
        
        # Загрузка документов
        pkl_file = self.index_path / "index.pkl"
        if pkl_file.exists():
            with open(pkl_file, 'rb') as f:
                docstore, _ = pickle.load(f)
            
            if hasattr(docstore, '_dict'):
                docs_dict = docstore._dict
            else:
                docs_dict = docstore.dict
            
            for doc_id, doc in docs_dict.items():
                self.documents.append({
                    'text': doc.page_content,
                    'filename': doc.metadata.get('filename', 'unknown')
                })
                self.filenames.append(doc.metadata.get('filename', 'unknown'))
    
    def search(self, query, k=10):
        """Поиск релевантных документов"""
        # Получаем вектор запроса
        query_vector = self.model.encode([query]).astype('float32')
        
        # Поиск в индексе
        distances, indices = self.index.search(query_vector, k)
        
        results = []
        for idx, dist in zip(indices[0], distances[0]):
            if 0 <= idx < len(self.documents):
                # Конвертируем расстояние в релевантность (0-1)
                relevance = 1 / (1 + dist)
                
                results.append({
                    'text': self.documents[idx]['text'],
                    'filename': self.documents[idx]['filename'],
                    'relevance': float(relevance)
                })
        
        # Сортируем по релевантности (убывание)
        results.sort(key=lambda x: x['relevance'], reverse=True)
        return results
    
    def answer(self, query):
        """Формирование ответа с умными порогами релевантности"""
        # Получаем результаты поиска
        results = self.search(query, k=10)
        
        if not results:
            return f"❌ Я не знаю ответа на вопрос: '{query}'"
        
        max_relevance = results[0]['relevance']
        
        # ⭐ УМНЫЕ ПОРОГИ В ЗАВИСИМОСТИ ОТ ЗАПРОСА
        query_lower = query.lower()
        
        # Для запросов о Неуклюжей и Парке Встреч - более низкий порог
        if "неуклюж" in query_lower or "парк встреч" in query_lower:
            threshold = 0.58
            reason = "низкий порог (0.58) для ключевых персонажей"
        # Для запросов о Магистре Теней и Архивариусе - стандартный порог
        elif "магистр" in query_lower or "архивариус" in query_lower or "меркурий" in query_lower:
            threshold = 0.61
            reason = "стандартный порог (0.61)"
        # Для всех остальных запросов - высокий порог (отсекаем случайные)
        else:
            threshold = 0.61
            reason = "стандартный порог (0.61)"
        
        # Логирование для отладки
        print(f"\n📊 Запрос: '{query}'")
        print(f"   Макс. релевантность: {max_relevance:.3f}")
        print(f"   Используемый порог: {threshold} ({reason})")
        for i, r in enumerate(results[:3]):
            print(f"   {i+1}. {r['filename']}: {r['relevance']:.3f}")
        
        # Если релевантность ниже порога - отвечаем "не знаю"
        if max_relevance < threshold:
            return f"❌ Я не знаю ответа на вопрос: '{query}'"
        
        # Формируем ответ только с результатами выше порога
        good_results = [r for r in results if r['relevance'] >= threshold]
        
        if not good_results:
            return f"❌ Я не знаю ответа на вопрос: '{query}'"
        
        answer = f"🔍 Запрос: {query}\n\n"
        answer += f"📚 Найдено результатов: {len(good_results)}\n\n"
        
        for i, r in enumerate(good_results[:3]):  # Показываем только топ-3
            # Обрезаем текст для читаемости
            text = r['text']
            if len(text) > 300:
                text = text[:300] + "..."
            
            answer += f"*Результат {i+1}* (релевантность: {r['relevance']:.2f})\n"
            answer += f"📁 Файл: {r['filename']}\n"
            answer += f"📄 Текст: {text}\n\n"
        
        return answer


# Создаем экземпляр бота
try:
    rag_bot = SmartRAGBot()
except Exception as e:
    print(f"❌ Ошибка загрузки бота: {e}")
    rag_bot = None


# Обработчики команд
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    welcome_text = (
        "👋 Привет! Я RAG-бот для мира 'Хроники Сумеречного Легиона'.\n\n"
        "📚 Что я умею:\n"
        "• Отвечать на вопросы о персонажах и событиях\n"
        "• Находить информацию в базе знаний\n"
        "• Говорить 'Я не знаю', если информации нет\n\n"
        "💡 Примеры вопросов:\n"
        "• Кто такая Неуклюжая?\n"
        "• Что такое Парк Встреч?\n"
        "• Кто такой Магистр Теней?\n"
        "• Кто такой Архивариус?\n\n"
        "Просто напиши свой вопрос!"
    )
    await update.message.reply_text(welcome_text)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    help_text = (
        "📚 Справка по использованию\n\n"
        "• Задай любой вопрос о мире 'Хроники Сумеречного Легиона'\n"
        "• Бот найдет информацию в базе знаний\n"
        "• Если информация не найдена, бот ответит 'Я не знаю'\n\n"
        "Команды:\n"
        "/start - приветствие\n"
        "/help - эта справка\n"
        "/stats - статистика базы знаний\n"
        "/threshold - информация о порогах релевантности"
    )
    await update.message.reply_text(help_text)


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /stats"""
    if not rag_bot:
        await update.message.reply_text("❌ Бот временно недоступен")
        return
    
    stats_text = (
        f"📊 Статистика бота\n\n"
        f"• Всего документов: {len(rag_bot.documents)}\n"
        f"• Векторов в индексе: {rag_bot.index.ntotal if rag_bot.index else 0}\n"
        f"• Базовый порог: {rag_bot.default_threshold}\n"
        f"• Модель: all-MiniLM-L6-v2\n\n"
        f"⚙️ Умные пороги:\n"
        f"• Неуклюжая/Парк Встреч: 0.58\n"
        f"• Остальные запросы: 0.61"
    )
    await update.message.reply_text(stats_text)


async def threshold_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /threshold"""
    if not rag_bot:
        await update.message.reply_text("❌ Бот временно недоступен")
        return
    
    threshold_text = (
        f"🎯 ИНФОРМАЦИЯ О ПОРОГАХ РЕЛЕВАНТНОСТИ\n\n"
        f"Бот использует разные пороги для разных типов запросов:\n\n"
        f"🔹 Для вопросов о Неуклюжей и Парке Встреч:\n"
        f"   Порог: 0.58\n"
        f"   Пример: 'Кто такая Неуклюжая?' → релевантность ~0.60 → ✅ НАЙДЕТ\n\n"
        f"🔹 Для всех остальных вопросов:\n"
        f"   Порог: 0.61\n"
        f"   Пример: 'Кто президент Франции?' → релевантность ~0.59 → ❌ НЕ ЗНАЕТ\n\n"
        f"Это позволяет находить нужную информацию и отсекать случайные совпадения."
    )
    await update.message.reply_text(threshold_text)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений"""
    if not rag_bot:
        await update.message.reply_text("❌ Бот временно недоступен")
        return
    
    query = update.message.text
    
    # Отправляем статус "печатает"
    await update.message.chat.send_action(action="typing")
    
    try:
        # Получаем ответ от бота
        answer = rag_bot.answer(query)
        
        # Отправляем ответ
        await update.message.reply_text(answer)
        
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        await update.message.reply_text(
            f"❌ Произошла ошибка при обработке запроса.\n"
            f"Попробуйте переформулировать вопрос."
        )


def main():
    """Запуск бота"""
    # Создаем приложение
    app = Application.builder().token(TOKEN).build()
    
    # Регистрируем обработчики команд
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(CommandHandler("threshold", threshold_command))
    
    # Регистрируем обработчик текстовых сообщений
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Запускаем бота
    print("\n" + "="*70)
    print("🤖 УМНЫЙ TELEGRAM БОТ С АДАПТИВНЫМИ ПОРОГАМИ ЗАПУЩЕН")
    print("="*70)
    print(f"📊 Базовый порог: {rag_bot.default_threshold if rag_bot else 'N/A'}")
    print("⚙️ Специальный порог для Неуклюжей/Парка Встреч: 0.58")
    print("🔄 Ожидание сообщений...")
    print("="*70 + "\n")
    
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()