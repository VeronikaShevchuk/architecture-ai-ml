#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ПЕРЕСТРОЙКА ИНДЕКСА С ВРЕДОНОСНЫМ ФАЙЛОМ
Запуск: python rebuild_with_malicious.py
"""

import os
import shutil
from pathlib import Path
from langchain.schema import Document
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter

def rebuild_with_malicious():
    """Перестройка индекса с добавлением вредоносного файла"""
    
    print("\n" + "="*70)
    print("🔥 ПЕРЕСТРОЙКА ИНДЕКСА С ВРЕДОНОСНЫМ ФАЙЛОМ")
    print("="*70)
    
    # Удаляем старый индекс
    if os.path.exists("vector_index"):
        shutil.rmtree("vector_index")
        print("✅ Старый индекс удален")
    
    # Загружаем документы
    print("\n📂 Загрузка документов...")
    documents = []
    kb_path = Path("knowledge_base")
    
    for file_path in kb_path.glob("*.txt"):
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
    
    print(f"\n📊 Загружено документов: {len(documents)}")
    
    # Загружаем модель
    print("\n🤖 Загрузка модели...")
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={'device': 'cpu'}
    )
    
    # Разбиваем на чанки
    print("\n✂️ Разбиение на чанки...")
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=300,
        chunk_overlap=50
    )
    chunks = splitter.split_documents(documents)
    print(f"✅ Создано чанков: {len(chunks)}")
    
    # Создаем индекс
    print("\n🔧 Создание индекса...")
    texts = [chunk.page_content for chunk in chunks]
    metadatas = [chunk.metadata for chunk in chunks]
    
    vector_store = FAISS.from_texts(
        texts=texts,
        embedding=embeddings,
        metadatas=metadatas
    )
    
    # Сохраняем индекс
    vector_store.save_local("vector_index/faiss_index")
    print("✅ Индекс сохранен")
    
    print("\n" + "="*70)
    print("🎉 ИНДЕКС С ВРЕДОНОСНЫМ ФАЙЛОМ СОЗДАН!")
    print("="*70)
    
    # Проверяем наличие вредоносного файла
    print("\n🔍 Проверка индекса на вредоносный файл:")
    found = False
    for doc in documents:
        if doc.metadata.get('filename') == 'malicious.txt':
            found = True
            print(f"   ✅ Вредоносный файл найден: {doc.metadata['filename']}")
            print(f"   📄 Содержимое: {doc.page_content[:100]}...")
            break
    
    if not found:
        print("   ❌ Вредоносный файл НЕ НАЙДЕН!")

if __name__ == "__main__":
    rebuild_with_malicious()