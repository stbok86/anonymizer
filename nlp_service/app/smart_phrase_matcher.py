#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Умный PhraseMatcher с приоритизацией по длине и расширением совпадений
"""

from typing import List, Dict, Any, Set, Tuple, Optional
from spacy.matcher import PhraseMatcher
from spacy.tokens import Doc, Span
from collections import defaultdict
import re


class SmartPhraseMatch:
    """Класс для хранения информации о совпадении с дополнительными метаданными"""
    
    def __init__(self, start: int, end: int, text: str, pattern_id: str, 
                 confidence: float = 1.0, is_partial: bool = False):
        self.start = start
        self.end = end
        self.text = text
        self.pattern_id = pattern_id
        self.confidence = confidence
        self.is_partial = is_partial
        self.length = len(text.split())
        
    def overlaps_with(self, other: 'SmartPhraseMatch') -> bool:
        """Проверяет пересечение с другим совпадением"""
        return (self.start < other.end and self.end > other.start)
    
    def contains(self, other: 'SmartPhraseMatch') -> bool:
        """Проверяет, содержит ли это совпадение другое"""
        return (self.start <= other.start and self.end >= other.end)
    
    def is_extension_of(self, other: 'SmartPhraseMatch') -> bool:
        """Проверяет, является ли это совпадение расширением другого"""
        # Если одно совпадение полностью содержит другое и начинается в той же позиции
        return (self.start == other.start and self.end > other.end) or \
               (self.end == other.end and self.start < other.start) or \
               (self.start <= other.start and self.end >= other.end and self.length > other.length)


class SmartPhraseMatcher:
    """
    Умный PhraseMatcher с приоритизацией по длине фраз
    и интеллектуальным объединением совпадений
    """
    
    def __init__(self, nlp, patterns_dict: Dict[str, List[str]], category: str = "default"):
        self.nlp = nlp
        self.category = category
        self.patterns_dict = patterns_dict
        
        # Создаем отдельные матчеры для разных длин фраз
        self.matchers_by_length = {}
        self.pattern_metadata = {}  # Метаданные о паттернах
        
        self._build_prioritized_matchers()
    
    def _build_prioritized_matchers(self):
        """Строит матчеры, приоритизированные по длине фраз"""
        
        # Группируем паттерны по длине
        patterns_by_length = defaultdict(list)
        
        for pattern_list in self.patterns_dict.values():
            for pattern in pattern_list:
                # Нормализуем и подсчитываем длину
                normalized_pattern = self._normalize_pattern(pattern)
                pattern_length = len(normalized_pattern.split())
                
                patterns_by_length[pattern_length].append({
                    'original': pattern,
                    'normalized': normalized_pattern,
                    'length': pattern_length
                })
                
                # Сохраняем метаданные
                self.pattern_metadata[pattern] = {
                    'length': pattern_length,
                    'is_partial': self._is_likely_partial(pattern, pattern_length)
                }
        
        # Создаем отдельные матчеры для каждой длины (от длинных к коротким)
        for length in sorted(patterns_by_length.keys(), reverse=True):
            matcher = PhraseMatcher(self.nlp.vocab, attr="LOWER")
            
            patterns_for_length = patterns_by_length[length]
            pattern_docs = []
            pattern_labels = []
            
            for i, pattern_info in enumerate(patterns_for_length):
                pattern_text = pattern_info['normalized']
                label = f"{self.category}_{length}_{i}"
                
                try:
                    pattern_doc = self.nlp(pattern_text)
                    if len(pattern_doc) > 0:  # Проверяем, что паттерн не пустой
                        pattern_docs.append(pattern_doc)
                        pattern_labels.append(label)
                        
                        # Связываем label с оригинальным паттерном
                        self.pattern_metadata[label] = {
                            'original_pattern': pattern_info['original'],
                            'length': length,
                            'is_partial': pattern_info.get('is_partial', False)
                        }
                except Exception as e:
                    print(f"⚠️ Ошибка при создании паттерна '{pattern_text}': {e}")
                    continue
            
            if pattern_docs:
                matcher.add(f"{self.category}_length_{length}", pattern_docs, on_match=None)
                self.matchers_by_length[length] = {
                    'matcher': matcher,
                    'labels': pattern_labels,
                    'patterns': patterns_for_length
                }
    
    def _normalize_pattern(self, pattern: str) -> str:
        """Нормализует паттерн для матчинга"""
        # Приводим к нижнему регистру и убираем лишние пробелы
        normalized = re.sub(r'\s+', ' ', pattern.lower().strip())
        return normalized
    
    def _is_likely_partial(self, pattern: str, length: int) -> bool:
        """Определяет, является ли паттерн частичным"""
        # Эвристики для определения частичных названий
        if length < 3:
            return True
        
        partial_endings = [
            'министерство', 'департамент', 'управление', 'развития', 
            'связи', 'образования', 'науки', 'здравоохранения'
        ]
        
        words = pattern.lower().split()
        last_word = words[-1] if words else ""
        
        # Если заканчивается на типичные "частичные" слова и коротко
        return length <= 4 and last_word in partial_endings
    
    def find_matches(self, doc: Doc) -> List[SmartPhraseMatch]:
        """
        Находит совпадения с приоритизацией по длине
        
        Args:
            doc: spaCy документ для поиска
            
        Returns:
            Список умных совпадений, отсортированный по приоритету
        """
        all_matches = []
        
        # Ищем совпадения от длинных к коротким фразам
        for length in sorted(self.matchers_by_length.keys(), reverse=True):
            matcher_info = self.matchers_by_length[length]
            matcher = matcher_info['matcher']
            
            try:
                matches = matcher(doc)
                
                for match_id, start, end in matches:
                    # Получаем информацию о совпадении
                    span = doc[start:end]
                    match_text = span.text
                    
                    # Находим соответствующий оригинальный паттерн
                    label_name = self.nlp.vocab.strings[match_id]
                    metadata = self.pattern_metadata.get(label_name, {})
                    
                    # Создаем умное совпадение
                    smart_match = SmartPhraseMatch(
                        start=span.start_char,
                        end=span.end_char,
                        text=match_text,
                        pattern_id=metadata.get('original_pattern', match_text),
                        confidence=self._calculate_confidence(metadata, length),
                        is_partial=metadata.get('is_partial', False)
                    )
                    
                    all_matches.append(smart_match)
                    
            except Exception as e:
                print(f"⚠️ Ошибка при поиске совпадений длины {length}: {e}")
                continue
        
        # Фильтруем и объединяем совпадения
        return self._merge_overlapping_matches(all_matches)
    
    def _calculate_confidence(self, metadata: Dict, length: int) -> float:
        """Вычисляет confidence на основе метаданных"""
        base_confidence = 0.95
        
        # Бонус за длину
        length_bonus = min(0.04, length * 0.01)
        
        # Штраф за частичность
        partial_penalty = 0.1 if metadata.get('is_partial', False) else 0
        
        return min(0.99, base_confidence + length_bonus - partial_penalty)
    
    def _merge_overlapping_matches(self, matches: List[SmartPhraseMatch]) -> List[SmartPhraseMatch]:
        """
        Объединяет перекрывающиеся совпадения, предпочитая более длинные и точные
        
        Args:
            matches: Список всех найденных совпадений
            
        Returns:
            Список объединенных совпадений без перекрытий
        """
        if not matches:
            return []
        
        # Сортируем по приоритету: длина -> confidence -> позиция
        matches.sort(key=lambda m: (-m.length, -m.confidence, m.start))
        
        merged_matches = []
        
        for match in matches:
            # Проверяем, не перекрывается ли с уже добавленными совпадениями
            should_add = True
            to_remove = []
            
            for i, existing_match in enumerate(merged_matches):
                if match.overlaps_with(existing_match):
                    # Если новое совпадение лучше (длиннее или точнее)
                    if (match.length > existing_match.length or 
                        (match.length == existing_match.length and match.confidence > existing_match.confidence)):
                        # Заменяем существующее
                        to_remove.append(i)
                    else:
                        # Не добавляем новое
                        should_add = False
                        break
            
            # Удаляем замененные совпадения
            for i in reversed(to_remove):
                del merged_matches[i]
            
            # Добавляем новое совпадение, если нужно
            if should_add:
                merged_matches.append(match)
        
        # Финальная сортировка по позиции
        merged_matches.sort(key=lambda m: m.start)
        
        return merged_matches
    
    def convert_to_detections(self, matches: List[SmartPhraseMatch], 
                            category: str, method: str = "smart_phrase_matcher") -> List[Dict[str, Any]]:
        """
        Конвертирует SmartPhraseMatch в стандартный формат детекций
        
        Args:
            matches: Список умных совпадений
            category: Категория детекций
            method: Метод детекции
            
        Returns:
            Список детекций в стандартном формате
        """
        detections = []
        
        for match in matches:
            detection = {
                'original_value': match.text,
                'position': {
                    'start': match.start,
                    'end': match.end
                },
                'confidence': match.confidence,
                'category': category,
                'method': method,
                'additional_info': {
                    'pattern_matched': match.pattern_id,
                    'phrase_length': match.length,
                    'is_partial_match': match.is_partial,
                    'smart_match': True
                }
            }
            
            detections.append(detection)
        
        return detections