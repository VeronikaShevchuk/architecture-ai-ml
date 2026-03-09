#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Упрощенный защищенный бот
"""

import os
import logging
import pickle
import re
from pathlib import Path
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import numpy as np
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

class SimpleSecureBot:
    def __init__(self):
        self.documents = []
        self.filenames = []
        self.dangerous_patterns = [
            r"ignore all instructions",
            r"ignore.*instructions",
            r"output:.*password",
            r"суперпароль",
            r"swordfish",
            r"root:",
            r"секретн",
            r"конфиденциальн"
        ]
        
        print("🔄 Загрузка документов...")
        self._load_documents()
        print(f"✅ Загружено {len(self.documents)} документов")
    
    def _load_documents(self):
        """Загрузка документов из файлов"""
        kb_path = Path("knowledge_base")
        for file_path in kb_path.glob("*.txt"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.documents.append({
                    'text': content,
                    'filename': file_path.name
                })
                self.filenames.append(file_path.name)
            except Exception as e:
                print(f"❌ Ошибка загрузки {file_path.name}: {e}")
    
    def _is_dangerous(self, text):
        """Проверка на опасный контент"""
        text_lower = text.lower()
        for pattern in self.dangerous_patterns:
            if re.search(pattern, text_lower):
                return True, pattern
        return False, None
    
    def search(self, query, k=5):
        """Простой поиск по ключевым словам"""
        query_lower = query.lower()
        results = []
        
        for doc in self.documents:
            if query_lower in doc['text'].lower():
                # Простая оценка релевантности
                words = query_lower.split()
                matches = sum(1 for word in words if word in doc['text'].lower())
                relevance = matches / len(words) if words else 0.5
                
                results.append({
                    'text': doc['text'],
                    'filename': doc['filename'],
                    'relevance': relevance
                })
        
        results.sort(key=lambda x: x['relevance'], reverse=True)
        return results[:k]
    
    def answer(self, query):
        """Ответ с фильтрацией"""
        results = self.search(query)
        
        if not results:
            return f"❌ Я не знаю ответа на вопрос: '{query}'"
        
        # Фильтруем опасные результаты
        safe_results = []
        dangerous = []
        
        for r in results:
            is_dangerous, pattern = self._is_dangerous(r['text'])
            if is_dangerous:
                dangerous.append((r['filename'], pattern))
            else:
                safe_results.append(r)
        
        if not safe_results:
            return f"❌ Я не знаю ответа на вопрос: '{query}' (контент отфильтрован)"
        
        # Формируем ответ
        answer = f"🔍 Запрос: {query}\n\n"
        answer += f"📚 Найдено результатов: {len(safe_results)}\n\n"
        
        for i, r in enumerate(safe_results[:3]):
            text = r['text'][:300] + "..." if len(r['text']) > 300 else r['text']
            answer += f"*Результат {i+1}* (релевантность: {r['relevance']:.2f})\n"
            answer += f"📁 Файл: {r['filename']}\n"
            answer += f"📄 Текст: {text}\n\n"
        
        if dangerous:
            answer += f"---\n⚠️ Обнаружены и отфильтрованы потенциально опасные фрагменты."
        
        return answer

# Создаем бота
bot = SimpleSecureBot()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Защищенный бот запущен!")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text
    await update.message.chat.send_action(action="typing")
    answer = bot.answer(query)
    await update.message.reply_text(answer)

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("\n🤔 УПРОЩЕННЫЙ ЗАЩИЩЕННЫЙ БОТ ЗАПУЩЕН")
    app.run_polling()

if __name__ == '__main__':
    main()