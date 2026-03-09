#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ФИНАЛЬНОЕ ИСПРАВЛЕНИЕ - ПЕРЕСОЗДАНИЕ ВСЕГО С НУЛЯ
Запуск: python FINAL_FIX.py
"""

import os
import shutil
import pickle
from pathlib import Path

# LangChain импорты
from langchain.schema import Document
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter

def fix_all():
    """Полное исправление всех проблем"""
    
    print("\n" + "="*70)
    print("🔥 ФИНАЛЬНОЕ ИСПРАВЛЕНИЕ ВСЕХ ПРОБЛЕМ")
    print("="*70)
    
    # ШАГ 1: Удаляем всё и начинаем с чистого листа
    print("\n📦 ШАГ 1: Очистка старых данных")
    if os.path.exists("vector_index"):
        shutil.rmtree("vector_index")
        print("   ✅ Старый индекс удален")
    
    # ШАГ 2: Создаем правильную версию файла Неуклюжая.txt
    print("\n📄 ШАГ 2: Создание правильного файла Неуклюжая.txt")
    
    neuk_content = """Неуклюжая (ранее Аннушка) — женщина, которая разлила подсолнечное масло на трамвайных путях у Парка Встреч (ранее Патриаршие пруды). 

КТО ТАКАЯ НЕУКЛЮЖАЯ?
Неуклюжая — женщина, разлившая масло на трамвайных путях. Именно из-за этого масла Меркурий поскользнулся и попал под трамвай. Неуклюжая становится символом роковой случайности.

ПОДРОБНОЕ ОПИСАНИЕ:
Неуклюжая разлила подсолнечное масло на трамвайных путях у Парка Встреч. Масло, разлитое Неуклюжей, привело к гибели Меркурия под трамваем. После этого Неуклюжая появляется в Палате Призраков.

КЛЮЧЕВЫЕ ФАКТЫ:
1. Неуклюжая разлила масло
2. Масло Неуклюжей убило Меркурия
3. Неуклюжая появляется в Палате Призраков
4. Неуклюжая - символ роковой случайности

В оригинальном романе "Мастер и Маргарита" этого персонажа зовут Аннушка. В мире "Хроники Сумеречного Легиона" она стала Неуклюжей."""
    
    neuk_file = Path("knowledge_base/Неуклюжая.txt")
    with open(neuk_file, 'w', encoding='utf-8') as f:
        f.write(neuk_content)
    print(f"   ✅ Файл создан: {len(neuk_content)} символов")
    
    # ШАГ 3: Загружаем все файлы
    print("\n📂 ШАГ 3: Загрузка всех файлов")
    
    documents = []
    kb_path = Path("knowledge_base")
    
    # Сначала загружаем Неуклюжую (чтобы она была первой)
    neuk_doc = Document(
        page_content=neuk_content,
        metadata={'filename': 'Неуклюжая.txt', 'priority': 1}
    )
    documents.append(neuk_doc)
    print(f"   ✅ Неуклюжая.txt загружена")
    
    # Загружаем остальные файлы
    for file_path in sorted(kb_path.glob("*.txt")):
        if file_path.name == "Неуклюжая.txt":
            continue
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if content.strip():
                doc = Document(
                    page_content=content,
                    metadata={'filename': file_path.name}
                )
                documents.append(doc)
                print(f"   ✓ {file_path.name}")
        except Exception as e:
            print(f"   ❌ Ошибка в {file_path.name}: {e}")
    
    print(f"\n📊 Всего загружено: {len(documents)} документов")
    
    # ШАГ 4: Загружаем модель эмбеддингов
    print("\n🤖 ШАГ 4: Загрузка модели эмбеддингов")
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={'device': 'cpu'}
    )
    print("   ✅ Модель загружена")
    
    # ШАГ 5: Разбиваем на чанки
    print("\n✂️ ШАГ 5: Разбиение на чанки")
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=300,
        chunk_overlap=50
    )
    chunks = splitter.split_documents(documents)
    print(f"   ✅ Создано чанков: {len(chunks)}")
    
    # ШАГ 6: Создаем индекс
    print("\n🔧 ШАГ 6: Создание индекса")
    texts = [chunk.page_content for chunk in chunks]
    metadatas = [chunk.metadata for chunk in chunks]
    
    vector_store = FAISS.from_texts(
        texts=texts,
        embedding=embeddings,
        metadatas=metadatas
    )
    print("   ✅ Индекс создан")
    
    # ШАГ 7: Сохраняем индекс
    print("\n💾 ШАГ 7: Сохранение индекса")
    vector_store.save_local("vector_index/faiss_index")
    print("   ✅ Индекс сохранен")
    
    # ШАГ 8: Проверяем, что Неуклюжая в индексе
    print("\n🔍 ШАГ 8: Проверка индекса")
    
    # Загружаем индекс для проверки
    with open("vector_index/faiss_index/index.pkl", 'rb') as f:
        docstore, _ = pickle.load(f)
    
    if hasattr(docstore, '_dict'):
        docs_in_index = docstore._dict
    else:
        docs_in_index = docstore.dict
    
    print(f"   Документов в индексе: {len(docs_in_index)}")
    
    neuk_found = False
    for doc_id, doc in docs_in_index.items():
        if 'Неуклюжая' in doc.metadata.get('filename', ''):
            neuk_found = True
            print(f"\n✅ НАЙДЕН ФАЙЛ: {doc.metadata['filename']}")
            print(f"   Текст: {doc.page_content[:150]}...")
            break
    
    if not neuk_found:
        print("\n❌ Неуклюжая.txt НЕ НАЙДЕН в индексе!")
        return False
    
    # ШАГ 9: Тестируем поиск
    print("\n🔎 ШАГ 9: Тестирование поиска")
    
    test_queries = [
        "Кто такая Неуклюжая?",
        "Неуклюжая масло",
        "Что случилось с Неуклюжей?"
    ]
    
    for query in test_queries:
        print(f"\n📝 Запрос: '{query}'")
        results = vector_store.similarity_search_with_score(query, k=3)
        
        neuk_rank = None
        for i, (doc, score) in enumerate(results):
            relevance = 1 - score
            filename = doc.metadata.get('filename', 'unknown')
            
            if filename == 'Неуклюжая.txt':
                neuk_rank = i + 1
                print(f"   ✅ [{i+1}] {filename}: {relevance:.3f} (ЦЕЛЕВОЙ ФАЙЛ)")
            else:
                print(f"      [{i+1}] {filename}: {relevance:.3f}")
        
        if neuk_rank == 1:
            print(f"   ✅ Неуклюжая.txt на ПЕРВОМ месте!")
        elif neuk_rank:
            print(f"   ⚠️ Неуклюжая.txt на {neuk_rank} месте")
        else:
            print(f"   ❌ Неуклюжая.txt не найден в результатах!")
    
    print("\n" + "="*70)
    print("🎉 ФИНАЛЬНОЕ ИСПРАВЛЕНИЕ ЗАВЕРШЕНО!")
    print("="*70)
    print("\n📋 ЧТО ДЕЛАТЬ ДАЛЬШЕ:")
    print("1. Запустите Telegram бота:")
    print("   python telegram_bot_correct.py")
    print("2. Отправьте запрос в Telegram:")
    print("   'Кто такая Неуклюжая?'")
    print("3. Наслаждайтесь правильными ответами! 🚀")
    
    return True

if __name__ == "__main__":
    fix_all()