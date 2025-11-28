#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Фабрика методов детекции и стандартизированного создания объектов detection
"""

import uuid
from typing import Dict, List, Any, Optional, Tuple
from abc import ABC, abstractmethod


class DetectionMethodFactory:
    """
    Фабрика для стандартизированного создания объектов detection
    с автоматическим расчетом confidence
    """
    
    def __init__(self, nlp_config):
        """
        Args:
            nlp_config: Экземпляр NLPConfig для доступа к настройкам
        """
        self.config = nlp_config
    
    def create_detection(
        self, 
        method: str, 
        category: str, 
        original_value: str, 
        position: Tuple[int, int], 
        confidence: Optional[float] = None,
        additional_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Создает стандартизированный объект detection
        
        Args:
            method: Метод обнаружения ('spacy_ner', 'regex', etc.)
            category: Категория данных ('person_name', 'organization', etc.)
            original_value: Найденный текст
            position: Позиция в тексте (start, end)
            confidence: Уверенность (если не указана, рассчитывается автоматически)
            additional_info: Дополнительная информация
            
        Returns:
            Стандартизированный объект detection
        """
        # Если confidence не указана, рассчитываем автоматически
        if confidence is None:
            confidence = self._calculate_confidence(method, category, original_value, additional_info)
        
        # Создаем базовый объект
        detection = {
            'category': category,
            'original_value': original_value,
            'confidence': confidence,
            'position': {
                'start': position[0],
                'end': position[1]
            },
            'method': method,
            'uuid': 'placeholder'  # Временный placeholder, UUID будет генерироваться централизованно в FormatterApplier
        }
        
        # Добавляем дополнительную информацию если есть
        if additional_info:
            detection.update(additional_info)
        
        return detection
    
    def _calculate_confidence(
        self, 
        method: str, 
        category: str, 
        original_value: str, 
        additional_info: Optional[Dict[str, Any]] = None
    ) -> float:
        """
        Автоматически рассчитывает confidence на основе метода и контекста
        
        Args:
            method: Метод обнаружения
            category: Категория
            original_value: Найденное значение
            additional_info: Дополнительная информация для расчета
            
        Returns:
            Рассчитанная confidence
        """
        # Получаем базовую confidence из конфигурации
        base_confidence = self.config.get_min_confidence_for_method(category, method)
        
        # Применяем модификаторы в зависимости от метода
        if method == 'spacy_ner':
            return self._calculate_spacy_confidence(category, original_value, base_confidence, additional_info)
        elif method == 'regex':
            return self._calculate_regex_confidence(category, original_value, base_confidence, additional_info)
        elif method == 'morphological':
            return self._calculate_morphological_confidence(category, original_value, base_confidence, additional_info)
        elif method in ['phrase_matcher', 'custom_matcher']:
            return self._calculate_matcher_confidence(category, original_value, base_confidence, additional_info)
        else:
            return base_confidence
    
    def _calculate_spacy_confidence(
        self, 
        category: str, 
        value: str, 
        base_confidence: float, 
        additional_info: Optional[Dict[str, Any]] = None
    ) -> float:
        """Рассчитывает confidence для spaCy NER"""
        confidence = base_confidence
        
        # Учитываем confidence из spaCy модели если доступна
        if additional_info and 'spacy_confidence' in additional_info:
            spacy_conf = additional_info['spacy_confidence']
            confidence = (confidence + spacy_conf) / 2
        
        # Бонус за длину для имен
        if category == 'person_name' and len(value.split()) > 1:
            confidence = min(confidence + 0.1, 1.0)
        
        # Штраф за очень короткие названия организаций
        if category == 'organization' and len(value) < 5:
            confidence = max(confidence - 0.2, 0.1)
        
        return confidence
    
    def _calculate_regex_confidence(
        self, 
        category: str, 
        value: str, 
        base_confidence: float, 
        additional_info: Optional[Dict[str, Any]] = None
    ) -> float:
        """Рассчитывает confidence для regex поиска"""
        confidence = base_confidence
        
        # Учитываем сложность паттерна
        if additional_info and 'pattern_complexity' in additional_info:
            complexity = additional_info['pattern_complexity']
            if complexity > 0.8:
                confidence = min(confidence + 0.15, 1.0)
            elif complexity < 0.3:
                confidence = max(confidence - 0.1, 0.1)
        
        # Учитываем контекст
        if additional_info and 'has_context' in additional_info:
            if additional_info['has_context']:
                confidence = min(confidence + 0.1, 1.0)
        
        return confidence
    
    def _calculate_morphological_confidence(
        self, 
        category: str, 
        value: str, 
        base_confidence: float, 
        additional_info: Optional[Dict[str, Any]] = None
    ) -> float:
        """Рассчитывает confidence для морфологического анализа"""
        confidence = base_confidence
        
        # Бонус за множественные морфологические признаки
        if additional_info and 'morphological_tags' in additional_info:
            tags = additional_info['morphological_tags']
            if len(tags) > 1:
                confidence = min(confidence + 0.1, 1.0)
        
        # Учитываем первую букву для имен
        if category == 'person_name' and value and value[0].isupper():
            confidence = min(confidence + 0.05, 1.0)
        
        return confidence
    
    def _calculate_matcher_confidence(
        self, 
        category: str, 
        value: str, 
        base_confidence: float, 
        additional_info: Optional[Dict[str, Any]] = None
    ) -> float:
        """Рассчитывает confidence для phrase/custom matcher"""
        confidence = base_confidence
        
        # Учитываем точность совпадения
        if additional_info and 'match_accuracy' in additional_info:
            accuracy = additional_info['match_accuracy']
            confidence = (confidence + accuracy) / 2
        
        # Бонус за структурированные паттерны
        if additional_info and 'is_structured' in additional_info:
            if additional_info['is_structured']:
                confidence = min(confidence + 0.1, 1.0)
        
        return confidence
    
    def validate_detection(self, detection: Dict[str, Any]) -> bool:
        """
        Валидирует объект detection на соответствие стандарту
        
        Args:
            detection: Объект для валидации
            
        Returns:
            True если объект валиден
        """
        required_fields = ['category', 'original_value', 'confidence', 'position', 'method', 'uuid']
        
        # Проверяем наличие обязательных полей
        for field in required_fields:
            if field not in detection:
                return False
        
        # Проверяем типы данных
        if not isinstance(detection['confidence'], (int, float)):
            return False
            
        if not (0 <= detection['confidence'] <= 1):
            return False
        
        if not isinstance(detection['position'], dict):
            return False
            
        if 'start' not in detection['position'] or 'end' not in detection['position']:
            return False
        
        # Проверяем логику позиций
        if detection['position']['start'] > detection['position']['end']:
            return False
        
        return True
    
    def enhance_detection_with_context(
        self, 
        detection: Dict[str, Any], 
        full_text: str, 
        context_window: int = None
    ) -> Dict[str, Any]:
        """
        Обогащает detection контекстной информацией
        
        Args:
            detection: Исходный объект detection
            full_text: Полный текст, из которого извлечена детекция
            context_window: Размер окна контекста (если не указан, берется из конфига)
            
        Returns:
            Обогащенный объект detection
        """
        if context_window is None:
            context_window = self.config.get_context_window_size()
        
        start = detection['position']['start']
        end = detection['position']['end']
        
        # Извлекаем контекст
        context_start = max(0, start - context_window)
        context_end = min(len(full_text), end + context_window)
        
        context_before = full_text[context_start:start]
        context_after = full_text[end:context_end]
        
        # Добавляем контекстную информацию
        enhanced_detection = detection.copy()
        enhanced_detection['context'] = {
            'before': context_before,
            'after': context_after,
            'window_size': context_window
        }
        
        return enhanced_detection