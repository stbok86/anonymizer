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
        Загрузка паттернов ТОЛЬКО из XLSX файла
        
        Returns:
            Словарь с паттернами по категориям
        """
        print(f"🔍 [INFO] Загружаем паттерны из: {self.patterns_file}")
        
        # Инициализируем пустой словарь паттернов
        patterns = {}
        
        # Загружаем паттерны ТОЛЬКО из файла
        try:
            if self.patterns_file and pd is not None:
                print(f"🔍 [DEBUG] Pandas доступен, пытаемся загрузить файл: {self.patterns_file}")
                import os
                
                # Проверяем существование файла
                if not os.path.exists(self.patterns_file):
                    print(f"❌ [ERROR] Файл паттернов не найден: {self.patterns_file}")
                    print(f"🔍 [DEBUG] Проверяем относительный путь...")
                    # Пробуем найти файл относительно текущего модуля
                    current_dir = os.path.dirname(os.path.abspath(__file__))
                    relative_path = os.path.join(current_dir, "..", self.patterns_file)
                    absolute_path = os.path.abspath(relative_path)
                    print(f"🔍 [DEBUG] Пробуем путь: {absolute_path}")
                    
                    if os.path.exists(absolute_path):
                        self.patterns_file = absolute_path
                        print(f"✅ [SUCCESS] Файл найден по пути: {self.patterns_file}")
                    else:
                        print(f"❌ [ERROR] Файл не найден и по относительному пути: {absolute_path}")
                        print("🔍 [DEBUG] Используем только встроенные паттерны")
                        return patterns
                
                # Определяем тип файла по расширению
                file_ext = os.path.splitext(self.patterns_file.lower())[1]
                print(f"🔍 [DEBUG] Расширение файла: {file_ext}")
                
                # Особая обработка: если файл .xlsx не существует как Excel, пробуем как CSV
                if file_ext == '.xlsx' and not self._is_valid_excel(self.patterns_file):
                    print(f"🔍 [DEBUG] Файл {self.patterns_file} не является валидным Excel, пробуем как CSV...")
                    try:
                        df = pd.read_csv(self.patterns_file)
                        print(f"✅ [SUCCESS] Загружены паттерны из файла {self.patterns_file} как CSV")
                    except Exception as csv_e:
                        print(f"❌ [ERROR] Не удалось прочитать как CSV: {csv_e}")
                        df = None
                elif file_ext == '.csv':
                    print(f"🔍 [DEBUG] Загружаем CSV файл...")
                    df = pd.read_csv(self.patterns_file)
                    print(f"✅ [SUCCESS] Загружены паттерны из CSV файла: {self.patterns_file}")
                elif file_ext in ['.xlsx', '.xls']:
                    print(f"🔍 [DEBUG] Загружаем Excel файл...")
                    df = pd.read_excel(self.patterns_file)
                    print(f"✅ [SUCCESS] Загружены паттерны из Excel файла: {self.patterns_file}")
                else:
                    print(f"❌ [ERROR] Неподдерживаемый формат файла: {file_ext}")
                    df = None
                
                if df is not None:
                    print(f"🔍 [DEBUG] DataFrame создан, строк: {len(df)}")
                    print(f"🔍 [DEBUG] Столбцы DataFrame: {list(df.columns)}")
                    
                    # Добавляем паттерны из файла к встроенным
                    patterns_added = 0
                    for i, (_, row) in enumerate(df.iterrows()):
                        category = row.get('category', 'unknown').lower()
                        pattern = row.get('pattern', '')
                        description = row.get('description', '')
                        confidence = float(row.get('confidence', 0.5))
                        
                        print(f"🔍 [DEBUG] Строка {i+1}: category={category}, pattern='{pattern[:50]}...', confidence={confidence}")
                        
                        if pattern:  # Добавляем только если паттерн не пустой
                            if category not in patterns:
                                patterns[category] = []
                                print(f"🔍 [DEBUG] Создана новая категория: {category}")
                            
                            patterns[category].append({
                                'pattern': pattern,
                                'description': description,
                                'confidence': confidence
                            })
                            patterns_added += 1
                    
                    print(f"✅ [SUCCESS] Добавлено {patterns_added} паттернов из файла")
                    print(f"🔍 [DEBUG] Итоговое количество категорий: {len(patterns)}")
                    for category, patterns_list in patterns.items():
                        print(f"🔍 [DEBUG]   {category}: {len(patterns_list)} правил")
                        
            else:
                if not self.patterns_file:
                    print(f"❌ [ERROR] Путь к файлу паттернов не указан")
                if pd is None:
                    print(f"❌ [ERROR] Pandas не доступен")
                
                print("❌ [ERROR] Встроенные паттерны удалены! Все правила должны быть в XLSX файле!")
                print("🚨 [ERROR] Система не может работать без файла паттернов!")
                return {}
                    
        except Exception as e:
            print(f"❌ [ERROR] Не удалось загрузить паттерны из файла {self.patterns_file}: {e}")
            import traceback
            traceback.print_exc()
            print("❌ [ERROR] Встроенные паттерны удалены! Все правила должны быть в XLSX файле!")
            print("🚨 [ERROR] Система не может работать без файла паттернов!")
            
            # Возвращаем пустой словарь - система должна требовать корректный файл
            return {}
        
        return patterns
    
    def _is_valid_excel(self, file_path: str) -> bool:
        """Проверяет, является ли файл валидным Excel файлом"""
        try:
            # Пробуем прочитать как Excel
            pd.read_excel(file_path, nrows=1)
            return True
        except Exception:
            return False
    
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
                
                # НЕТ удаления дубликатов - паттерны должны быть написаны правильно!
                if all_matches:
                    processed_block['sensitive_patterns'] = all_matches
            
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
        Удаление дублирующихся совпадений по позиции с приоритизацией по длине числа
        
        Args:
            matches: Список совпадений
            
        Returns:
            Список уникальных совпадений
        """
        unique_matches = []
        seen_positions = {}  # позиция -> лучший match
        
        # Сортируем по приоритету: длина числа (убывание), затем уверенность (убывание)
        def match_priority(match):
            value = match.get('original_value', '')
            # Считаем только цифры для определения длины
            digit_length = len(''.join(filter(str.isdigit, value)))
            confidence = match.get('confidence', 0)
            return (digit_length, confidence)
        
        matches.sort(key=match_priority, reverse=True)
        
        print(f"🔍 [DEBUG] Сортировка совпадений по приоритету:")
        for i, match in enumerate(matches):
            value = match.get('original_value', '')
            digit_length = len(''.join(filter(str.isdigit, value)))
            confidence = match.get('confidence', 0)
            category = match.get('category', 'unknown')
            print(f"   {i+1}. {category.upper()}: '{value}' (цифр: {digit_length}, уверенность: {confidence})")
        
        for match in matches:
            position = match.get('position', {})
            pos_key = (position.get('start', 0), position.get('end', 0))
            
            if pos_key not in seen_positions:
                # Первое совпадение для этой позиции - принимаем
                seen_positions[pos_key] = match
                unique_matches.append(match)
                print(f"✅ [DEBUG] Принято: {match.get('category', 'unknown').upper()} '{match.get('original_value', '')}' (позиция {pos_key})")
            else:
                # Уже есть совпадение для этой позиции - отклоняем
                existing = seen_positions[pos_key]
                print(f"❌ [DEBUG] Отклонено: {match.get('category', 'unknown').upper()} '{match.get('original_value', '')}' (дубликат {existing.get('category', 'unknown').upper()})")
        
        return unique_matches
    
    def find_sensitive_data(self, text: str) -> List[Dict]:
        """
        Простой поиск чувствительных данных в тексте
        
        Args:
            text: Текст для анализа
            
        Returns:
            Список найденных элементов (БЕЗ удаления дубликатов - паттерны должны быть корректными!)
        """
        regex_matches = self._find_regex_matches(text)
        nlp_matches = self._find_nlp_matches(text)
        
        all_matches = regex_matches + nlp_matches
        # НЕТ удаления дубликатов - правила должны быть написаны правильно!
        return all_matches
    
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