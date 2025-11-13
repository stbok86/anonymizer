#!/usr/bin/env python3
"""
NLP Adapter для обработки неструктурированных данных
Фокус на spaCy NER + кастомные матчеры + морфологический анализ
"""

import re
import os
import uuid
from typing import Dict, List, Any, Optional, Set
import pandas as pd
import spacy
from spacy.matcher import Matcher, PhraseMatcher
from spacy.tokens import Doc, Token
import pymorphy3


class NLPAdapter:
    """
    Адаптер для обработки неструктурированных именованных сущностей
    """
    
    def __init__(self, patterns_file: Optional[str] = None, confidence_threshold: float = 0.6):
        """
        Инициализация NLP адаптера
        
        Args:
            patterns_file: Путь к файлу с паттернами. Если None, использует дефолтный
            confidence_threshold: Минимальный уровень уверенности для обнаружений
        """
        self.nlp = None
        self.matcher = None
        self.phrase_matcher = None
        self.morph = None  # pymorphy3 анализатор
        self.patterns = {}
        self.pattern_configs = {}
        self.confidence_threshold = confidence_threshold
        
        # Специальные термины для PhraseMatcher
        self.custom_phrases = {}
        
        # Загружаем spaCy модель
        self._load_spacy_model()
        
        # Инициализируем морфологический анализатор
        self._init_morphology()
        
        # Загружаем паттерны
        if patterns_file is None:
            patterns_file = os.path.join(
                os.path.dirname(__file__), "..", "patterns", "nlp_patterns.xlsx"
            )
        self._load_patterns(patterns_file)
        
        # Настраиваем матчеры
        self._setup_matchers()
    
    def _load_spacy_model(self):
        """Загружает русскую spaCy модель"""
        try:
            # Пытаемся загрузить большую модель
            self.nlp = spacy.load("ru_core_news_lg")
            print("✅ Загружена русская spaCy модель: ru_core_news_lg")
        except OSError:
            try:
                # Если большой нет, загружаем среднюю
                self.nlp = spacy.load("ru_core_news_md")
                print("✅ Загружена русская spaCy модель: ru_core_news_md")
            except OSError:
                try:
                    # Если средней нет, загружаем малую
                    self.nlp = spacy.load("ru_core_news_sm")
                    print("✅ Загружена русская spaCy модель: ru_core_news_sm")
                except OSError:
                    raise RuntimeError(
                        "Не найдена русская spaCy модель. "
                        "Установите: python -m spacy download ru_core_news_sm"
                    )
    
    def _init_morphology(self):
        """Инициализирует морфологический анализатор pymorphy3"""
        try:
            self.morph = pymorphy3.MorphAnalyzer()
            print("✅ Морфологический анализатор pymorphy3 загружен")
        except Exception as e:
            print(f"⚠️ Не удалось загрузить pymorphy3: {e}")
            self.morph = None
    
    def _load_patterns(self, patterns_file: str):
        """
        Загружает паттерны из Excel файла
        
        Args:
            patterns_file: Путь к Excel файлу с паттернами
        """
        if not os.path.exists(patterns_file):
            raise FileNotFoundError(f"Файл паттернов не найден: {patterns_file}")
        
        try:
            df = pd.read_excel(patterns_file)
            
            for _, row in df.iterrows():
                category = row['category']
                pattern = row['pattern']
                pattern_type = row['pattern_type']
                confidence = float(row.get('confidence', 0.7))
                context_required = bool(row.get('context_required', True))
                description = row.get('description', '')
                
                # Группируем по категориям
                if category not in self.patterns:
                    self.patterns[category] = []
                    self.pattern_configs[category] = []
                
                self.patterns[category].append(pattern)
                self.pattern_configs[category].append({
                    'pattern': pattern,
                    'pattern_type': pattern_type,
                    'confidence': confidence,
                    'context_required': context_required,
                    'description': description
                })
            
            print(f"✅ Загружено {len(df)} NLP паттернов из {patterns_file}")
            
        except Exception as e:
            print(f"❌ Ошибка загрузки паттернов: {e}")
            raise
    
    def _setup_matchers(self):
        """Настраивает spaCy Matcher и PhraseMatcher с кастомными правилами"""
        self.matcher = Matcher(self.nlp.vocab)
        self.phrase_matcher = PhraseMatcher(self.nlp.vocab, attr="LOWER")
        
        # Добавляем паттерны в матчеры
        for category, patterns in self.patterns.items():
            for i, pattern_text in enumerate(patterns):
                config = self.pattern_configs[category][i]
                
                if config['pattern_type'] == 'regex':
                    # Для regex паттернов используем отдельную обработку
                    continue
                elif config['pattern_type'] == 'spacy_context':
                    # Добавляем контекстные паттерны
                    self._add_context_patterns(category, pattern_text)
        
        # Настраиваем кастомные фразы для специфических терминов
        self._setup_custom_phrases()
        
        # Настраиваем кастомные правила Matcher для сложных паттернов
        self._setup_custom_matchers()
    
    def _setup_custom_phrases(self):
        """Настраивает PhraseMatcher для специфических терминов"""
        
        # Должности и роли (расширенный список)
        positions = [
            # Руководящие должности
            "генеральный директор", "исполнительный директор", "директор",
            "заместитель директора", "зам директора", "зам. директора",
            "начальник", "руководитель", "заведующий", "управляющий",
            
            # Менеджмент
            "менеджер", "старший менеджер", "ведущий менеджер",
            "менеджер по продажам", "менеджер по персоналу", "hr менеджер",
            "проект менеджер", "продакт менеджер",
            
            # Специалисты
            "специалист", "ведущий специалист", "старший специалист",
            "главный специалист", "консультант", "эксперт", "аналитик",
            
            # IT должности
            "программист", "разработчик", "системный администратор",
            "сисадмин", "devops", "тестировщик", "аналитик данных",
            "архитектор", "техлид", "team lead",
            
            # Финансы и учет
            "бухгалтер", "главный бухгалтер", "экономист", "финансист",
            "казначей", "аудитор", "контролер",
            
            # Юридические должности
            "юрист", "корпоративный юрист", "правовед", "юрисконсульт",
            
            # Кадры и HR
            "кадровик", "hr", "рекрутер", "специалист по кадрам",
            
            # Производство
            "инженер", "главный инженер", "технолог", "мастер",
            "начальник смены", "супервайзер", "оператор",
            
            # Прочее
            "секретарь", "помощник", "ассистент", "координатор",
            "администратор", "делопроизводитель"
        ]
        
        # Типы организаций
        organization_types = [
            "общество с ограниченной ответственностью", "ооо",
            "акционерное общество", "ао", "пао", "зао",
            "индивидуальный предприниматель", "ип",
            "государственное унитарное предприятие", "гуп",
            "муниципальное унитарное предприятие", "муп",
            "некоммерческая организация", "нко",
            "автономная некоммерческая организация", "ано",
            "учреждение", "бюджетное учреждение", "казенное учреждение"
        ]
        
        # Подразделения
        departments = [
            "отдел", "управление", "департамент", "служба", "сектор",
            "группа", "команда", "подразделение", "филиал", "представительство",
            "отдел кадров", "бухгалтерия", "финансовый отдел",
            "it отдел", "отдел продаж", "маркетинг", "pr отдел"
        ]
        
        # Финансовые термины
        financial_terms = [
            "заработная плата", "зарплата", "оклад", "доход", "заработок",
            "выплата", "премия", "бонус", "надбавка", "компенсация",
            "стипендия", "пенсия", "пособие", "субсидия"
        ]
        
        # Медицинские термины
        medical_terms = [
            "диагноз", "заболевание", "болезнь", "лечение", "терапия",
            "операция", "процедура", "анализ", "обследование",
            "медицинская карта", "история болезни", "рецепт"
        ]
        
        # Конфиденциальные термины
        confidential_terms = [
            "коммерческая тайна", "конфиденциально", "секретно",
            "ноу-хау", "служебная информация", "внутренняя информация",
            "персональные данные", "чувствительная информация"
        ]
        
        # Добавляем фразы в PhraseMatcher
        phrase_categories = {
            'position': positions,
            'organization': organization_types,
            'department': departments,
            'salary': financial_terms,
            'health_info': medical_terms,
            'trade_secret': confidential_terms
        }
        
        for category, phrases in phrase_categories.items():
            if phrases:
                # Создаем документы для фраз
                phrase_docs = [self.nlp(phrase) for phrase in phrases]
                # Добавляем в matcher
                self.phrase_matcher.add(f"{category}_phrases", phrase_docs)
                
                # Сохраняем для справки
                self.custom_phrases[category] = phrases
        
        print(f"✅ Настроено {len(phrase_categories)} категорий кастомных фраз")
    
    def _setup_custom_matchers(self):
        """Настраивает кастомные правила Matcher для сложных паттернов"""
        
        # Паттерн для ФИО: PROPN PROPN PROPN (Фамилия Имя Отчество)
        fio_pattern = [
            {"POS": "PROPN", "IS_TITLE": True},
            {"POS": "PROPN", "IS_TITLE": True},
            {"POS": "PROPN", "IS_TITLE": True}
        ]
        self.matcher.add("full_name", [fio_pattern])
        
        # Паттерн для сокращенных имен: PROPN "." PROPN "." (И.О.)
        initials_pattern = [
            {"POS": "PROPN", "LENGTH": 1},
            {"TEXT": "."},
            {"POS": "PROPN", "LENGTH": 1},
            {"TEXT": "."},
            {"POS": "PROPN", "IS_TITLE": True}
        ]
        self.matcher.add("initials_lastname", [initials_pattern])
        
        # Паттерн для организаций с юр.формой
        org_pattern = [
            {"LOWER": {"IN": ["ооо", "ао", "пао", "зао", "ип", "гуп", "муп"]}},
            {"TEXT": {"IN": ["\"", "«", "'"]}},
            {"POS": {"IN": ["NOUN", "PROPN"]}, "OP": "+"},
            {"TEXT": {"IN": ["\"", "»", "'"]}},
        ]
        self.matcher.add("quoted_organization", [org_pattern])
        
        print("✅ Настроены кастомные правила Matcher")
    
    def _add_context_patterns(self, category: str, pattern_text: str):
        """Добавляет контекстные паттерны в матчеры"""
        # Этот метод теперь упрощен, так как основные паттерны добавляются в _setup_custom_phrases
        pass
    
    def find_sensitive_data(self, text: str) -> List[Dict[str, Any]]:
        """
        Находит чувствительные данные в тексте
        
        Args:
            text: Текст для анализа
            
        Returns:
            Список найденных чувствительных данных
        """
        if not text or not isinstance(text, str):
            return []
        
        # Обрабатываем текст через spaCy
        doc = self.nlp(text)
        
        detections = []
        
        # 1. spaCy NER
        detections.extend(self._extract_spacy_entities(doc))
        
        # 2. Regex паттерны
        detections.extend(self._extract_regex_patterns(text))
        
        # 3. Контекстные матчеры
        detections.extend(self._extract_context_matches(doc))
        
        # 4. Морфологический анализ для имен
        detections.extend(self._extract_morphological_names(doc))
        
        # 5. Кастомные матчеры
        detections.extend(self._extract_custom_matches(doc))
        
        # Удаляем дубликаты и фильтруем по confidence
        unique_detections = self._deduplicate_detections(detections)
        
        # Фильтруем по минимальному уровню уверенности
        filtered_detections = [
            d for d in unique_detections 
            if d['confidence'] >= self.confidence_threshold
        ]
        
        return filtered_detections
    
    def _extract_spacy_entities(self, doc: Doc) -> List[Dict[str, Any]]:
        """Извлекает именованные сущности через spaCy NER"""
        entities = []
        
        for ent in doc.ents:
            # Маппинг spaCy меток на наши категории
            category_map = {
                'PER': 'person_name',
                'PERSON': 'person_name', 
                'ORG': 'organization',
                'LOC': 'location',
                'GPE': 'location'  # Geopolitical entity
            }
            
            if ent.label_ in category_map:
                category = category_map[ent.label_]
                
                # Детализируем метод spaCy NER
                method_detail = f"spacy_ner_{ent.label_.lower()}"
                
                detection = {
                    'category': category,
                    'original_value': ent.text,
                    'confidence': 0.8,  # spaCy NER обычно надежный
                    'position': {
                        'start': ent.start_char,
                        'end': ent.end_char
                    },
                    'method': method_detail,
                    'spacy_label': ent.label_,  # Добавляем оригинальную метку spaCy
                    'uuid': str(uuid.uuid4())
                }
                entities.append(detection)
        
        return entities
    
    def _extract_regex_patterns(self, text: str) -> List[Dict[str, Any]]:
        """Извлекает данные через regex паттерны"""
        detections = []
        
        for category, configs in self.pattern_configs.items():
            for config in configs:
                if config['pattern_type'] != 'regex' or not config['pattern']:
                    continue
                
                try:
                    pattern = config['pattern']
                    
                    # Для категории person_name не используем IGNORECASE, 
                    # чтобы избежать ложных срабатываний на обычных словах
                    if category == 'person_name':
                        matches = re.finditer(pattern, text, re.UNICODE)
                    else:
                        matches = re.finditer(pattern, text, re.IGNORECASE | re.UNICODE)
                    
                    for match in matches:
                        # Проверяем контекст если требуется
                        if config['context_required']:
                            if not self._validate_context(text, match, category):
                                continue
                        
                        detection = {
                            'category': category,
                            'original_value': match.group(),
                            'confidence': config['confidence'],
                            'position': {
                                'start': match.start(),
                                'end': match.end()
                            },
                            'method': 'regex',
                            'uuid': str(uuid.uuid4())
                        }
                        detections.append(detection)
                
                except re.error as e:
                    print(f"⚠️ Ошибка regex паттерна {category}: {e}")
                    continue
        
        return detections
    
    def _extract_context_matches(self, doc: Doc) -> List[Dict[str, Any]]:
        """Извлекает данные через контекстные матчеры"""
        detections = []
        
        # Используем phrase matcher
        matches = self.phrase_matcher(doc)
        
        for match_id, start, end in matches:
            span = doc[start:end]
            label = self.nlp.vocab.strings[match_id]
            
            # Извлекаем категорию из метки
            category = label.split('_')[0] if '_' in label else label
            
            detection = {
                'category': category,
                'original_value': span.text,
                'confidence': 0.7,
                'position': {
                    'start': span.start_char,
                    'end': span.end_char
                },
                'method': 'phrase_matcher',
                'uuid': str(uuid.uuid4())
            }
            detections.append(detection)
        
        return detections
    
    def _extract_morphological_names(self, doc: Doc) -> List[Dict[str, Any]]:
        """Извлекает имена через морфологический анализ с pymorphy3"""
        detections = []
        
        # Ищем потенциальные имена по морфологическим признакам
        for token in doc:
            # Пропускаем стоп-слова, пунктуацию и короткие токены
            if token.is_stop or token.is_punct or len(token.text) < 2:
                continue
            
            # Ищем слова с большой буквы (потенциальные имена)
            if token.text[0].isupper() and token.pos_ == 'PROPN':
                # Используем pymorphy3 для более точного анализа
                if self.morph and self._is_likely_person_name_morph(token.text):
                    detection = {
                        'category': 'person_name',
                        'original_value': token.text,
                        'confidence': 0.7,  # Средняя уверенность для морфологического анализа
                        'position': {
                            'start': token.idx,
                            'end': token.idx + len(token.text)
                        },
                        'method': 'morphological_enhanced',
                        'uuid': str(uuid.uuid4())
                    }
                    detections.append(detection)
                elif self._is_likely_person_name(token, doc):
                    # Fallback на старый метод
                    detection = {
                        'category': 'person_name',
                        'original_value': token.text,
                        'confidence': 0.6,
                        'position': {
                            'start': token.idx,
                            'end': token.idx + len(token.text)
                        },
                        'method': 'morphological',
                        'uuid': str(uuid.uuid4())
                    }
                    detections.append(detection)
        
        return detections
    
    def _is_likely_person_name_morph(self, word: str) -> bool:
        """Проверяет слово на принадлежность к именам с помощью pymorphy3"""
        if not self.morph:
            return False
        
        try:
            # Анализируем слово
            parsed = self.morph.parse(word)
            
            for parse in parsed:
                # Проверяем теги
                if 'Name' in parse.tag or 'Surn' in parse.tag or 'Patr' in parse.tag:
                    return True
                # Также проверяем одушевленные существительные
                if 'NOUN' in parse.tag and 'anim' in parse.tag:
                    return True
            
            return False
            
        except Exception:
            return False
    
    def _extract_custom_matches(self, doc: Doc) -> List[Dict[str, Any]]:
        """Извлекает данные через кастомные spaCy матчеры"""
        detections = []
        
        # Используем Matcher для сложных паттернов
        matches = self.matcher(doc)
        
        for match_id, start, end in matches:
            span = doc[start:end]
            label = self.nlp.vocab.strings[match_id]
            
            # Определяем категорию по метке
            if label == "full_name" or label == "initials_lastname":
                category = "person_name"
                confidence = 0.9  # Высокая уверенность для структурированных имен
            elif label == "quoted_organization":
                category = "organization"
                confidence = 0.85
            else:
                category = "unknown"
                confidence = 0.5
            
            detection = {
                'category': category,
                'original_value': span.text,
                'confidence': confidence,
                'position': {
                    'start': span.start_char,
                    'end': span.end_char
                },
                'method': 'custom_matcher',
                'uuid': str(uuid.uuid4())
            }
            detections.append(detection)
        
        return detections
    
    def _validate_context(self, text: str, match: re.Match, category: str) -> bool:
        """Валидирует контекст найденного совпадения"""
        # Получаем контекст вокруг совпадения
        start = max(0, match.start() - 50)
        end = min(len(text), match.end() + 50)
        context = text[start:end].lower()
        
        # Контекстные слова для разных категорий
        context_keywords = {
            'salary': ['зарплата', 'оклад', 'доход', 'заработок', 'выплата'],
            'health_info': ['диагноз', 'лечение', 'болезнь', 'медицин', 'больниц'],
            'contract_info': ['номер', 'договор', 'контракт', 'соглашение'],
            'financial_amount': ['стоимость', 'цена', 'сумма', 'оплата', 'платеж']
        }
        
        if category in context_keywords:
            keywords = context_keywords[category]
            return any(keyword in context for keyword in keywords)
        
        return True  # По умолчанию разрешаем
    
    def _is_likely_person_name(self, token: Token, doc: Doc) -> bool:
        """Проверяет, является ли токен вероятным именем человека"""
        # Простая эвристика: 
        # 1. Большая буква в начале
        # 2. Не является известным словом (не в словаре)
        # 3. Окружен другими именами или контекстными словами
        
        if not token.text[0].isupper():
            return False
        
        # Проверяем наличие контекстных слов рядом
        context_words = ['господин', 'госпожа', 'товарищ', 'коллега', 
                        'сотрудник', 'работник', 'специалист']
        
        # Смотрим на соседние токены
        start_idx = max(0, token.i - 2)
        end_idx = min(len(doc), token.i + 3)
        
        nearby_text = ' '.join([t.text.lower() for t in doc[start_idx:end_idx]])
        
        return any(word in nearby_text for word in context_words)
    
    def _deduplicate_detections(self, detections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Удаляет дубликаты обнаружений"""
        unique_detections = []
        seen_positions = set()
        
        # Сортируем по позиции для стабильности
        detections.sort(key=lambda x: x['position']['start'])
        
        for detection in detections:
            pos_key = (detection['position']['start'], detection['position']['end'])
            
            # Проверяем перекрытие с уже добавленными
            overlaps = False
            for seen_start, seen_end in seen_positions:
                if (detection['position']['start'] < seen_end and 
                    detection['position']['end'] > seen_start):
                    overlaps = True
                    break
            
            if not overlaps:
                unique_detections.append(detection)
                seen_positions.add(pos_key)
        
        return unique_detections