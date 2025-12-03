#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Стратегия детекции информационных систем для анонимизации
"""

import spacy
import re
import uuid
from typing import List, Dict, Any, Set, Tuple, Optional
from spacy.matcher import Matcher, PhraseMatcher
from spacy.tokens import Doc, Span, Token

try:
    from detection_strategies import DetectionStrategy
except ImportError:
    import sys
    import os
    sys.path.append(os.path.dirname(__file__))
    from detection_strategies import DetectionStrategy


class InformationSystemStrategy(DetectionStrategy):
    """Стратегия для детекции и анонимизации названий информационных систем"""
    
    def __init__(self, config_settings: Dict[str, Any], nlp_model=None):
        super().__init__(config_settings)
        self.nlp = nlp_model  # Используем переданную модель
        self.matcher = None
        self.phrase_matcher = None
        self.partitioner = None
        self.is_initialized = False
        # Инициализируем сразу при создании объекта
        self._initialize_components()
        
    def _initialize_components(self):
        """Инициализация spaCy компонентов"""
        if self.is_initialized:
            return
            
        try:
            # Если модель не передана, загружаем свою
            if self.nlp is None:
                model_name = self.settings.get('spacy_model', 'ru_core_news_sm')
                models_to_try = [model_name, 'ru_core_news_sm', 'ru_core_news_md']
                
                for model in models_to_try:
                    try:
                        self.nlp = spacy.load(model)
                        print(f"✅ Загружена spaCy модель: {model}")
                        break
                    except OSError:
                        continue
                
                if self.nlp is None:
                    raise RuntimeError("Не удалось загрузить ни одну русскую spaCy модель")
            # else: используем переданную модель без вывода
            
            # Создаем матчеры
            self.matcher = Matcher(self.nlp.vocab)
            self.phrase_matcher = PhraseMatcher(self.nlp.vocab, attr="LOWER")
            
            # Создаем партиционер
            self.partitioner = ISPartitioner(self.nlp, self.settings)
            
            # Настраиваем правила
            self._setup_patterns()
            
            self.is_initialized = True
            
        except Exception as e:
            print(f"⚠️ Ошибка инициализации InformationSystemStrategy: {e}")
            # Не поднимаем исключение, чтобы не ломать весь NLP сервис
            self.is_initialized = False
    
    def _setup_patterns(self):
        """Загрузка паттернов для детекции ИС из JSON-файла"""
        from nlp_config import NLPConfig
        config = NLPConfig()
        patterns = config.get_information_system_patterns()
        if not patterns:
            raise RuntimeError("Паттерны для информационных систем не найдены в nlp_patterns.json")
        self.complex_abbr_patterns = [p['pattern'] for p in patterns if p.get('type') == 'regex' and p.get('priority', 1) == 1]
        self.spaced_abbr_patterns = [p['pattern'] for p in patterns if p.get('type') == 'regex' and p.get('priority', 1) == 2]
        abbr_phrases = [p['pattern'] for p in patterns if p.get('type') == 'phrase']
        abbr_docs = [self.nlp(abbr) for abbr in abbr_phrases]
        if abbr_docs:
            self.phrase_matcher.add("IS_SIMPLE_ABBREVIATIONS", abbr_docs)
    
    def detect_information_systems_in_text(self, text: str, doc: Doc = None) -> List[Dict[str, Any]]:
        """
        Детекция информационных систем в тексте
        
        Args:
            text: Текст для анализа
            doc: Предварительно обработанный spaCy Doc (опционально)
            
        Returns:
            Список обнаруженных ИС с метаданными
        """
        # Проверяем готовность компонентов
        if not self.is_initialized:
            return []
        
        if doc is None:
            doc = self.nlp(text)
        
        detections = []
        
        try:
            complex_detections = self._search_complex_abbreviations(text)
            detections.extend(complex_detections)
            regex_detections = self._simple_pattern_search(text, doc, detections)
            detections.extend(regex_detections)
            simple_detections = self._search_simple_abbreviations(text, doc, detections)
            detections.extend(simple_detections)
            spaced_detections = self._search_spaced_abbreviations_filtered(text, detections)
            detections.extend(spaced_detections)
            detections = self._remove_duplicates(detections, threshold=0.7)
            
        except Exception as e:
            print(f"⚠️ Ошибка при детекции ИС: {e}")
            return []
        
        return detections
    
    def _search_complex_abbreviations(self, text: str) -> List[Dict[str, Any]]:
        """Поиск сложных аббревиатур типа ЕИСУФХД с подробным логированием"""
        detections = []
        for pattern in self.complex_abbr_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                start_char = match.start()
                end_char = match.end()
                # Post-filter: abbreviation must not be inside a word (not preceded or followed by lowercase letter)
                before = text[start_char - 1] if start_char > 0 else ''
                after = text[end_char] if end_char < len(text) else ''
                debug_context = text[max(0, start_char-20):min(len(text), end_char+20)]
                print(f"[DEBUG][IS][complex_abbr] pattern: {pattern} | match: '{match.group(0)}' | pos: {start_char}-{end_char} | before: '{before}' | after: '{after}' | context: ...{debug_context}...")
                if (before and before.islower()) or (after and after.islower()):
                    print(f"[DEBUG][IS][complex_abbr][SKIP] False positive filtered: '{match.group(0)}' at {start_char}-{end_char}")
                    continue
                anonymous_part = match.group(1)  # ЕИС
                private_part = match.group(2)    # УФХД
                full_match = match.group(0)      # ЕИСУФХД
                anonymized_text = f"{anonymous_part} [SYSTEM_ID]"
                detection = {
                    'category': 'information_system',
                    'original_value': full_match,
                    'confidence': 0.9,
                    'position': {'start': start_char, 'end': end_char},
                    'method': 'complex_abbreviation',
                    'uuid': 'placeholder',
                    'system_type': 'information_system',
                    'core_part': anonymous_part,
                    'private_part': private_part,
                    'anonymized_text': anonymized_text
                }
                # Подробный отладочный лог
                print(
                    f"[complex_abbreviation][DETECT] pattern: {pattern} | "
                    f"match: '{full_match}' | pos: {start_char}-{end_char} | "
                    f"core: '{anonymous_part}' | private: '{private_part}' | "
                    f"anonymized: '{anonymized_text}' | text: ...{text[max(0, start_char-30):min(len(text), end_char+30)]}..."
                )
                detections.append(detection)
        return detections
    
    def _search_spaced_abbreviations_filtered(self, text: str, existing_detections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Поиск аббревиатур с пробелами только в местах без конфликтов"""
        detections = []
        
        # Получаем позиции уже найденных детекций
        occupied_ranges = []
        for detection in existing_detections:
            pos = detection.get('position', {})
            if 'start' in pos and 'end' in pos:
                occupied_ranges.append((pos['start'], pos['end']))
        
        for pattern in self.spaced_abbr_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                start_char = match.start()
                end_char = match.end()
                # Post-filter: abbreviation must not be inside a word (not preceded or followed by lowercase letter)
                before = text[start_char - 1] if start_char > 0 else ''
                after = text[end_char] if end_char < len(text) else ''
                debug_context = text[max(0, start_char-20):min(len(text), end_char+20)]
                print(f"[DEBUG][IS][spaced_abbr] pattern: {pattern} | match: '{match.group(0)}' | pos: {start_char}-{end_char} | before: '{before}' | after: '{after}' | context: ...{debug_context}...")
                if (before and before.islower()) or (after and after.islower()):
                    print(f"[DEBUG][IS][spaced_abbr][SKIP] False positive filtered: '{match.group(0)}' at {start_char}-{end_char}")
                    continue
                anonymous_part = match.group(1)  # ЕИС/ФГИС
                private_part = match.group(2).strip()  # УФХД ПК
                full_match = match.group(0)      # ЕИС УФХД ПК
                # Проверяем пересечения с существующими детекциями
                is_overlapping = False
                for occ_start, occ_end in occupied_ranges:
                    if not (end_char <= occ_start or start_char >= occ_end):
                        is_overlapping = True
                        break
                if not is_overlapping:
                    # Создаем анонимизированный текст (будет обработан в FormatterApplier)
                    anonymized_text = f"{anonymous_part} [SYSTEM_ID]"
                    detection = {
                        'category': 'information_system',
                        'original_value': full_match,
                        'confidence': 0.9,  # Высокая уверенность для точных аббревиатур
                        'position': {'start': start_char, 'end': end_char},
                        'method': 'spaced_abbreviation',
                        'uuid': 'placeholder',  # Временный placeholder, UUID будет генерироваться централизованно в FormatterApplier
                        'system_type': 'information_system',
                        'core_part': anonymous_part,
                        'private_part': private_part,
                        'anonymized_text': anonymized_text
                    }
                    print(f"🔧 Общая часть (без нормализации): '{anonymous_part}'")
                    detections.append(detection)
        return detections

    def _search_spaced_abbreviations_filtered(self, text: str, existing_detections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Поиск аббревиатур с пробелами с точным определением границ через spaCy токены"""
        detections = []
        
        # Получаем позиции уже найденных детекций для избежания пересечений
        occupied_ranges = []
        for detection in existing_detections:
            pos = detection.get('position', {})
            if 'start' in pos and 'end' in pos:
                occupied_ranges.append((pos['start'], pos['end']))
        
        # Создаем spaCy документ для точной токенизации
        doc = self.nlp(text)
        
        # Ищем паттерны аббревиатур в начале токенов
        abbreviation_tokens = {
            'ЕИС': 'ЕИС', 'АИС': 'АИС', 'ГИС': 'ГИС', 
            'ФГИС': 'ФГИС', 'ЕГИС': 'ЕГИС', 'ПГИС': 'ПГИС',
            'ГАС': 'ГАС', 'ФИС': 'ФИС', 'РИС': 'РИС'
        }
        
        for i, token in enumerate(doc):
            token_text = token.text.upper()
            # Проверяем, является ли токен одной из наших аббревиатур
            if token_text in abbreviation_tokens:
                anonymous_part = abbreviation_tokens[token_text]
                # Проверяем, не пересекается ли с уже найденными детекциями
                start_char = token.idx
                is_overlapping = False
                for occ_start, occ_end in occupied_ranges:
                    if not (start_char >= occ_end or start_char < occ_start):
                        is_overlapping = True
                        break
                if is_overlapping:
                    continue
                # Ищем следующие токены-аббревиатуры (заглавные буквы, длина <= 10)
                private_parts = []
                current_pos = i + 1
                while current_pos < len(doc):
                    next_token = doc[current_pos]
                    next_text = next_token.text.strip()
                    # Пропускаем пробельные токены (включая неразрывные пробелы)
                    if not next_text or next_text.isspace():
                        current_pos += 1
                        continue
                    # Проверяем, является ли следующий токен частью аббревиатуры
                    if (next_text and 
                        len(next_text) <= 10 and 
                        next_text.isupper() and 
                        next_text.isalpha() and
                        not next_text.lower() in ['и', 'в', 'на', 'с', 'для', 'по']):  # Исключаем предлоги
                        private_parts.append(next_text)
                        current_pos += 1
                        # Ограничиваем максимум 3 токена в приватной части
                        if len(private_parts) >= 3:
                            break
                    else:
                        # Если встретили не-аббревиатуру, останавливаемся
                        break
                # Создаем детекцию только если есть приватная часть
                if private_parts:
                    private_part = ' '.join(private_parts)
                    # Вычисляем точные позиции на основе токенов
                    # Находим последний значимый (не-пробельный) токен
                    last_meaningful_pos = current_pos - 1
                    while (last_meaningful_pos >= 0 and 
                           last_meaningful_pos < len(doc) and 
                           (not doc[last_meaningful_pos].text.strip() or doc[last_meaningful_pos].text.isspace())):
                        last_meaningful_pos -= 1
                    if last_meaningful_pos >= 0 and last_meaningful_pos < len(doc):
                        last_token = doc[last_meaningful_pos]
                        end_char = last_token.idx + len(last_token.text)
                    else:
                        # Fallback: используем позицию текущего токена
                        end_char = token.idx + len(token.text) + len(private_part) + 1
                    # ИСПРАВЛЕНИЕ: Извлекаем точный текст с сохранением исходных пробелов
                    full_match = text[start_char:end_char]
                    debug_context = text[max(0, start_char-20):min(len(text), end_char+20)]
                    print(f"[DEBUG][IS][spacy_abbr] abbr: '{anonymous_part}' | private: '{private_part}' | match: '{full_match}' | pos: {start_char}-{end_char} | context: ...{debug_context}...")
                    # Создаем анонимизированный текст (будет обработан в FormatterApplier)
                    anonymized_text = f"{anonymous_part} [SYSTEM_ID]"
                    detection = {
                        'category': 'information_system',
                        'original_value': full_match,
                        'confidence': 0.95,  # Высокая уверенность для токен-базированного анализа
                        'position': {'start': start_char, 'end': end_char},
                        'method': 'spaced_abbreviation',
                        'uuid': 'placeholder',  # Временный placeholder, UUID будет генерироваться централизованно в FormatterApplier
                        'system_type': 'information_system',
                        'core_part': anonymous_part,
                        'private_part': private_part,
                        'anonymized_text': anonymized_text
                    }
                    detections.append(detection)
        return detections

    def _search_spaced_abbreviations(self, text: str) -> List[Dict[str, Any]]:
        """Устаревший метод - используется только для обратной совместимости"""
        # Вызываем новый улучшенный метод с пустым списком существующих детекций
        return self._search_spaced_abbreviations_filtered(text, [])

    def _search_simple_abbreviations(self, text: str, doc, existing_detections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Поиск простых аббревиатур только если нет более сложных в том же месте"""
        detections = []
        
        # Получаем позиции уже найденных детекций
        occupied_ranges = []
        for detection in existing_detections:
            pos = detection.get('position', {})
            if 'start' in pos and 'end' in pos:
                occupied_ranges.append((pos['start'], pos['end']))
        
        # Поиск через PhraseMatcher
        phrase_results = self.phrase_matcher(doc)
        for match_id, start, end in phrase_results:
            span = doc[start:end]
            
            # Проверяем, не пересекается ли с уже найденными детекциями
            span_start = span.start_char
            span_end = span.end_char
            
            is_overlapping = False
            for occ_start, occ_end in occupied_ranges:
                if not (span_end <= occ_start or span_start >= occ_end):
                    is_overlapping = True
                    break
            
            if not is_overlapping:
                detection = self._create_simple_abbreviation_detection(span, doc)
                if detection:
                    detections.append(detection)
        
        return detections
    
    def _create_simple_abbreviation_detection(self, span, doc) -> Optional[Dict[str, Any]]:
        """Создает детекцию для простой аббревиатуры (только анонимная часть)"""
        
        abbr_text = span.text.strip()
        
        # Проверяем контекст - если после аббревиатуры есть еще аббревиатуры, пропускаем
        next_token_index = span.end
        if next_token_index < len(doc):
            next_token = doc[next_token_index]
            # Если следующий токен - это аббревиатура из заглавных букв, пропускаем
            if (next_token.text and 
                len(next_token.text) <= 10 and 
                next_token.text.isupper() and 
                next_token.text.isalpha()):
                return None
                
            # Также проверяем следующий через один токен (для случаев "ЕИС УФХД ПК")  
            if next_token_index + 1 < len(doc):
                token_after_next = doc[next_token_index + 1]
                if (token_after_next.text and 
                    len(token_after_next.text) <= 10 and 
                    token_after_next.text.isupper() and 
                    token_after_next.text.isalpha()):
                    return None
        
        # Простые аббревиатуры остаются как есть (только анонимная часть)
        detection = {
            'category': 'information_system',
            'original_value': abbr_text,
            'confidence': 0.85,
            'position': {'start': span.start_char, 'end': span.end_char},
            'method': 'simple_abbreviation',
            'uuid': 'placeholder',  # Временный placeholder, UUID будет генерироваться централизованно в FormatterApplier
            'system_type': 'information_system',
            'core_part': abbr_text,         # Вся аббревиатуря - это анонимная часть
            'private_part': '',             # Нет приватной части
            'anonymized_text': abbr_text    # Остается как есть
        }
        
        print(f"🔧 Общая часть (без нормализации): '{abbr_text}'")
        return detection
    
    def _simple_pattern_search(self, text: str, doc: Doc, existing_detections: List[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Умный поиск паттернов информационных систем с правильным определением границ"""
        detections = []
        
        if existing_detections is None:
            existing_detections = []
        
        # Получаем позиции уже найденных детекций для проверки пересечений
        occupied_ranges = []
        for detection in existing_detections:
            pos = detection.get('position', {})
            if 'start' in pos and 'end' in pos:
                occupied_ranges.append((pos['start'], pos['end']))
        
        # Улучшенные паттерны для поиска ИС с точным определением границ
        patterns = [
            {
                'name': 'единая_ис_exact', 
                'pattern': r'(?i)(Единая)\s+(информационная)\s+(система)',
                'capture_suffix': True
            },
            {
                'name': 'единая_ис_declined', 
                'pattern': r'(?i)(едино[йыеми])\s+(информационно[йыеми])\s+(систем[аыеуой])',
                'capture_suffix': True
            },
            {
                'name': 'государственная_ис',
                'pattern': r'(?i)(государственна[яоейыми]|федеральна[яоейыми])\s+(информационна[яоейыми])\s+(систем[аыеуой])', 
                'capture_suffix': True
            },
            {
                'name': 'автоматизированная_ис',
                'pattern': r'(?i)(автоматизированна[яоейыми])\s+(информационна[яоейыми])\s+(систем[аыеуой])',
                'capture_suffix': True
            },
        ]
        
        for pattern_info in patterns:
            pattern = pattern_info['pattern']
            matches = re.finditer(pattern, text, re.IGNORECASE | re.UNICODE)
            
            for match in matches:
                start_char = match.start()
                core_end = match.end()
                core_text = match.group().strip()
                
                # Ищем дополнительную часть после основного паттерна
                suffix_text = ""
                actual_end = core_end
                
                if pattern_info.get('capture_suffix', False):
                    # Ищем продолжение после основного паттерна
                    remaining_text = text[core_end:]
                    suffix_match = self._extract_system_suffix(remaining_text)
                    if suffix_match:
                        suffix_text = suffix_match
                        # Правильно вычисляем конечную позицию
                        # Ищем suffix в оставшемся тексте и прибавляем к позиции core_end
                        suffix_start_in_remaining = remaining_text.lstrip().find(suffix_match.strip())
                        if suffix_start_in_remaining != -1:
                            # Учитываем пробелы в начале remaining_text
                            leading_spaces = len(remaining_text) - len(remaining_text.lstrip())
                            actual_end = core_end + leading_spaces + suffix_start_in_remaining + len(suffix_match.strip())
                        else:
                            # Fallback: используем приблизительный расчет
                            actual_end = core_end + len(suffix_match) + 1
                
                # Формируем полное название, избегая двойных пробелов
                if suffix_text:
                    full_name = f"{core_text} {suffix_text}".strip()
                else:
                    full_name = core_text
                
                # Проверяем, не пересекается ли с уже найденными детекциями
                is_overlapping = False
                for occ_start, occ_end in occupied_ranges:
                    # Проверяем перекрытие
                    if not (actual_end <= occ_start or start_char >= occ_end):
                        is_overlapping = True
                        break
                
                # Если есть пересечение, пропускаем эту детекцию
                if is_overlapping:
                    continue
                
                # Создаем детекцию
                detection = {
                    'category': 'information_system',
                    'original_value': full_name,
                    'confidence': 0.8,
                    'position': {'start': start_char, 'end': actual_end},
                    'method': 'information_system_regex',
                    'uuid': 'placeholder'  # Временный placeholder, UUID будет генерироваться централизованно в FormatterApplier
                }
                
                # Разделяем на части
                partition_result = self._intelligent_partition(core_text, suffix_text)
                if partition_result:
                    detection.update(partition_result)
                
                detections.append(detection)
        
        return detections
    
    def _extract_system_suffix(self, remaining_text: str) -> Optional[str]:
        """Извлекает продолжение названия информационной системы"""
        if not remaining_text:
            return None
        
        # Стоп-слова, которые указывают на конец названия системы
        stop_words = [
            'содержит', 'включает', 'предназначена', 'используется', 'применяется',
            'обеспечивает', 'является', 'представляет', 'служит', 'создана',
            'разработана', 'внедрена', 'функционирует', 'работает', 'действует',
            'предоставляет', 'осуществляет', 'выполняет'
        ]
        
        # Убираем ведущие пробелы и разбиваем на слова
        cleaned_text = remaining_text.lstrip()
        words = cleaned_text.split()
        suffix_words = []
        
        for word in words:
            # Проверяем на открывающую скобку - это всегда конец названия системы
            if '(' in word:
                # Если скобка в начале слова, останавливаемся
                if word.startswith('('):
                    break
                # Если скобка в середине/конце, добавляем часть до скобки и останавливаемся
                else:
                    bracket_pos = word.find('(')
                    word_before_bracket = word[:bracket_pos].strip()
                    if word_before_bracket:
                        suffix_words.append(word_before_bracket)
                    break
            
            # Очищаем от знаков препинания для проверки
            clean_word = re.sub(r'[^\w\s\-]', '', word).lower()
            
            # Если встретили стоп-слово, останавливаемся
            if clean_word in stop_words:
                break
            
            # Если встретили точку, запятую или другой знак конца предложения
            if word.endswith('.') or word.endswith(',') or word.endswith(';') or word.endswith('!') or word.endswith('?'):
                # Добавляем слово без знака препинания
                clean_word_for_suffix = word[:-1]
                if clean_word_for_suffix:
                    suffix_words.append(clean_word_for_suffix)
                break
            
            # Добавляем обычные слова
            if len(clean_word) > 0:
                suffix_words.append(word)
            else:
                break
                
        return ' '.join(suffix_words).strip() if suffix_words else None
    
    def _intelligent_partition(self, core_text: str, suffix_text: str) -> Optional[Dict[str, Any]]:
        """Умное разделение названия ИС на общую и приватную части с сохранением падежа"""
        
        # НЕ нормализуем общую часть - сохраняем оригинальный падеж
        core_part = core_text.strip()
        print(f"🔧 Общая часть (без нормализации): '{core_part}'")
        
        # Приватная часть - это suffix_text (специфическая область применения)
        private_part = suffix_text.strip() if suffix_text else ""
        
        # Создаем анонимизированный текст
        if private_part and len(private_part.split()) >= 1:
            # Если есть приватная часть, заменяем её на плейсхолдер
            anonymized_text = f"{core_part} [SYSTEM_ID]"
        else:
            # Если нет приватной части, оставляем как есть
            anonymized_text = core_part
        
        return {
            'system_type': 'information_system',
            'core_part': core_part, 
            'private_part': private_part,
            'anonymized_text': anonymized_text
        }
    
    def _normalize_system_name(self, core_text: str) -> str:
        """УСТАРЕЛО: Нормализует название системы, приводя к именительному падежу
        
        Этот метод больше не используется, так как система должна сохранять
        оригинальный падеж в результате анонимизации.
        """
        
        # Этот метод больше не используется
        return core_text
    
    def _simple_partition(self, text: str) -> Optional[Dict[str, Any]]:
        """Простое разделение названия ИС"""
        
        # Ключевые слова системы
        system_keywords = ['система', 'системы', 'систему', 'системе', 'платформа', 'портал']
        
        words = text.split()
        system_word_idx = -1
        
        # Найдем ключевое слово
        for i, word in enumerate(words):
            if any(kw in word.lower() for kw in system_keywords):
                system_word_idx = i
                break
        
        if system_word_idx == -1:
            return None
        
        # Разделяем
        core_part = " ".join(words[:system_word_idx + 1])
        private_part = " ".join(words[system_word_idx + 1:]) if system_word_idx + 1 < len(words) else ""
        
        # Создаем анонимизированный текст
        if private_part and len(private_part.split()) >= 2:
            anonymized_text = f"{core_part} [SYSTEM_ID]"
        else:
            anonymized_text = core_part
            private_part = ""
        
        return {
            'system_type': 'information_system',
            'core_part': core_part.strip(), 
            'private_part': private_part.strip(),
            'anonymized_text': anonymized_text
        }
    
    def _create_detection_from_span(self, span: Span, method: str, doc: Doc) -> Optional[Dict[str, Any]]:
        """Создает объект детекции из spaCy span"""
        
        # Разделяем на общую и приватную части  
        partition_result = self._simple_partition(span.text)
        
        confidence = 0.85 if method == "phrase_matcher" else 0.8
        
        detection = {
            'category': 'information_system',
            'original_value': span.text,
            'confidence': confidence,
            'position': {
                'start': span.start_char,
                'end': span.end_char
            },
            'method': f'information_system_{method}',
            'uuid': 'placeholder'  # Временный placeholder, UUID будет генерироваться централизованно в FormatterApplier
        }
        
        if partition_result:
            detection.update(partition_result)
        else:
            detection.update({
                'system_type': 'information_system',
                'core_part': span.text,
                'private_part': '',
                'anonymized_text': span.text
            })
        
        return detection
    
    def combine_results(self, results_by_method: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """
        Комбинирует результаты детекции ИС
        """
        # Если есть результаты spacy_ner, пропускаем их через нашу детекцию
        all_detections = []
        
        for method_name, detections in results_by_method.items():
            for detection in detections:
                # Проверяем, может ли это быть ИС
                text = detection.get('original_value', '')
                if self._might_be_information_system(text):
                    # Применяем нашу детекцию
                    is_detections = self.detect_information_systems_in_text(text)
                    if is_detections:
                        # Заменяем оригинальную детекцию на ИС детекцию
                        for is_det in is_detections:
                            # Корректируем позиции
                            orig_start = detection['position']['start']
                            is_det['position']['start'] += orig_start
                            is_det['position']['end'] += orig_start
                            all_detections.append(is_det)
                    else:
                        all_detections.append(detection)
                else:
                    all_detections.append(detection)
        
        # Удаляем дубликаты
        return self._remove_duplicates(all_detections, threshold=0.6)
    
    def _might_be_information_system(self, text: str) -> bool:
        """Проверяет, может ли текст быть названием ИС"""
        text_lower = text.lower()
        
        # Ключевые слова ИС
        is_keywords = [
            'информационная система', 'информационная платформа', 
            'информационный портал', 'информационный комплекс',
            'еис', 'аис', 'гис', 'егис', 'епгу', 'есиа'
        ]
        
        return any(keyword in text_lower for keyword in is_keywords)


class ISPartitioner:
    """Упрощенный компонент для разделения названий ИС"""
    
    def __init__(self, nlp, settings: Dict[str, Any]):
        self.nlp = nlp
        self.settings = settings