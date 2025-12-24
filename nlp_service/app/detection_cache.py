#!/usr/bin/env python3
"""
Интеллектуальное кеширование детекций для NLP Service
"""

import hashlib
from typing import List, Dict, Any, Optional
from collections import OrderedDict
import time


class DetectionCache:
    """
    LRU кеш для результатов детекции с учетом схожести текстов
    """
    
    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600):
        """
        Args:
            max_size: Максимальный размер кеша
            ttl_seconds: Время жизни записи в секундах (по умолчанию 1 час)
        """
        self.cache = OrderedDict()
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        
        # Статистика
        self.hits = 0
        self.misses = 0
        
    def _get_cache_key(self, text: str) -> str:
        """Вычисляет ключ кеша для текста"""
        # Нормализуем текст для лучшего кеширования
        normalized = text.strip().lower()
        return hashlib.sha256(normalized.encode('utf-8')).hexdigest()
    
    def get(self, text: str) -> Optional[List[Dict[str, Any]]]:
        """
        Получает детекции из кеша
        
        Args:
            text: Текст для поиска
            
        Returns:
            Список детекций или None если не найдено
        """
        key = self._get_cache_key(text)
        
        if key in self.cache:
            entry_data, timestamp = self.cache[key]
            
            # Проверяем TTL
            if time.time() - timestamp > self.ttl_seconds:
                # Запись устарела
                del self.cache[key]
                self.misses += 1
                return None
            
            # Перемещаем в конец (LRU)
            self.cache.move_to_end(key)
            self.hits += 1
            return entry_data
        
        self.misses += 1
        return None
    
    def put(self, text: str, detections: List[Dict[str, Any]]) -> None:
        """
        Сохраняет детекции в кеш
        
        Args:
            text: Текст
            detections: Найденные детекции
        """
        key = self._get_cache_key(text)
        
        # Удаляем самую старую запись если кеш переполнен
        if len(self.cache) >= self.max_size:
            self.cache.popitem(last=False)
        
        self.cache[key] = (detections, time.time())
    
    def clear(self) -> None:
        """Очищает кеш"""
        self.cache.clear()
        self.hits = 0
        self.misses = 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Возвращает статистику кеша"""
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'size': len(self.cache),
            'max_size': self.max_size,
            'hits': self.hits,
            'misses': self.misses,
            'total_requests': total_requests,
            'hit_rate_pct': round(hit_rate, 2)
        }
    
    def cleanup_expired(self) -> int:
        """
        Удаляет устаревшие записи
        
        Returns:
            Количество удаленных записей
        """
        current_time = time.time()
        expired_keys = []
        
        for key, (_, timestamp) in self.cache.items():
            if current_time - timestamp > self.ttl_seconds:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.cache[key]
        
        return len(expired_keys)


class SmartGroupingCache:
    """
    Умное кеширование с группировкой похожих текстов
    """
    
    def __init__(self, max_size: int = 500):
        """
        Args:
            max_size: Максимальный размер кеша
        """
        self.cache = DetectionCache(max_size=max_size)
        self.prefix_index = {}  # Индекс по префиксам для быстрого поиска
        
    def _get_prefix(self, text: str, length: int = 50) -> str:
        """Получает префикс текста для индексирования"""
        return text[:length].strip().lower()
    
    def find_similar(self, text: str, similarity_threshold: float = 0.9) -> Optional[List[Dict[str, Any]]]:
        """
        Ищет похожий текст в кеше
        
        Args:
            text: Текст для поиска
            similarity_threshold: Порог схожести (не используется пока)
            
        Returns:
            Детекции похожего текста или None
        """
        # Сначала пробуем точное совпадение
        detections = self.cache.get(text)
        if detections is not None:
            return detections
        
        # Затем пробуем по префиксу (для очень похожих текстов)
        prefix = self._get_prefix(text)
        if prefix in self.prefix_index:
            cached_text = self.prefix_index[prefix]
            similar_detections = self.cache.get(cached_text)
            if similar_detections is not None:
                return similar_detections
        
        return None
    
    def add(self, text: str, detections: List[Dict[str, Any]]) -> None:
        """
        Добавляет детекции в кеш с индексированием
        
        Args:
            text: Текст
            detections: Найденные детекции
        """
        self.cache.put(text, detections)
        
        # Индексируем по префиксу
        prefix = self._get_prefix(text)
        if prefix not in self.prefix_index:
            self.prefix_index[prefix] = text
    
    def get_stats(self) -> Dict[str, Any]:
        """Возвращает статистику кеша"""
        base_stats = self.cache.get_stats()
        base_stats['prefix_index_size'] = len(self.prefix_index)
        return base_stats
    
    def clear(self) -> None:
        """Очищает кеш и индексы"""
        self.cache.clear()
        self.prefix_index.clear()
