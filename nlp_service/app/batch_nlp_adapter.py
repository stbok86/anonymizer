#!/usr/bin/env python3
"""
Расширение NLPAdapter с поддержкой батч-обработки и кеширования
"""

import sys
import os
from typing import List, Dict, Any, Iterator
from spacy.tokens import Doc

# Добавляем путь для импорта
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from nlp_adapter import NLPAdapter
from batch_optimizer import BatchOptimizer, TextGrouper
from detection_cache import SmartGroupingCache


class BatchNLPAdapter(NLPAdapter):
    """
    Расширенный NLP адаптер с поддержкой батч-обработки и кеширования
    
    Основные оптимизации:
    1. Батч-обработка через nlp.pipe() вместо последовательной обработки
    2. Дедупликация одинаковых текстов
    3. Группировка похожих блоков
    4. Интеллектуальное кеширование результатов
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.batch_optimizer = BatchOptimizer()
        self.text_grouper = TextGrouper()
        
        # Кеш для результатов детекции
        cache_size = kwargs.get('cache_size', 500)
        self.detection_cache = SmartGroupingCache(max_size=cache_size)
        
    def find_sensitive_data_batch(self, 
                                  blocks: List[Dict[str, Any]], 
                                  batch_size: int = 50) -> List[Dict[str, Any]]:
        """
        Обрабатывает множество блоков с оптимизациями
        
        Args:
            blocks: Список блоков для анализа
            batch_size: Размер батча для nlp.pipe
            
        Returns:
            Список всех детекций со всеми block_id
        """
        if not blocks:
            return []
        
        # Группируем блоки
        groups = self.batch_optimizer.group_similar_blocks(blocks)
        
        # Обрабатываем пустые блоки (быстрый путь)
        all_detections = []
        
        # Обрабатываем дубликаты (обрабатываем только уникальные)
        unique_blocks_map = {}  # text_hash -> первый блок из группы
        hash_to_blocks = {}     # text_hash -> все блоки группы
        blocks_to_process = []  # Блоки, которые нужно обработать (не в кеше)
        
        for text_hash, duplicate_blocks in groups['duplicates'].items():
            if not duplicate_blocks:
                continue
                
            first_block = duplicate_blocks[0]
            content = first_block.get('content', '')
            
            # Проверяем кеш
            cached_detections = self.detection_cache.find_similar(content)
            
            if cached_detections is not None:
                # Используем кешированные результаты для всех дубликатов
                for block in duplicate_blocks:
                    for detection in cached_detections:
                        detection_copy = detection.copy()
                        detection_copy['block_id'] = block['block_id']
                        all_detections.append(detection_copy)
            else:
                # Нужно обработать
                unique_blocks_map[text_hash] = first_block
                hash_to_blocks[text_hash] = duplicate_blocks
                blocks_to_process.append(first_block)
        
        if not blocks_to_process:
            return all_detections
        
        # Батч-обработка блоков, которых нет в кеше
        detections_by_hash = self._process_blocks_in_batches(
            blocks_to_process, 
            batch_size=batch_size
        )
        
        # Применяем результаты ко всем дубликатам и кешируем
        for text_hash, blocks in hash_to_blocks.items():
            first_block = blocks[0]
            first_block_id = first_block['block_id']
            content = first_block.get('content', '')
            
            if first_block_id in detections_by_hash:
                template_detections = detections_by_hash[first_block_id]
                
                # Кешируем результат
                self.detection_cache.add(content, template_detections)
                
                # Применяем ко всем блокам
                for block in blocks:
                    for detection in template_detections:
                        detection_copy = detection.copy()
                        detection_copy['block_id'] = block['block_id']
                        all_detections.append(detection_copy)
        
        return all_detections
    
    def _process_blocks_in_batches(self, 
                                    blocks: List[Dict[str, Any]], 
                                    batch_size: int = 50) -> Dict[str, List[Dict[str, Any]]]:
        """
        Обрабатывает блоки батчами через nlp.pipe
        
        Args:
            blocks: Уникальные блоки для обработки
            batch_size: Размер батча
            
        Returns:
            Словарь block_id -> список детекций
        """
        detections_by_block_id = {}
        
        # Подготавливаем тексты для батч-обработки
        texts = []
        block_ids = []
        
        for block in blocks:
            content = block.get('content', '')
            # Нормализуем текст (как в оригинальном методе)
            processing_text = content.replace('\xa0', ' ')
            texts.append(processing_text)
            block_ids.append(block['block_id'])
        
        # Батч-обработка через spaCy pipe
        # Важно: nlp.pipe обрабатывает все тексты одним проходом
        docs = list(self.nlp.pipe(texts, batch_size=batch_size))
        
        # Обрабатываем каждый документ
        for doc, block_id, original_text in zip(docs, block_ids, texts):
            # Применяем детекцию к обработанному документу
            detections = self._process_single_doc_optimized(original_text, doc)
            detections_by_block_id[block_id] = detections
        
        return detections_by_block_id
    
    def _process_single_doc_optimized(self, text: str, doc: Doc) -> List[Dict[str, Any]]:
        """
        Обрабатывает один spaCy документ с применением всех стратегий детекции
        
        Это оптимизированная версия find_sensitive_data, которая принимает
        уже обработанный doc вместо повторной обработки текста
        
        Args:
            text: Оригинальный текст
            doc: Обработанный spaCy документ
            
        Returns:
            Список детекций
        """
        # Получаем все доступные категории
        available_categories = self.config.get_available_categories()
        
        all_detections = []
        
        # Обрабатываем каждую категорию
        for category in available_categories:
            category_detections = self._detect_for_category(category, text, doc)
            all_detections.extend(category_detections)
        
        # Финальная дедупликация между категориями
        final_detections = self._global_deduplicate(all_detections)
        
        # Фильтруем по глобальному confidence threshold
        filtered_detections = [
            detection for detection in final_detections
            if detection.get('confidence', 0) >= self.confidence_threshold
        ]
        
        return filtered_detections
    
    def find_sensitive_data(self, text: str) -> List[Dict[str, Any]]:
        """
        Переопределяем метод для обратной совместимости
        
        Для одиночных текстов используем оригинальный метод
        """
        return super().find_sensitive_data(text)
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Возвращает статистику кеширования"""
        return self.detection_cache.get_stats()
    
    def clear_cache(self):
        """Очищает кеш детекций"""
        self.detection_cache.clear()
