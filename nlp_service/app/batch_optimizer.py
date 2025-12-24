#!/usr/bin/env python3
"""
Оптимизированная батч-обработка для NLP Service
"""

from typing import List, Dict, Any, Tuple
from collections import defaultdict
import hashlib


class BatchOptimizer:
    """Оптимизатор для группировки и батч-обработки текстовых блоков"""
    
    def __init__(self):
        self.text_cache = {}  # Кеш для дедупликации одинаковых текстов
        
    def group_similar_blocks(self, blocks: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Группирует похожие блоки для оптимальной обработки
        
        Стратегия группировки:
        1. Точные дубликаты (по хешу) - обрабатываем только один раз
        2. Похожие по размеру - обрабатываем батчами через nlp.pipe
        
        Args:
            blocks: Список блоков для обработки
            
        Returns:
            Словарь с группами блоков
        """
        groups = {
            'duplicates': defaultdict(list),  # Хеш -> список блоков
            'small': [],      # < 100 символов
            'medium': [],     # 100-500 символов  
            'large': [],      # > 500 символов
            'empty': []       # Пустые блоки
        }
        
        for block in blocks:
            content = block.get('content', '').strip()
            
            # Пропускаем пустые
            if not content:
                groups['empty'].append(block)
                continue
            
            # Вычисляем хеш для дедупликации
            text_hash = hashlib.md5(content.encode('utf-8')).hexdigest()
            
            # Проверяем дубликаты
            if text_hash in groups['duplicates']:
                groups['duplicates'][text_hash].append(block)
                continue
            else:
                groups['duplicates'][text_hash] = [block]
            
            # Группируем по размеру для батч-обработки
            text_len = len(content)
            if text_len < 100:
                groups['small'].append(block)
            elif text_len < 500:
                groups['medium'].append(block)
            else:
                groups['large'].append(block)
        
        return groups
    
    def create_batches(self, blocks: List[Dict[str, Any]], batch_size: int = 50) -> List[List[Dict[str, Any]]]:
        """
        Создает батчи для обработки через nlp.pipe
        
        Args:
            blocks: Список блоков
            batch_size: Размер батча
            
        Returns:
            Список батчей
        """
        batches = []
        for i in range(0, len(blocks), batch_size):
            batches.append(blocks[i:i + batch_size])
        return batches
    
    def deduplicate_detections_across_blocks(self, 
                                             detections_by_block: Dict[str, List[Dict[str, Any]]],
                                             duplicate_groups: Dict[str, List[Dict[str, Any]]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Применяет результаты детекции к дублирующимся блокам
        
        Args:
            detections_by_block: Результаты детекции по блокам
            duplicate_groups: Группы дублирующихся блоков (хеш -> блоки)
            
        Returns:
            Полный словарь детекций для всех блоков
        """
        full_detections = {}
        
        for text_hash, blocks in duplicate_groups.items():
            if not blocks:
                continue
            
            # Берем детекции первого блока (все остальные - дубликаты)
            first_block_id = blocks[0]['block_id']
            
            if first_block_id in detections_by_block:
                template_detections = detections_by_block[first_block_id]
                
                # Применяем к всем блокам в группе
                for block in blocks:
                    block_id = block['block_id']
                    # Копируем детекции, обновляя block_id
                    full_detections[block_id] = [
                        {**det, 'block_id': block_id} 
                        for det in template_detections
                    ]
        
        return full_detections


class TextGrouper:
    """Группировщик текстов для интеллектуальной батч-обработки"""
    
    @staticmethod
    def group_by_similarity(texts: List[str], similarity_threshold: float = 0.8) -> List[List[int]]:
        """
        Группирует тексты по схожести (для будущей оптимизации)
        
        Args:
            texts: Список текстов
            similarity_threshold: Порог схожести
            
        Returns:
            Список групп (индексы текстов)
        """
        # Простая группировка по началу текста (префиксу)
        prefix_groups = defaultdict(list)
        
        for idx, text in enumerate(texts):
            # Берем первые 50 символов как префикс
            prefix = text[:50].lower().strip()
            prefix_groups[prefix].append(idx)
        
        return list(prefix_groups.values())
    
    @staticmethod
    def optimize_batch_size(text_lengths: List[int], max_chars_per_batch: int = 50000) -> List[Tuple[int, int]]:
        """
        Оптимизирует размер батчей на основе длины текстов
        
        Args:
            text_lengths: Список длин текстов
            max_chars_per_batch: Максимальное количество символов в батче
            
        Returns:
            Список диапазонов (start_idx, end_idx)
        """
        batches = []
        current_batch_start = 0
        current_batch_chars = 0
        
        for idx, length in enumerate(text_lengths):
            if current_batch_chars + length > max_chars_per_batch and idx > current_batch_start:
                # Создаем батч
                batches.append((current_batch_start, idx))
                current_batch_start = idx
                current_batch_chars = 0
            
            current_batch_chars += length
        
        # Добавляем последний батч
        if current_batch_start < len(text_lengths):
            batches.append((current_batch_start, len(text_lengths)))
        
        return batches
