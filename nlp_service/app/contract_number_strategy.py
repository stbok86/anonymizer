#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Стратегия детекции номеров контрактов и договоров для анонимизации
"""

import re
import uuid
from typing import List, Dict, Any

try:
    from detection_strategies import DetectionStrategy
except ImportError:
    import sys
    import os
    sys.path.append(os.path.dirname(__file__))
    from detection_strategies import DetectionStrategy


class ContractNumberStrategy(DetectionStrategy):
    """Стратегия для детекции номеров государственных контрактов и договоров"""
    
    def __init__(self, config_settings: Dict[str, Any]):
        super().__init__(config_settings)
        self._compile_patterns()
    
    def combine_results(self, results_by_method: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """
        Комбинирует результаты методов детекции контрактов
        Используем стратегию лучшей уверенности
        """
        all_detections = []
        for method_name, detections in results_by_method.items():
            all_detections.extend(detections)
        
        # Удаляем дубликаты и сортируем по уверенности
        unique_detections = self._remove_duplicates(all_detections, threshold=0.7)
        return sorted(unique_detections, key=lambda x: x['confidence'], reverse=True)
        
    def detect_contract_numbers_in_text(self, text: str) -> List[Dict[str, Any]]:
        """
        Основной метод детекции номеров контрактов для внешнего использования
        
        Args:
            text: Текст для анализа
            
        Returns:
            Список найденных номеров контрактов с метаданными
        """
        return self.detect_contract_numbers(text)
        
    def _compile_patterns(self):
        """Компиляция regex паттернов для номеров контрактов"""
        self.contract_patterns = [
            # Государственные контракты с номерами
            {
                'name': 'government_contract_number',
                'pattern': re.compile(
                    r'(?i)(?:государственный\s+)?(?:контракт|договор)(?:\s+от\s+[^№]*?)?\s*№\s*([^\s,.\n]+)',
                    re.UNICODE
                ),
                'confidence': 0.95
            },
            # Номер после знака №
            {
                'name': 'number_sign',
                'pattern': re.compile(
                    r'№\s*([А-Яа-я0-9\-\/ОК]+(?:\-\d{4})?)',
                    re.UNICODE
                ),
                'confidence': 0.8,
                'context_required': ['контракт', 'договор']  # Требуется контекст
            },
            # Номер после слова "номер"
            {
                'name': 'word_number',
                'pattern': re.compile(
                    r'(?i)номер\s+([А-Яа-я0-9\-\/ОК]+(?:\-\d{4})?)',
                    re.UNICODE
                ),
                'confidence': 0.85,
                'context_required': ['контракт', 'договор']
            },
            # Контракт/договор в начале с датой и номером
            {
                'name': 'contract_with_date_number',
                'pattern': re.compile(
                    r'(?i)(?:государственный\s+)?(?:контракт|договор)\s+от\s+\d{1,2}\s+\w+\s+\d{4}\s*г\.?\s*№\s*([^\s,.\n]+)',
                    re.UNICODE
                ),
                'confidence': 0.98
            }
        ]
    
    def detect_contract_numbers(self, text: str) -> List[Dict[str, Any]]:
        """
        Основной метод детекции номеров контрактов
        
        Args:
            text: Текст для анализа
            
        Returns:
            Список найденных номеров контрактов с метаданными
        """
        detections = []
        
        for pattern_info in self.contract_patterns:
            pattern = pattern_info['pattern']
            name = pattern_info['name']
            base_confidence = pattern_info['confidence']
            
            for match in pattern.finditer(text):
                contract_number = match.group(1).strip()
                
                # Проверяем контекст если требуется
                if 'context_required' in pattern_info:
                    if not self._check_context(text, match, pattern_info['context_required']):
                        continue
                
                # Валидация номера контракта
                if not self._is_valid_contract_number(contract_number):
                    continue
                
                # Создаем детекцию
                detection = {
                    'category': 'contract_number',
                    'original_value': contract_number,
                    'confidence': base_confidence,
                    'position': {
                        'start': match.start(1),
                        'end': match.end(1)
                    },
                    'method': f'contract_regex_{name}',
                    'uuid': str(uuid.uuid4()),
                    'anonymized_text': self._anonymize_contract_number(contract_number),
                    'context': {
                        'full_match': match.group(0),
                        'pattern_name': name
                    }
                }
                
                detections.append(detection)
        
        return detections
    
    def _check_context(self, text: str, match: re.Match, required_words: List[str]) -> bool:
        """Проверка наличия контекстных слов рядом с найденным номером"""
        start = max(0, match.start() - 50)  # 50 символов до
        end = min(len(text), match.end() + 50)  # 50 символов после
        context = text[start:end].lower()
        
        return any(word.lower() in context for word in required_words)
    
    def _is_valid_contract_number(self, number: str) -> bool:
        """Валидация номера контракта"""
        if not number or len(number) < 2:
            return False
            
        # Исключаем слишком простые номера
        if number.isdigit() and len(number) < 3:
            return False
            
        # Паттерны валидных номеров контрактов
        valid_patterns = [
            r'^\d{1,4}\/[А-Я]{2,4}\-\d{4}$',  # 13/ОК-2023
            r'^\d{1,4}\-[А-Я]{2,4}\-\d{4}$',  # 13-ОК-2023  
            r'^[А-Я]{2,4}\-\d{1,4}\-\d{4}$',  # ОК-13-2023
            r'^\d{4}\-\d{1,4}$',               # 2023-13
            r'^[А-Я]{2,4}\d{1,4}$',           # ОК13
            r'^\d{1,4}\/\d{4}$',               # 13/2023
        ]
        
        return any(re.match(pattern, number.upper()) for pattern in valid_patterns)
    
    def _anonymize_contract_number(self, original_number: str) -> str:
        """Создание анонимизированной версии номера контракта"""
        # Сохраняем структуру оригинального номера
        if '/' in original_number:
            parts = original_number.split('/')
            if len(parts) == 2 and parts[1].endswith('-2023'):
                # Формат: 13/ОК-2023
                prefix = str(uuid.uuid4().hex[:2].upper())
                return f"{prefix}/{parts[1]}"
            elif len(parts) == 2:
                # Формат: 13/2023
                prefix = str(uuid.uuid4().hex[:2].upper())
                return f"{prefix}/{parts[1]}"
        elif '-' in original_number:
            parts = original_number.split('-')
            if len(parts) >= 2:
                # Заменяем первую часть
                prefix = str(uuid.uuid4().hex[:2].upper())
                return f"{prefix}-{'-'.join(parts[1:])}"
        
        # Для простых номеров - полная замена
        return str(uuid.uuid4().hex[:8].upper())