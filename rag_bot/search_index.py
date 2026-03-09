import os
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any

# Правильные импорты для новых версий LangChain
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.vectorstores import Chroma
from langchain.schema import Document

import warnings
warnings.filterwarnings('ignore')


class KnowledgeBaseSearcher:
    """
    Класс для поиска по векторному индексу
    """
    
    def __init__(self, index_path: str, index_type: str = 'faiss'):
        """
        Инициализация поисковика
        
        :param index_path: путь к индексу
        :param index_type: тип индекса
        """
        self.index_path = index_path
        self.index_type = index_type
        self.vector_store = None
        self.metadata = self._load_metadata()
        
        self._load_index()
    
    def _load_metadata(self):
        """
        Загрузка метаданных индекса
        """
        metadata_path = os.path.join(os.path.dirname(self.index_path), 'index_metadata.json')
        
        if os.path.exists(metadata_path):
            try:
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _load_index(self):
        """
        Загрузка индекса
        """
        print(f"🔄 Загрузка индекса из: {self.index_path}")
        
        # Загружаем модель эмбеддингов
        model_name = self.metadata.get('embedding_model', 'sentence-transformers/all-MiniLM-L6-v2')
        
        print(f"   Используемая модель: {model_name}")
        
        embeddings = HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        
        # Загружаем индекс
        try:
            if self.index_type == 'faiss':
                # Для FAISS нужно передавать embeddings при загрузке
                self.vector_store = FAISS.load_local(
                    self.index_path, 
                    embeddings,
                    allow_dangerous_deserialization=True  # Важно для новых версий
                )
            elif self.index_type == 'chroma':
                self.vector_store = Chroma(
                    persist_directory=self.index_path,
                    embedding_function=embeddings
                )
            else:
                raise ValueError(f"Неподдерживаемый тип индекса: {self.index_type}")
            
            print("✅ Индекс загружен успешно")
            
        except Exception as e:
            print(f"❌ Ошибка при загрузке индекса: {e}")
            raise
        
        if self.metadata:
            print(f"   Модель: {self.metadata.get('embedding_model', 'unknown')}")
            print(f"   Чанков: {self.metadata.get('total_chunks', 'unknown')}")
    
    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        Поиск по запросу
        
        :param query: поисковый запрос
        :param k: количество результатов
        :return: список результатов
        """
        if self.vector_store is None:
            raise ValueError("Индекс не загружен")
        
        # Выполняем поиск
        results = self.vector_store.similarity_search_with_score(query, k=k)
        
        formatted_results = []
        for doc, score in results:
            # Конвертируем расстояние в релевантность (1 - score для нормализованных векторов)
            relevance = float(1 - score) if score <= 1 else float(1 / (1 + score))
            
            formatted_results.append({
                'text': doc.page_content,
                'source': doc.metadata.get('relative_path', doc.metadata.get('source', 'unknown')),
                'filename': doc.metadata.get('filename', 'unknown'),
                'chunk_id': doc.metadata.get('chunk_id', 'unknown'),
                'relevance': relevance,
                'score': float(score)
            })
        
        return formatted_results
    
    def print_results(self, results: List[Dict[str, Any]], query: str):
        """
        Красивый вывод результатов
        
        :param results: результаты поиска
        :param query: исходный запрос
        """
        print("\n" + "="*80)
        print(f"🔍 ЗАПРОС: {query}")
        print("="*80)
        
        if not results:
            print("\n❌ Ничего не найдено")
            return
        
        for i, result in enumerate(results):
            print(f"\n📌 РЕЗУЛЬТАТ {i+1} (релевантность: {result['relevance']:.4f})")
            print(f"📁 Источник: {result['source']}")
            print(f"📄 Текст: {result['text'][:300]}...")


def test_searcher():
    """
    Тестовая функция для проверки поисковика
    """
    index_path = "./vector_index/faiss_index"
    
    if not os.path.exists(index_path):
        print(f"❌ Индекс не найден по пути: {index_path}")
        print("   Сначала создайте индекс с помощью build_index.py")
        return
    
    try:
        searcher = KnowledgeBaseSearcher(index_path, 'faiss')
        
        # Тестовые запросы
        test_queries = [
            "Аннушка и масло на Патриарших прудах",
            "Воланд и его свита",
            "Мастер и его роман",
            "Берлиоз и трамвай",
            "Нехорошая квартира"
        ]
        
        for query in test_queries:
            try:
                results = searcher.search(query, k=3)
                searcher.print_results(results, query)
            except Exception as e:
                print(f"❌ Ошибка при поиске '{query}': {e}")
                
    except Exception as e:
        print(f"❌ Ошибка при инициализации поисковика: {e}")


def main():
    parser = argparse.ArgumentParser(description='Поиск по векторному индексу')
    parser.add_argument('query', type=str, nargs='?', help='Поисковый запрос')
    parser.add_argument('--index', type=str, default='./vector_index/faiss_index', 
                       help='Путь к индексу')
    parser.add_argument('--type', type=str, default='faiss', choices=['faiss', 'chroma'],
                       help='Тип индекса')
    parser.add_argument('--k', type=int, default=5, help='Количество результатов')
    
    args = parser.parse_args()
    
    # Если запрос не указан, запускаем тестовый режим
    if not args.query:
        print("🔍 Запуск в тестовом режиме...")
        test_searcher()
        return
    
    # Проверяем существование индекса
    if not os.path.exists(args.index):
        print(f"❌ Индекс не найден по пути: {args.index}")
        print("   Убедитесь, что путь указан правильно")
        return
    
    try:
        searcher = KnowledgeBaseSearcher(args.index, args.type)
        results = searcher.search(args.query, args.k)
        searcher.print_results(results, args.query)
        
        # Сохраняем результаты в файл
        output_file = f"search_results_{args.query[:20].replace(' ', '_')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'query': args.query,
                'results': results
            }, f, ensure_ascii=False, indent=2)
        print(f"\n✅ Результаты сохранены в {output_file}")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")


if __name__ == "__main__":
    main()