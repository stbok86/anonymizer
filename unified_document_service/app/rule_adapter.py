"""
Адаптер для поиска чувствительных данных с интеграцией NLP сервиса
"""

import re
import uuid
import requests
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple


class RuleEngineAdapter:
    def __init__(self, patterns_file: str = None, nlp_service_url: str = "http://localhost:8003"):
        """
        Инициализация адаптера правил поиска
        
        Args:
            patterns_file: Путь к файлу с паттернами (Excel/CSV)
            nlp_service_url: URL NLP сервиса для продвинутого анализа
        """
        self.patterns_file = patterns_file or "patterns/sensitive_patterns.xlsx"
        self.nlp_service_url = nlp_service_url
        self.patterns = self._load_patterns()
        
    def _load_patterns(self) -> Dict[str, List[Dict]]:
        """
        Загрузка паттернов из файла или использование встроенных
        
        Returns:
            Словарь с паттернами по категориям
        """
        patterns = {
            'phone': [
                {
                    'pattern': r'\b\+?7[-\s]?\(?9\d{2}\)?[-\s]?\d{3}[-\s]?\d{2}[-\s]?\d{2}\b',
                    'description': 'Российский мобильный номер',
                    'confidence': 0.95
                },
                {
                    'pattern': r'\b\+?7[-\s]?\(?\d{3}\)?[-\s]?\d{3}[-\s]?\d{2}[-\s]?\d{2}\b',
                    'description': 'Российский телефонный номер',
                    'confidence': 0.9
                },
                {
                    'pattern': r'\b8[-\s]?\(?9\d{2}\)?[-\s]?\d{3}[-\s]?\d{2}[-\s]?\d{2}\b',
                    'description': 'Российский мобильный (8-ка)',
                    'confidence': 0.9
                }
            ],
            'email': [
                {
                    'pattern': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                    'description': 'Email адрес',
                    'confidence': 0.98
                }
            ],
            'passport': [
                {
                    'pattern': r'\b\d{4}[-\s]?\d{6}\b',
                    'description': 'Серия и номер паспорта РФ',
                    'confidence': 0.85
                },
                {
                    'pattern': r'\b\d{2}[-\s]?\d{2}[-\s]?\d{6}\b',
                    'description': 'Паспорт РФ с разделителями',
                    'confidence': 0.8
                }
            ],
            'inn': [
                {
                    'pattern': r'\b\d{10}\b',
                    'description': 'ИНН физического лица (10 цифр)',
                    'confidence': 0.7
                },
                {
                    'pattern': r'\b\d{12}\b',
                    'description': 'ИНН юридического лица (12 цифр)',
                    'confidence': 0.7
                }
            ],
            'snils': [
                {
                    'pattern': r'\b\d{3}[-\s]?\d{3}[-\s]?\d{3}[-\s]?\d{2}\b',
                    'description': 'СНИЛС',
                    'confidence': 0.9
                }
            ],
            'name': [
                {
                    'pattern': r'\b[А-ЯЁ][а-яё]+\s+[А-ЯЁ][а-яё]+(?:\s+[А-ЯЁ][а-яё]+)?\b',
                    'description': 'ФИО на русском языке',
                    'confidence': 0.6
                }
            ]
        }
        
        # Попытка загрузить дополнительные паттерны из файла
        try:
            if self.patterns_file and pd is not None:
                df = pd.read_excel(self.patterns_file)
                # Добавляем паттерны из файла к встроенным
                for _, row in df.iterrows():
                    category = row.get('category', 'unknown').lower()
                    pattern = row.get('pattern', '')
                    description = row.get('description', '')
                    confidence = float(row.get('confidence', 0.5))
                    
                    if category not in patterns:
                        patterns[category] = []
                    
                    patterns[category].append({
                        'pattern': pattern,
                        'description': description,
                        'confidence': confidence
                    })
                    
        except Exception as e:
            print(f"Не удалось загрузить паттерны из файла {self.patterns_file}: {e}")
            print("Используются встроенные паттерны")
        
        return patterns
    
    def apply_rules_to_blocks(self, blocks: List[Dict]) -> List[Dict]:
        """
        Применение правил поиска чувствительных данных к блокам документа
        
        Args:
            blocks: Список блоков документа
            
        Returns:
            Блоки с найденными чувствительными данными
        """
        processed_blocks = []
        
        for block in blocks:
            processed_block = block.copy()
            
            text_content = block.get('text', block.get('content', ''))
            if text_content:
                # Поиск с помощью регулярных выражений
                regex_matches = self._find_regex_matches(text_content)
                
                # Поиск с помощью NLP сервиса (если доступен)
                nlp_matches = self._find_nlp_matches(text_content)
                
                # Объединяем результаты
                all_matches = regex_matches + nlp_matches
                
                # Удаляем дубликаты по позиции
                unique_matches = self._remove_duplicate_matches(all_matches)
                
                if unique_matches:
                    processed_block['sensitive_patterns'] = unique_matches
            
            processed_blocks.append(processed_block)
        
        return processed_blocks
    
    def _find_regex_matches(self, text: str) -> List[Dict]:
        """
        Поиск совпадений с помощью регулярных выражений
        
        Args:
            text: Текст для анализа
            
        Returns:
            Список найденных совпадений
        """
        matches = []
        
        for category, category_patterns in self.patterns.items():
            for pattern_info in category_patterns:
                pattern = pattern_info['pattern']
                confidence = pattern_info['confidence']
                description = pattern_info['description']
                
                try:
                    for match in re.finditer(pattern, text):
                        matches.append({
                            'category': category,
                            'original_value': match.group(),
                            'uuid': str(uuid.uuid4()),
                            'position': {
                                'start': match.start(),
                                'end': match.end()
                            },
                            'confidence': confidence,
                            'source': 'regex',
                            'description': description
                        })
                except re.error as e:
                    print(f"Ошибка в регулярном выражении {pattern}: {e}")
                    continue
        
        return matches
    
    def _find_nlp_matches(self, text: str) -> List[Dict]:
        """
        Поиск совпадений с помощью NLP сервиса
        
        Args:
            text: Текст для анализа
            
        Returns:
            Список найденных совпадений от NLP сервиса
        """
        try:
            # Пытаемся обратиться к NLP сервису
            response = requests.post(
                f"{self.nlp_service_url}/analyze_text",
                json={"text": text},
                timeout=5
            )
            
            if response.status_code == 200:
                nlp_data = response.json()
                
                matches = []
                for entity in nlp_data.get('entities', []):
                    matches.append({
                        'category': entity.get('label', 'unknown').lower(),
                        'original_value': entity.get('text', ''),
                        'uuid': str(uuid.uuid4()),
                        'position': {
                            'start': entity.get('start', 0),
                            'end': entity.get('end', 0)
                        },
                        'confidence': entity.get('confidence', 0.5),
                        'source': 'nlp',
                        'description': f"NLP: {entity.get('label', 'Unknown')}"
                    })
                
                return matches
                
        except requests.exceptions.RequestException as e:
            print(f"NLP сервис недоступен: {e}")
        except Exception as e:
            print(f"Ошибка при обращении к NLP сервису: {e}")
        
        return []
    
    def _remove_duplicate_matches(self, matches: List[Dict]) -> List[Dict]:
        """
        Удаление дублирующихся совпадений по позиции
        
        Args:
            matches: Список совпадений
            
        Returns:
            Список уникальных совпадений
        """
        unique_matches = []
        seen_positions = set()
        
        # Сортируем по уверенности (убывание)
        matches.sort(key=lambda x: x.get('confidence', 0), reverse=True)
        
        for match in matches:
            position = match.get('position', {})
            pos_key = (position.get('start', 0), position.get('end', 0))
            
            if pos_key not in seen_positions:
                seen_positions.add(pos_key)
                unique_matches.append(match)
        
        return unique_matches
    
    def find_sensitive_data(self, text: str) -> List[Dict]:
        """
        Простой поиск чувствительных данных в тексте
        
        Args:
            text: Текст для анализа
            
        Returns:
            Список найденных элементов
        """
        regex_matches = self._find_regex_matches(text)
        nlp_matches = self._find_nlp_matches(text)
        
        all_matches = regex_matches + nlp_matches
        return self._remove_duplicate_matches(all_matches)
    
    def generate_report(self, processed_blocks: List[Dict]) -> Dict[str, Any]:
        """
        Генерация отчета о найденных чувствительных данных
        
        Args:
            processed_blocks: Обработанные блоки документа
            
        Returns:
            Отчет с статистикой
        """
        report = {
            'total_blocks': len(processed_blocks),
            'blocks_with_sensitive_data': 0,
            'pattern_statistics': {},
            'confidence_distribution': {
                'high': 0,  # > 0.8
                'medium': 0,  # 0.5 - 0.8
                'low': 0    # < 0.5
            },
            'source_statistics': {
                'regex': 0,
                'nlp': 0
            }
        }
        
        total_patterns = 0
        
        for block in processed_blocks:
            if 'sensitive_patterns' in block and block['sensitive_patterns']:
                report['blocks_with_sensitive_data'] += 1
                
                for pattern in block['sensitive_patterns']:
                    total_patterns += 1
                    
                    # Статистика по категориям
                    category = pattern.get('category', 'unknown')
                    if category not in report['pattern_statistics']:
                        report['pattern_statistics'][category] = 0
                    report['pattern_statistics'][category] += 1
                    
                    # Распределение уверенности
                    confidence = pattern.get('confidence', 0.5)
                    if confidence > 0.8:
                        report['confidence_distribution']['high'] += 1
                    elif confidence > 0.5:
                        report['confidence_distribution']['medium'] += 1
                    else:
                        report['confidence_distribution']['low'] += 1
                    
                    # Статистика по источникам
                    source = pattern.get('source', 'regex')
                    if source in report['source_statistics']:
                        report['source_statistics'][source] += 1
        
        report['total_patterns_found'] = total_patterns
        
        return report
    
    def validate_patterns(self) -> Dict[str, Any]:
        """
        Валидация загруженных паттернов
        
        Returns:
            Результат валидации
        """
        validation_report = {
            'valid_patterns': 0,
            'invalid_patterns': 0,
            'categories': list(self.patterns.keys()),
            'errors': []
        }
        
        for category, patterns_list in self.patterns.items():
            for i, pattern_info in enumerate(patterns_list):
                try:
                    # Проверяем валидность регулярного выражения
                    re.compile(pattern_info['pattern'])
                    validation_report['valid_patterns'] += 1
                except re.error as e:
                    validation_report['invalid_patterns'] += 1
                    validation_report['errors'].append({
                        'category': category,
                        'pattern_index': i,
                        'pattern': pattern_info['pattern'],
                        'error': str(e)
                    })
        
        return validation_report