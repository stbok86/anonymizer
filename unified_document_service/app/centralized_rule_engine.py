#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Центральный движок правил для обнаружения чувствительных данных.
Объединяет логику Rule Engine и NLP Service в единую систему.
"""

import re
import uuid
from typing import Dict, List, Any, Optional, Set, Tuple
from enum import Enum
from dataclasses import dataclass
from abc import ABC, abstractmethod


class DetectionMethod(Enum):
    """Методы обнаружения чувствительных данных"""
    REGEX = "regex"
    SPACY_NER = "spacy_ner"
    SPACY_MATCHER = "spacy_matcher"
    PHRASE_MATCHER = "phrase_matcher"
    MORPHOLOGICAL = "morphological"
    CONTEXT_ANALYSIS = "context_analysis"
    CUSTOM_RULE = "custom_rule"


class DataCategory(Enum):
    """Категории чувствительных данных"""
    PERSON_NAME = "person_name"
    ORGANIZATION = "organization"
    POSITION = "position"
    PHONE = "phone"
    EMAIL = "email"
    ADDRESS = "address"
    PASSPORT = "passport"
    INN = "inn"
    SNILS = "snils"
    SALARY = "salary"
    HEALTH_INFO = "health_info"
    TRADE_SECRET = "trade_secret"
    OTHER = "other"


class Priority(Enum):
    """Приоритеты правил обнаружения"""
    CRITICAL = 1    # Максимальная точность (regex, точные совпадения)
    HIGH = 2        # spaCy NER, проверенные алгоритмы
    MEDIUM = 3      # Морфологический анализ
    LOW = 4         # Контекстный анализ, эвристики


@dataclass
class DetectionRule:
    """Правило обнаружения чувствительных данных"""
    id: str
    category: DataCategory
    method: DetectionMethod
    priority: Priority
    pattern: str
    confidence: float
    description: str
    enabled: bool = True
    context_required: bool = False
    validation_func: Optional[str] = None  # Имя функции валидации
    
    def __post_init__(self):
        """Валидация после создания"""
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError(f"Confidence должен быть в диапазоне [0.0, 1.0], получен: {self.confidence}")


@dataclass 
class Detection:
    """Результат обнаружения чувствительных данных"""
    rule_id: str
    category: DataCategory
    method: DetectionMethod
    original_value: str
    confidence: float
    position: Dict[str, int]  # {'start': int, 'end': int}
    uuid: str = None
    context: str = ""
    validation_passed: bool = True
    
    def __post_init__(self):
        """Генерация UUID если не задан"""
        if self.uuid is None:
            self.uuid = str(uuid.uuid4())


class DetectionEngine(ABC):
    """Абстрактный класс для движков обнаружения"""
    
    @abstractmethod
    def detect(self, text: str, rules: List[DetectionRule]) -> List[Detection]:
        """Обнаружение чувствительных данных в тексте"""
        pass
    
    @abstractmethod
    def is_compatible(self, method: DetectionMethod) -> bool:
        """Проверка совместимости с методом обнаружения"""
        pass


class RegexEngine(DetectionEngine):
    """Движок для regex-обнаружения"""
    
    def detect(self, text: str, rules: List[DetectionRule]) -> List[Detection]:
        """Обнаружение через регулярные выражения"""
        detections = []
        
        for rule in rules:
            if not self.is_compatible(rule.method) or not rule.enabled:
                continue
                
            try:
                for match in re.finditer(rule.pattern, text, re.IGNORECASE | re.UNICODE):
                    detection = Detection(
                        rule_id=rule.id,
                        category=rule.category,
                        method=rule.method,
                        original_value=match.group(),
                        confidence=rule.confidence,
                        position={'start': match.start(), 'end': match.end()}
                    )
                    detections.append(detection)
                    
            except re.error as e:
                print(f"❌ Ошибка в regex правиле {rule.id}: {e}")
                continue
                
        return detections
    
    def is_compatible(self, method: DetectionMethod) -> bool:
        """Проверка совместимости с regex методом"""
        return method == DetectionMethod.REGEX


class CentralizedRuleEngine:
    """
    Централизованный движок правил для обнаружения чувствительных данных.
    Координирует работу всех типов детекторов и применяет правила приоритизации.
    """
    
    def __init__(self):
        """Инициализация централизованного движка"""
        self.rules: Dict[str, DetectionRule] = {}
        self.engines: Dict[DetectionMethod, DetectionEngine] = {}
        self.category_priorities: Dict[DataCategory, Priority] = {}
        self.method_weights: Dict[DetectionMethod, float] = {}
        
        # Настройка весов методов по умолчанию
        self._setup_default_weights()
        
        # Регистрация базовых движков
        self._register_default_engines()
    
    def _setup_default_weights(self):
        """Настройка весов методов обнаружения по умолчанию"""
        self.method_weights = {
            DetectionMethod.REGEX: 1.0,                # Максимальная точность
            DetectionMethod.SPACY_NER: 0.9,            # Высокая точность
            DetectionMethod.SPACY_MATCHER: 0.8,        # Высокая точность
            DetectionMethod.PHRASE_MATCHER: 0.7,       # Средняя точность
            DetectionMethod.MORPHOLOGICAL: 0.6,        # Средняя точность
            DetectionMethod.CONTEXT_ANALYSIS: 0.5,     # Низкая точность
            DetectionMethod.CUSTOM_RULE: 0.8           # Зависит от реализации
        }
    
    def _register_default_engines(self):
        """Регистрация базовых движков обнаружения"""
        # Regex движок
        regex_engine = RegexEngine()
        self.engines[DetectionMethod.REGEX] = regex_engine
    
    def register_engine(self, method: DetectionMethod, engine: DetectionEngine):
        """Регистрация движка обнаружения"""
        if not engine.is_compatible(method):
            raise ValueError(f"Движок не совместим с методом {method}")
        self.engines[method] = engine
    
    def add_rule(self, rule: DetectionRule):
        """Добавление правила обнаружения"""
        if rule.method not in self.engines:
            raise ValueError(f"Нет зарегистрированного движка для метода {rule.method}")
        self.rules[rule.id] = rule
    
    def add_rules(self, rules: List[DetectionRule]):
        """Добавление множества правил"""
        for rule in rules:
            self.add_rule(rule)
    
    def remove_rule(self, rule_id: str):
        """Удаление правила"""
        if rule_id in self.rules:
            del self.rules[rule_id]
    
    def enable_rule(self, rule_id: str):
        """Включение правила"""
        if rule_id in self.rules:
            self.rules[rule_id].enabled = True
    
    def disable_rule(self, rule_id: str):
        """Отключение правила"""
        if rule_id in self.rules:
            self.rules[rule_id].enabled = False
    
    def detect_sensitive_data(self, text: str, 
                            categories: Optional[List[DataCategory]] = None,
                            methods: Optional[List[DetectionMethod]] = None,
                            min_confidence: float = 0.0) -> List[Detection]:
        """
        Обнаружение чувствительных данных в тексте
        
        Args:
            text: Текст для анализа
            categories: Фильтр по категориям (если None - все категории)
            methods: Фильтр по методам (если None - все методы)
            min_confidence: Минимальный уровень уверенности
            
        Returns:
            Список обнаружений, отсортированный по приоритету
        """
        if not text or not isinstance(text, str):
            return []
        
        # Фильтруем правила
        filtered_rules = self._filter_rules(categories, methods, min_confidence)
        
        # Группируем правила по методам
        rules_by_method = self._group_rules_by_method(filtered_rules)
        
        # Запускаем обнаружение для каждого метода
        all_detections = []
        for method, method_rules in rules_by_method.items():
            if method in self.engines:
                engine = self.engines[method]
                detections = engine.detect(text, method_rules)
                all_detections.extend(detections)
        
        # Применяем post-processing
        processed_detections = self._post_process_detections(all_detections, text)
        
        return processed_detections
    
    def _filter_rules(self, categories: Optional[List[DataCategory]], 
                     methods: Optional[List[DetectionMethod]],
                     min_confidence: float) -> List[DetectionRule]:
        """Фильтрация правил по критериям"""
        filtered = []
        
        for rule in self.rules.values():
            # Проверка включенности
            if not rule.enabled:
                continue
            
            # Фильтр по категориям
            if categories and rule.category not in categories:
                continue
            
            # Фильтр по методам
            if methods and rule.method not in methods:
                continue
            
            # Фильтр по уверенности
            if rule.confidence < min_confidence:
                continue
            
            filtered.append(rule)
        
        return filtered
    
    def _group_rules_by_method(self, rules: List[DetectionRule]) -> Dict[DetectionMethod, List[DetectionRule]]:
        """Группировка правил по методам обнаружения"""
        groups = {}
        for rule in rules:
            if rule.method not in groups:
                groups[rule.method] = []
            groups[rule.method].append(rule)
        return groups
    
    def _post_process_detections(self, detections: List[Detection], text: str) -> List[Detection]:
        """
        Пост-обработка обнаружений: удаление дубликатов, сортировка, валидация
        """
        # 1. Удаляем дубликаты (перекрывающиеся обнаружения)
        unique_detections = self._remove_overlapping_detections(detections)
        
        # 2. Применяем дополнительную валидацию
        validated_detections = self._validate_detections(unique_detections, text)
        
        # 3. Сортируем по приоритету и уверенности
        sorted_detections = self._sort_detections(validated_detections)
        
        return sorted_detections
    
    def _remove_overlapping_detections(self, detections: List[Detection]) -> List[Detection]:
        """Удаление перекрывающихся обнаружений с учетом приоритета"""
        if not detections:
            return []
        
        # Сортируем по позиции
        sorted_detections = sorted(detections, key=lambda x: (x.position['start'], x.position['end']))
        
        unique_detections = []
        for current in sorted_detections:
            # Проверяем перекрытие с уже добавленными
            overlaps = False
            for existing in unique_detections:
                if self._positions_overlap(current.position, existing.position):
                    # Если есть перекрытие, выбираем лучшее обнаружение
                    if self._is_better_detection(current, existing):
                        unique_detections.remove(existing)
                        unique_detections.append(current)
                    overlaps = True
                    break
            
            if not overlaps:
                unique_detections.append(current)
        
        return unique_detections
    
    def _positions_overlap(self, pos1: Dict[str, int], pos2: Dict[str, int]) -> bool:
        """Проверка перекрытия позиций"""
        return (pos1['start'] < pos2['end'] and pos1['end'] > pos2['start'])
    
    def _is_better_detection(self, det1: Detection, det2: Detection) -> bool:
        """Определение лучшего обнаружения при перекрытии"""
        # Приоритет по методу
        weight1 = self.method_weights.get(det1.method, 0.5)
        weight2 = self.method_weights.get(det2.method, 0.5)
        
        if weight1 != weight2:
            return weight1 > weight2
        
        # При равном приоритете метода - по уверенности
        return det1.confidence > det2.confidence
    
    def _validate_detections(self, detections: List[Detection], text: str) -> List[Detection]:
        """Дополнительная валидация обнаружений"""
        validated = []
        
        for detection in detections:
            # Применяем кастомную валидацию если есть
            rule = self.rules.get(detection.rule_id)
            if rule and rule.validation_func:
                # Здесь можно добавить вызов кастомной функции валидации
                # validation_result = self._call_validation_function(rule.validation_func, detection, text)
                # detection.validation_passed = validation_result
                pass
            
            # Добавляем контекст
            detection.context = self._extract_context(text, detection.position)
            
            validated.append(detection)
        
        return validated
    
    def _extract_context(self, text: str, position: Dict[str, int], window: int = 50) -> str:
        """Извлечение контекста вокруг обнаружения"""
        start = max(0, position['start'] - window)
        end = min(len(text), position['end'] + window)
        return text[start:end].strip()
    
    def _sort_detections(self, detections: List[Detection]) -> List[Detection]:
        """Сортировка обнаружений по приоритету и уверенности"""
        def sort_key(detection):
            weight = self.method_weights.get(detection.method, 0.5)
            return (-weight, -detection.confidence, detection.position['start'])
        
        return sorted(detections, key=sort_key)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Получение статистики по правилам"""
        total_rules = len(self.rules)
        enabled_rules = sum(1 for rule in self.rules.values() if rule.enabled)
        
        method_stats = {}
        category_stats = {}
        
        for rule in self.rules.values():
            # Статистика по методам
            method = rule.method.value
            if method not in method_stats:
                method_stats[method] = 0
            method_stats[method] += 1
            
            # Статистика по категориям
            category = rule.category.value
            if category not in category_stats:
                category_stats[category] = 0
            category_stats[category] += 1
        
        return {
            'total_rules': total_rules,
            'enabled_rules': enabled_rules,
            'disabled_rules': total_rules - enabled_rules,
            'methods': method_stats,
            'categories': category_stats,
            'registered_engines': list(self.engines.keys())
        }


