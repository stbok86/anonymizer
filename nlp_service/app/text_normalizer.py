#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Улучшенная обработка текста для PhraseMatcher
Решает проблему с переносами строк и неполными совпадениями
"""

import re
from typing import List, Dict, Any
from spacy.tokens import Doc

class TextNormalizer:
    """Класс для нормализации текста перед PhraseMatcher"""
    
    def __init__(self, normalization_patterns=None):
        # Паттерны для нормализации теперь берём только из nlp_patterns.json
        if normalization_patterns is not None:
            self.normalization_patterns = normalization_patterns
        else:
            from nlp_config import NLPConfig
            config = NLPConfig()
            self.normalization_patterns = config.get_normalization_patterns()
    
    def normalize_text(self, text: str) -> str:
        """
        Нормализует текст для лучшего сопоставления с PhraseMatcher
        
        Args:
            text: Исходный текст
            
        Returns:
            Нормализованный текст
        """
        normalized = text
        
        # Применяем паттерны нормализации
        for pattern, replacement in self.normalization_patterns:
            normalized = re.sub(pattern, replacement, normalized)
        
        return normalized
    
    def create_text_variants(self, text: str) -> List[str]:
        """
        Создает варианты текста для лучшего сопоставления
        
        Args:
            text: Исходный текст
            
        Returns:
            Список вариантов текста
        """
        variants = []
        
        # Оригинальный текст
        variants.append(text)
        
        # Нормализованный текст
        normalized = self.normalize_text(text)
        if normalized != text:
            variants.append(normalized)
        
        # Текст в верхнем регистре
        upper_text = text.upper()
        if upper_text not in variants:
            variants.append(upper_text)
            
        # Нормализованный текст в верхнем регистре
        normalized_upper = self.normalize_text(upper_text)
        if normalized_upper not in variants:
            variants.append(normalized_upper)
        
        return list(set(variants))  # Убираем дубликаты


class PartialMatchPostProcessor:
    """Класс для постобработки частичных совпадений PhraseMatcher"""
    
    def __init__(self, government_organizations: List[str]):
        self.government_organizations = government_organizations
        # Создаем маппинг коротких фраз к длинным
        self.short_to_long_mapping = self._build_mapping()
    
    def _build_mapping(self) -> Dict[str, List[str]]:
        """Строит маппинг коротких фраз к полным названиям"""
        mapping = {}
        
        for full_org in self.government_organizations:
            # Создаем короткие варианты
            words = full_org.lower().split()
            
            # Варианты с разным количеством слов
            for i in range(3, len(words)):  # Минимум 3 слова
                short_variant = ' '.join(words[:i])
                
                if short_variant not in mapping:
                    mapping[short_variant] = []
                
                # Добавляем полное название, если оно длиннее
                if len(full_org.split()) > len(short_variant.split()):
                    mapping[short_variant].append(full_org)
        
        return mapping
    
    def extend_partial_matches(self, matches: List[Dict[str, Any]], doc: Doc) -> List[Dict[str, Any]]:
        """
        Расширяет частичные совпадения до полных названий
        
        Args:
            matches: Список найденных совпадений
            doc: spaCy документ
            
        Returns:
            Расширенный список совпадений
        """
        extended_matches = []
        processed_positions = set()
        
        for match in matches:
            original_value = match['original_value'].lower()
            start_pos = match['position']['start']
            
            # Пропускаем уже обработанные позиции
            if start_pos in processed_positions:
                continue
            
            # Ищем возможные расширения
            extended_match = self._try_extend_match(match, doc, original_value)
            extended_matches.append(extended_match)
            
            # Отмечаем позицию как обработанную
            processed_positions.add(start_pos)
        
        return extended_matches
    
    def _try_extend_match(self, match: Dict[str, Any], doc: Doc, original_value: str) -> Dict[str, Any]:
        """Пытается расширить частичное совпадение"""
        
        # Проверяем, есть ли маппинг для этой фразы
        if original_value in self.short_to_long_mapping:
            possible_extensions = self.short_to_long_mapping[original_value]
            
            # Ищем лучшее расширение в контексте
            best_extension = self._find_best_extension(match, doc, possible_extensions)
            
            if best_extension:
                # Создаем расширенное совпадение
                extended_match = match.copy()
                extended_match['original_value'] = best_extension
                extended_match['confidence'] = min(match['confidence'] + 0.05, 0.99)  # Небольшой бонус
                extended_match['method'] = f"{match['method']}_extended"
                extended_match['extended_from'] = match['original_value']
                
                return extended_match
        
        return match
    
    def _find_best_extension(self, match: Dict[str, Any], doc: Doc, candidates: List[str]) -> str:
        """Находит лучшее расширение среди кандидатов"""
        
        start_char = match['position']['start']
        end_char = match['position']['end']
        
        # Получаем контекст вокруг совпадения
        context_start = max(0, start_char - 100)
        context_end = min(len(doc.text), end_char + 100)
        context = doc.text[context_start:context_end].lower()
        
        # Ищем кандидата, который лучше всего совпадает с контекстом
        best_candidate = None
        best_score = 0
        
        for candidate in candidates:
            # Подсчитываем количество слов кандидата, найденных в контексте
            candidate_words = candidate.lower().split()
            found_words = sum(1 for word in candidate_words if word in context)
            score = found_words / len(candidate_words)
            
            if score > best_score and score > 0.7:  # Минимум 70% слов должно быть в контексте
                best_score = score
                best_candidate = candidate
        
        return best_candidate