#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Гибридная стратегия для детекции государственных организаций
Объединяет Phrase Matcher и spaCy NER для максимальной точности и покрытия
"""

from typing import Dict, List, Any, Optional, Set
import uuid
import re
import os
from dataclasses import dataclass
from collections import defaultdict
from detection_strategies import DetectionStrategy
from text_normalizer import TextNormalizer, PartialMatchPostProcessor


@dataclass
class OrganizationMatch:
    """Класс для хранения информации о найденной организации"""
    text: str
    start: int
    end: int
    method: str
    confidence: float
    organization_type: str  # 'government', 'commercial', 'unknown'
    raw_detection: Dict[str, Any]


class HybridGovernmentStrategy(DetectionStrategy):
    """
    Гибридная стратегия для детекции государственных организаций
    
    Этапы:
    1. Phrase Matcher для известных организаций (быстро, точно)
    2. spaCy NER для дополнительного поиска (находит неизвестные)
    3. Интеллектуальное объединение с фильтрацией и дедупликацией
    """
    
    def __init__(self, config_settings: Dict[str, Any]):
        super().__init__(config_settings)
        
        # Настройки гибридной стратегии
        self.phrase_priority = config_settings.get('phrase_priority', 0.98)
        self.ner_confidence_boost = config_settings.get('ner_confidence_boost', 0.1)
        self.government_keywords = config_settings.get('government_keywords', [
            'министерство', 'департамент', 'управление', 'служба', 'комитет',
            'администрация', 'правительство', 'дума', 'совет', 'федеральный',
            'государственный', 'муниципальный', 'краевой', 'областной'
        ])
        
        # Инициализируем компоненты для работы с текстом
        self.text_normalizer = TextNormalizer()
        
        # Загружаем словарь государственных организаций для постобработки
        try:
            import sys
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'patterns'))
            from government_organizations import GOVERNMENT_ORGANIZATIONS
            self.partial_matcher = PartialMatchPostProcessor(GOVERNMENT_ORGANIZATIONS)
        except ImportError as e:
            print(f"⚠️ Не удалось загрузить словарь государственных организаций: {e}")
            self.partial_matcher = None
        
        # Паттерны для фильтрации false positives
        self.false_positive_patterns = [
            r'^[А-Я]{2,4}$',  # Аббревиатуры типа ТЗ, ЧТЗ
            r'^(система|описание|регламент)',  # Техническая документация
            r'(требования|технический|программный)'  # Техническая терминология
        ]
        
    def combine_results(self, results_by_method: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """
        Реализует трёхэтапную гибридную стратегию
        
        Args:
            results_by_method: Словарь {method_name: [detections]}
            
        Returns:
            Объединенный и отфильтрованный список детекций
        """
        # Этап 1: Phrase Matcher - быстро и точно для известных организаций
        phrase_matches = self._extract_phrase_matches(results_by_method)
        
        # Этап 2: spaCy NER - дополнительный поиск неизвестных организаций
        ner_matches = self._extract_ner_matches(results_by_method)
        
        # Этап 3: Интеллектуальное объединение
        combined_matches = self._intelligent_merge(phrase_matches, ner_matches)
        
        # Конвертируем обратно в стандартный формат
        final_results = self._convert_to_detections(combined_matches)
        
        return final_results
    
    def _extract_phrase_matches(self, results_by_method: Dict[str, List[Dict[str, Any]]]) -> List[OrganizationMatch]:
        """Этап 1: Извлекаем результаты Phrase Matcher с постобработкой"""
        matches = []
        
        for method in ['phrase_matcher', 'context_matcher']:
            if method in results_by_method:
                # Применяем постобработку для расширения частичных совпадений
                processed_detections = self._postprocess_partial_matches(results_by_method[method])
                
                for detection in processed_detections:
                    match = OrganizationMatch(
                        text=detection['original_value'],
                        start=detection['position']['start'],
                        end=detection['position']['end'],
                        method=method,
                        confidence=self.phrase_priority,  # Высокий приоритет для точных совпадений
                        organization_type='government',  # Phrase matcher настроен на госорганы
                        raw_detection=detection
                    )
                    matches.append(match)
        
        return matches
    
    def _extract_ner_matches(self, results_by_method: Dict[str, List[Dict[str, Any]]]) -> List[OrganizationMatch]:
        """Этап 2: Извлекаем результаты spaCy NER с классификацией"""
        matches = []
        
        if 'spacy_ner' in results_by_method:
            for detection in results_by_method['spacy_ner']:
                # Классифицируем тип организации
                org_type = self._classify_organization_type(detection['original_value'])
                
                # Фильтруем false positives
                if self._is_false_positive(detection['original_value']):
                    continue
                
                # Повышаем confidence для государственных организаций
                confidence = detection['confidence']
                if org_type == 'government':
                    confidence = min(0.95, confidence + self.ner_confidence_boost)
                
                match = OrganizationMatch(
                    text=detection['original_value'],
                    start=detection['position']['start'],
                    end=detection['position']['end'],
                    method='spacy_ner',
                    confidence=confidence,
                    organization_type=org_type,
                    raw_detection=detection
                )
                matches.append(match)
        
        return matches
    
    def _classify_organization_type(self, org_text: str) -> str:
        """Классифицирует тип организации на основе текста"""
        org_lower = org_text.lower()
        
        # Проверяем на государственные ключевые слова
        for keyword in self.government_keywords:
            if keyword in org_lower:
                return 'government'
        
        # Проверяем на коммерческие формы
        commercial_indicators = ['ооо', 'ао', 'пао', 'зао', 'ип', 'Ltd', 'Inc']
        for indicator in commercial_indicators:
            if indicator.lower() in org_lower:
                return 'commercial'
        
        return 'unknown'
    
    def _is_false_positive(self, text: str) -> bool:
        """Проверяет, является ли текст ложным срабатыванием"""
        for pattern in self.false_positive_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False
    
    def _intelligent_merge(self, phrase_matches: List[OrganizationMatch], 
                          ner_matches: List[OrganizationMatch]) -> List[OrganizationMatch]:
        """Этап 3: Интеллектуальное объединение результатов"""
        
        # Сначала добавляем все phrase matches (они имеют приоритет)
        final_matches = phrase_matches.copy()
        
        # Добавляем NER matches, которые не пересекаются с phrase matches
        for ner_match in ner_matches:
            if not self._has_overlap_with_existing(ner_match, final_matches):
                final_matches.append(ner_match)
        
        # Сортируем по позиции для стабильности
        final_matches.sort(key=lambda x: x.start)
        
        # Удаляем дубликаты с учетом приоритета методов
        final_matches = self._remove_duplicates_with_priority(final_matches)
        
        return final_matches
    
    def _has_overlap_with_existing(self, new_match: OrganizationMatch, 
                                  existing_matches: List[OrganizationMatch]) -> bool:
        """Проверяет пересечение нового совпадения с существующими"""
        threshold = self.settings.get('overlap_threshold', 0.5)
        
        for existing in existing_matches:
            overlap = self._calculate_overlap(
                {'start': new_match.start, 'end': new_match.end},
                {'start': existing.start, 'end': existing.end}
            )
            if overlap >= threshold:
                return True
        return False
    
    def _remove_duplicates_with_priority(self, matches: List[OrganizationMatch]) -> List[OrganizationMatch]:
        """Удаляет дубликаты с учетом приоритета методов"""
        # Приоритет методов: phrase_matcher > spacy_ner для government
        method_priority = {
            'phrase_matcher': 3,
            'context_matcher': 3, 
            'spacy_ner': 2
        }
        
        # Группируем пересекающиеся совпадения
        groups = []
        used_indices = set()
        
        for i, match in enumerate(matches):
            if i in used_indices:
                continue
                
            group = [match]
            used_indices.add(i)
            
            for j, other_match in enumerate(matches[i+1:], i+1):
                if j in used_indices:
                    continue
                    
                overlap = self._calculate_overlap(
                    {'start': match.start, 'end': match.end},
                    {'start': other_match.start, 'end': other_match.end}
                )
                
                if overlap >= 0.3:  # Более мягкий порог для группировки
                    group.append(other_match)
                    used_indices.add(j)
            
            groups.append(group)
        
        # Выбираем лучшее совпадение из каждой группы
        final_matches = []
        for group in groups:
            # Сортируем по приоритету метода, затем по confidence
            def sort_key(match):
                method_priority_score = method_priority.get(match.method, 1)
                # Для государственных организаций повышаем приоритет
                gov_boost = 0.1 if match.organization_type == 'government' else 0
                return (-method_priority_score, -(match.confidence + gov_boost))
            
            best_match = min(group, key=sort_key)
            final_matches.append(best_match)
        
        return final_matches
    
    def _convert_to_detections(self, matches: List[OrganizationMatch]) -> List[Dict[str, Any]]:
        """Конвертирует OrganizationMatch обратно в стандартный формат детекций"""
        detections = []
        
        for match in matches:
            detection = {
                'original_value': match.text,
                'position': {
                    'start': match.start,
                    'end': match.end
                },
                'confidence': match.confidence,
                'category': 'government_org',
                'method': f"hybrid_{match.method}",
                'uuid': str(uuid.uuid4()),
                'hybrid_info': {
                    'organization_type': match.organization_type,
                    'source_method': match.method,
                    'is_government': match.organization_type == 'government'
                }
            }
            
            # Добавляем дополнительную информацию из оригинальной детекции
            if 'additional_info' in match.raw_detection:
                detection['additional_info'] = match.raw_detection['additional_info']
            
            detections.append(detection)
        
        return detections
    
    def _postprocess_partial_matches(self, detections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Постобработка частичных совпадений для расширения до полных названий
        
        Args:
            detections: Список детекций от Phrase Matcher
            
        Returns:
            Обработанный список детекций с расширенными совпадениями
        """
        if not self.partial_matcher or not detections:
            return detections
        
        try:
            # Используем постпроцессор для расширения частичных совпадений
            # Для этого нужен spaCy документ, но у нас его нет на этом уровне
            # Поэтому делаем простую проверку по длине названий
            
            extended_detections = []
            for detection in detections:
                original_value = detection['original_value']
                
                # Проверяем, может ли это быть частичным совпадением
                if self._is_likely_partial_match(original_value):
                    # Помечаем для дальнейшей обработки
                    detection['requires_extension_check'] = True
                
                extended_detections.append(detection)
            
            return extended_detections
            
        except Exception as e:
            # В случае ошибки возвращаем исходные детекции
            return detections
    
    def _is_likely_partial_match(self, text: str) -> bool:
        """
        Проверяет, может ли текст быть частичным совпадением
        
        Args:
            text: Текст для проверки
            
        Returns:
            True, если текст может быть частичным совпадением
        """
        # Простая эвристика: если название заканчивается определенными словами
        # и имеет менее 6 слов, это может быть частичное совпадение
        words = text.lower().split()
        
        if len(words) >= 6:
            return False  # Длинные названия обычно полные
        
        # Проверяем окончания, характерные для частичных совпадений
        partial_endings = ['министерство', 'департамент', 'управление', 'развития', 'связи']
        last_word = words[-1] if words else ""
        
        return last_word in partial_endings