class RuleLoader:
    """Утилитарный класс для загрузки правил из различных источников"""
    
    @staticmethod
    def load_from_excel(file_path: str, engine: CentralizedRuleEngine) -> int:
        """
        Загрузка правил из Excel файла
        
        Args:
            file_path: Путь к Excel файлу
            engine: Экземпляр CentralizedRuleEngine
            
        Returns:
            Количество загруженных правил
        """
        try:
            import pandas as pd
            df = pd.read_excel(file_path)
            
            loaded_count = 0
            for _, row in df.iterrows():
                try:
                    rule = DetectionRule(
                        id=f"{row.get('category', 'unknown')}_{loaded_count}",
                        category=DataCategory(row.get('category', 'other')),
                        method=DetectionMethod(row.get('method', 'regex')),
                        priority=Priority(row.get('priority', 3)),
                        pattern=row['pattern'],
                        confidence=float(row.get('confidence', 0.8)),
                        description=row.get('description', ''),
                        context_required=bool(row.get('context_required', False))
                    )
                    engine.add_rule(rule)
                    loaded_count += 1
                    
                except Exception as e:
                    print(f"❌ Ошибка загрузки правила из строки {loaded_count}: {e}")
                    continue
            
            return loaded_count
            
        except Exception as e:
            print(f"❌ Ошибка загрузки файла {file_path}: {e}")
            return 0