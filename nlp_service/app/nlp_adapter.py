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

try:
    from nlp_config import NLPConfig
    from detection_strategies import DetectionStrategyFactory
    from detection_factory import DetectionMethodFactory
    from text_normalizer import TextNormalizer
    from smart_phrase_matcher import SmartPhraseMatcher
except ImportError:
    import sys
    import os
    sys.path.append(os.path.dirname(__file__))
    from nlp_config import NLPConfig
    from detection_strategies import DetectionStrategyFactory
    from detection_factory import DetectionMethodFactory
    from text_normalizer import TextNormalizer
    from smart_phrase_matcher import SmartPhraseMatcher


class NLPAdapter:
    def _is_valid_person_name_regex(self, match_text: str) -> bool:
        """Проверяет, что совпадение по regex действительно похоже на ФИО с помощью морфологии"""
        if not self.morph:
            return True  # Если морфология не инициализирована, не фильтруем
        words = match_text.split()
        if len(words) != 3:
            return False
        noun_count = 0
        animate_count = 0
        for word in words:
            parses = self.morph.parse(word)
            if not parses:
                continue
            best = parses[0]
            if 'NOUN' in best.tag:
                noun_count += 1
                if 'anim' in best.tag:
                    animate_count += 1
        # Требуем, чтобы все три слова были существительными и хотя бы два — одушевлённые
        return noun_count == 3 and animate_count >= 2
    """
    Адаптер для обработки неструктурированных именованных сущностей
    """
    
    def __init__(self, config_path: Optional[str] = None, patterns_file: Optional[str] = None, confidence_threshold: Optional[float] = None):
        """
        Инициализация NLP адаптера
        
        Args:
            config_path: Путь к файлу конфигурации. Если None, использует дефолтный
            patterns_file: Путь к файлу с паттернами. Если None, использует из конфига
            confidence_threshold: Минимальный уровень уверенности. Если None, использует из конфига
        """
        # Загружаем конфигурацию
        self.config = NLPConfig(config_path)
        
        # Инициализируем нормализатор текста
        self.text_normalizer = TextNormalizer()
        
        # Словарь умных phrase матчеров для разных категорий
        self.smart_phrase_matchers = {}
        
        # Инициализируем переменные
        self.nlp = None
        self.matcher = None
        self.phrase_matcher = None
        self.morph = None  # pymorphy3 анализатор
        self.patterns = {}
        self.pattern_configs = {}
        
        # Флаг для ленивой загрузки lemmatizer (оптимизация производительности)
        self._lemmatizer_enabled = False
        
        # Устанавливаем порог уверенности
        self.confidence_threshold = confidence_threshold or self.config.get_global_confidence_threshold()
        
        # Специальные термины для PhraseMatcher
        self.custom_phrases = {}
        
        # Загружаем spaCy модель
        self._load_spacy_model()
        
        # Инициализируем морфологический анализатор
        if self.config.is_morphology_enabled():
            self._init_morphology()
        
        # Загружаем паттерны
        patterns_file_path = patterns_file or self.config.get_patterns_file_path()
        self._load_patterns(patterns_file_path)
        
        # Настраиваем матчеры
        self._setup_matchers()
        
        # Инициализируем централизованную систему детекции
        self.detection_factory = DetectionMethodFactory(self.config)
        
        # Инициализируем и кешируем стратегию информационных систем
        self._is_strategy = None
        self._init_information_system_strategy()

        # === Загрузка справочников имен и фамилий ===
        from fio_dictionaries import load_dictionary
        dict_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'patterns'))
        self.male_names = load_dictionary(os.path.join(dict_dir, 'male_names_rus.txt'))
        self.female_names = load_dictionary(os.path.join(dict_dir, 'female_names_rus.txt'))
        self.surnames = load_dictionary(os.path.join(dict_dir, 'male_surnames_rus.txt'))
        # Можно добавить объединение с женскими фамилиями, если появятся

    def _fio_dictionary_filter(self, match_text: str) -> bool:
        """Проверяет, что ФИО (или часть) действительно содержит имя и фамилию из справочников с учетом лемматизации (любые падежи).
        Для паттернов с инициалами (например, 'Фамилия И.О.') фильтруется только фамилия."""
        if not self.morph:
            return False
        words = match_text.split()
        names_set = self.male_names.union(self.female_names)
        # Унификация: все сравнения через "е" вместо "ё"
        def norm(s):
            return s.replace("ё", "е").replace("Ё", "Е")

        def get_lemma(word, prefer_tag=None):
            """Вернуть нормальную форму слова с нужным тегом (Surn/Name/Patr), иначе первую"""
            parses = self.morph.parse(word)
            if prefer_tag:
                for p in parses:
                    if prefer_tag in p.tag:
                        return norm(p.normal_form.capitalize())
            return norm(parses[0].normal_form.capitalize() if parses else word)
        def is_initials(word):
            return bool(len(word) == 4 and word[1] == '.' and word[3] == '.' and word[0].isupper() and word[2].isupper())
        # Фамилия инициалы ("Сидоров А.В.")
        if len(words) == 2 and is_initials(words[1]):
            fam_lemma = get_lemma(words[0], prefer_tag='Surn')
            return fam_lemma in self.surnames
        # Инициалы фамилия ("А.В. Смирнов")
        if len(words) == 2 and is_initials(words[0]):
            fam_lemma = get_lemma(words[1], prefer_tag='Surn')
            return fam_lemma in self.surnames
        # Фамилия инициалы инициалы (редко, но поддержим)
        if len(words) == 3 and is_initials(words[1]) and is_initials(words[2]):
            fam_lemma = get_lemma(words[0], prefer_tag='Surn')
            return fam_lemma in self.surnames
        # Инициалы инициалы фамилия ("А.В. М.П. Козлова" — экзотика, но поддержим)
        if len(words) == 3 and is_initials(words[0]) and is_initials(words[1]):
            fam_lemma = get_lemma(words[2], prefer_tag='Surn')
            return fam_lemma in self.surnames
        # Обычная логика для ФИО
        # Для полного ФИО: ищем фамилию и имя по нужным тегам
        if len(words) == 3:
            fam = get_lemma(words[0], prefer_tag='Surn')
            name = get_lemma(words[1], prefer_tag='Name')
            otch = get_lemma(words[2], prefer_tag='Patr')
            return (
                (fam in self.surnames and name in names_set) or
                (name in names_set and fam in self.surnames)
            )
        elif len(words) == 2:
            a = get_lemma(words[0], prefer_tag='Surn')
            b = get_lemma(words[1], prefer_tag='Name')
            return (
                (a in self.surnames and b in names_set) or
                (b in self.surnames and a in names_set)
            )
        elif len(words) == 1:
            l = get_lemma(words[0])
            return (
                l in self.surnames or l in names_set
            )
        return False
    
    def _load_spacy_model(self):
        """Загружает русскую spaCy модель согласно конфигурации"""
        preferred_models = self.config.get_spacy_models()
        fallback_error = self.config.get_spacy_fallback_error()
        
        for model_name in preferred_models:
            try:
                # ОПТИМИЗАЦИЯ: Загружаем модель БЕЗ lemmatizer (экономим 53% времени)
                # Lemmatizer будет добавлен динамически только для person_name категории
                self.nlp = spacy.load(model_name, exclude=["lemmatizer"])
                # if self.config.should_log_model_loading():
                #     pass
                return
            except OSError:
                continue
        
        # Если ни одна модель не загрузилась
        raise RuntimeError(fallback_error)
    
    def _init_morphology(self):
        """Инициализирует морфологический анализатор pymorphy3"""
        try:
            self.morph = pymorphy3.MorphAnalyzer()
            # if self.config.should_log_model_loading():
            #     pass
        except Exception as e:
            self.morph = None
    
    def _ensure_lemmatizer_enabled(self):
        """
        ОПТИМИЗАЦИЯ: Включает lemmatizer только при первом вызове для person_name
        
        Lemmatizer занимает 53% времени обработки, но используется только для
        морфологической детекции person_name. Для остальных категорий (information_system,
        organization, address) он не нужен и только замедляет работу.
        
        Включение происходит один раз и остается активным для последующих вызовов.
        """
        if not self._lemmatizer_enabled:
            try:
                # Добавляем lemmatizer в pipeline после parser
                if "lemmatizer" not in self.nlp.pipe_names:
                    self.nlp.add_pipe("lemmatizer", after="parser")
                self._lemmatizer_enabled = True
            except Exception as e:
                # Если не удалось добавить lemmatizer, продолжаем без него
                pass
    
    def _load_patterns(self, patterns_file: str):
        """
        Загружает паттерны из JSON-файла
        Args:
            patterns_file: Путь к JSON-файлу с паттернами
        """
        if not os.path.exists(patterns_file):
            raise FileNotFoundError(f"Файл паттернов не найден: {patterns_file}")
        try:
            import json
            with open(patterns_file, encoding="utf-8") as f:
                data = json.load(f)
            patterns = data["patterns"]
            for row in patterns:
                category = row['category']
                pattern = row['pattern']
                pattern_type = row.get('type') or row.get('pattern_type')
                confidence = float(row.get('confidence', self.config.get_default_pattern_confidence()))
                context_required = bool(row.get('context_required', True))
                description = row.get('description', '')
                if not pattern and pattern_type == 'regex':
                    continue
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
            # if self.config.should_log_pattern_loading():
            #     pass
        except Exception as e:
            raise
    
    def _setup_matchers(self):
        """Настраивает spaCy Matcher и PhraseMatcher с кастомными правилами"""
        self.matcher = Matcher(self.nlp.vocab)
        self.phrase_matcher = PhraseMatcher(self.nlp.vocab, attr=self.config.get_phrase_matcher_attr())
        
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
        
        # Все списки фраз теперь берём из JSON/настроек
        phrase_categories = self.config.get_phrase_categories_from_json()
        for category, phrases in phrase_categories.items():
            if phrases:
                phrase_docs = [self.nlp(phrase) for phrase in phrases]
                self.phrase_matcher.add(f"{category}_phrases", phrase_docs)
                self.custom_phrases[category] = phrases
        self._setup_smart_phrase_matchers()
    
    def _setup_smart_phrase_matchers(self):
        """Настраивает умные phrase матчеры для сложных категорий"""
        try:
            # Создаем умный матчер для государственных организаций
            if 'government_org' in self.custom_phrases:
                gov_org_patterns = {'government_org': self.custom_phrases['government_org']}
                
                self.smart_phrase_matchers['government_org'] = SmartPhraseMatcher(
                    nlp=self.nlp,
                    patterns_dict=gov_org_patterns,
                    category='government_org'
                )
                
            
            # Можно добавить умные матчеры для других категорий при необходимости
            
        except Exception as e:
            # Продолжаем работу без умных матчеров
            pass
    
    def _load_government_organizations(self) -> List[str]:
        """Загружает расширенный список государственных организаций"""
        try:
            # Пытаемся загрузить из файла government_organizations.py
            import sys
            patterns_dir = os.path.join(os.path.dirname(__file__), '..', 'patterns')
            sys.path.insert(0, patterns_dir)
            
            from government_organizations import GOVERNMENT_ORGANIZATIONS
            
            # if self.config.should_log_pattern_loading():
            #     pass
            
            return GOVERNMENT_ORGANIZATIONS
            
        except ImportError:
            # Fallback - базовый список из конфигурации
            fallback_orgs = [
                "министерство", "департамент", "управление", "служба", "комитет",
                "администрация", "правительство", "дума", "совет",
                "федеральная служба", "государственная дума", 
                "совет федерации", "правительство российской федерации"
            ]
            
            # if self.config.should_log_pattern_loading():
            #     pass
            
            return fallback_orgs
    
    def _setup_custom_matchers(self):
        """Настраивает кастомные правила Matcher для сложных паттернов"""
        
        # Паттерн для ФИО: PROPN PROPN PROPN (Фамилия Имя Отчество)
        fio_pattern = [
            {"POS": "PROPN", "IS_TITLE": True},
            {"POS": "PROPN", "IS_TITLE": True},
            {"POS": "PROPN", "IS_TITLE": True}
        ]
        self.matcher.add("full_name", [fio_pattern])
        
        # ИСПРАВЛЕННЫЕ паттерны для инициалов (И. О. Фамилия)
        # Вариант 1: Токены типа "А." (POS может быть PROPN или PUNCT)
        initials_pattern_v1 = [
            {"TEXT": {"REGEX": r"^[А-ЯЁ]\.$"}},  # Первый инициал с точкой
            {"TEXT": {"REGEX": r"^[А-ЯЁ]\.$"}},  # Второй инициал с точкой
            {"POS": "PROPN", "LENGTH": {">": 2}}  # Фамилия (длиннее 2 символов)
        ]
        self.matcher.add("initials_lastname_v1", [initials_pattern_v1])
        
        # Вариант 2: Фамилия + инициалы (Фамилия И. О.)
        lastname_initials_pattern = [
            {"POS": "PROPN", "LENGTH": {">": 2}},  # Фамилия
            {"TEXT": {"REGEX": r"^[А-ЯЁ]\.$"}},  # Первый инициал
            {"TEXT": {"REGEX": r"^[А-ЯЁ]\.$"}}   # Второй инициал
        ]
        self.matcher.add("lastname_initials", [lastname_initials_pattern])
        
        # Паттерн для организаций с юр.формой
        org_pattern = [
            {"LOWER": {"IN": ["ооо", "ао", "пао", "зао", "ип", "гуп", "муп"]}},
            {"TEXT": {"IN": ["\"", "«", "'"]}},
            {"POS": {"IN": ["NOUN", "PROPN"]}, "OP": "+"},
            {"TEXT": {"IN": ["\"", "»", "'"]}},
        ]
        self.matcher.add("quoted_organization", [org_pattern])
        
    
    def _add_context_patterns(self, category: str, pattern_text: str):
        """Добавляет контекстные паттерны в матчеры"""
        # Этот метод теперь упрощен, так как основные паттерны добавляются в _setup_custom_phrases
        pass
    
    def find_sensitive_data(self, text: str) -> List[Dict[str, Any]]:
        """
        Находит чувствительные данные в тексте используя централизованную логику
        
        Args:
            text: Текст для анализа
            
        Returns:
            Список найденных чувствительных данных
        """
        if not text or not isinstance(text, str):
            return []


        # Сохраняем оригинальный текст для mapping позиций
        original_text = text
        
        # КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Нормализуем неразрывные пробелы для правильной токенизации
        # Заменяем \xa0 (неразрывный пробел) на обычный пробел
        processing_text = original_text.replace('\xa0', ' ')
        
        # ОПТИМИЗАЦИЯ: Включаем lemmatizer заранее только если будет обработка person_name
        # (единственная категория использующая morphological метод)
        available_categories = self.config.get_available_categories()
        if 'person_name' in available_categories:
            enabled_methods = self.config.get_enabled_methods_for_category('person_name')
            if 'morphological' in enabled_methods:
                self._ensure_lemmatizer_enabled()
        
        # Обрабатываем текст через spaCy один раз для всех методов
        doc = self.nlp(processing_text)
        
        # Получаем все доступные категории из конфигурации
        available_categories = self.config.get_available_categories()
        
        all_detections = []
        
        # Обрабатываем каждую категорию отдельно с её настройками
        for category in available_categories:
            category_detections = self._detect_for_category(category, processing_text, doc)
            
            # Позиции уже корректны, так как используем оригинальный текст
            
            # if category_detections:
            #     pass
            # else:
            #     pass
            all_detections.extend(category_detections)
        
        
        # Финальная дедупликация между категориями
        final_detections = self._global_deduplicate(all_detections)
        
        # Фильтруем по глобальному confidence threshold
        filtered_detections = [
            detection for detection in final_detections
            if detection.get('confidence', 0) >= self.confidence_threshold
        ]
        
        return filtered_detections
    
    def _detect_for_category(self, category: str, text: str, doc: Doc) -> List[Dict[str, Any]]:
        """
        Выполняет детекцию для конкретной категории используя её настройки
        
        Args:
            category: Категория для поиска
            text: Исходный текст
            doc: Обработанный spaCy документ
            
        Returns:
            Список детекций для категории
        """
        # Получаем настройки для категории
        enabled_methods = self.config.get_enabled_methods_for_category(category)
        strategy_name = self.config.get_detection_strategy_name(category)
        max_results = self.config.get_max_results_for_category(category)
        
        if not enabled_methods:
            return []
        
        # Собираем результаты по методам с учетом приоритетов
        results_by_method = {}
        priority_order = self.config.get_method_priority_order(category)
        
        # Создаем список методов с их приоритетами
        methods_with_priority = list(zip(enabled_methods, priority_order)) if priority_order else [(m, 1) for m in enabled_methods]
        methods_with_priority.sort(key=lambda x: x[1])  # Сортируем по приоритету
        
        for method, priority in methods_with_priority:
            method_results = self._execute_detection_method(method, category, text, doc)
            
            if method_results:
                results_by_method[method] = method_results
                
                # Проверяем early exit
                if self._should_early_exit(category, method, method_results):
                    # if self.config.should_log_detection_stats():
                    #     pass
                    break
        
        # Применяем стратегию комбинирования
        strategy_settings = self.config.get_detection_strategy_settings(strategy_name)
        
        # Для информационных систем используем кешированную стратегию
        if strategy_name == 'information_system' and self._is_strategy is not None:
            strategy = self._is_strategy
        else:
            strategy = DetectionStrategyFactory.create_strategy(strategy_name, strategy_settings)
        
        combined_results = strategy.combine_results(results_by_method)
        
        # Ограничиваем количество результатов
        if len(combined_results) > max_results:
            # Сортируем по confidence и берем лучшие
            combined_results.sort(key=lambda x: x.get('confidence', 0), reverse=True)
            combined_results = combined_results[:max_results]
        
        return combined_results
    
    def _execute_detection_method(self, method: str, category: str, text: str, doc: Doc) -> List[Dict[str, Any]]:
        """
        Выполняет конкретный метод обнаружения для категории
        
        Args:
            method: Название метода
            category: Категория для поиска
            text: Исходный текст  
            doc: Обработанный spaCy документ
            
        Returns:
            Результаты метода
        """
        method_settings = self.config.get_method_settings(category, method)
        min_confidence = self.config.get_min_confidence_for_method(category, method)
        
        results = []
        
        try:
            if method == 'spacy_ner':
                results = self._extract_spacy_entities_for_category(doc, category)
            elif method == 'regex':
                results = self._extract_regex_patterns_for_category(text, category)
            elif method == 'morphological':
                results = self._extract_morphological_names_for_category(doc, category)
            elif method == 'custom_matcher':
                results = self._extract_custom_matches_for_category(doc, category)
            elif method == 'phrase_matcher':
                results = self._extract_context_matches_for_category(doc, category)
            elif method == 'context_matcher':
                results = self._extract_context_matches_for_category(doc, category)
            else:
                # if self.config.should_log_detection_stats():
                #     pass
                return []
            
            # Фильтруем по минимальной confidence для метода
            filtered_results = [r for r in results if r.get('confidence', 0) >= min_confidence]
            
            return filtered_results
            
        except Exception as e:
            # if self.config.should_log_detection_stats():
            #     pass
            return []
    
    def _should_early_exit(self, category: str, method: str, results: List[Dict[str, Any]]) -> bool:
        """
        Определяет, нужно ли делать early exit после данного метода
        
        Args:
            category: Категория
            method: Метод
            results: Результаты метода
            
        Returns:
            True если нужен early exit
        """
        # Отключаем early exit для government_org, чтобы использовать гибридную стратегию
        if category == 'government_org':
            return False
            
        if not results:
            return False
        
        early_exit_threshold = self.config.get_early_exit_threshold(category, method)
        
        # Проверяем, есть ли результаты с высокой confidence
        for result in results:
            if result.get('confidence', 0) >= early_exit_threshold:
                return True
        
        return False
    
    def _global_deduplicate(self, all_detections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Глобальная дедупликация между всеми категориями
        
        Args:
            all_detections: Все найденные детекции
            
        Returns:
            Дедуплицированный список
        """
        if not all_detections:
            return []
        
        # Группируем по перекрывающимся позициям
        deduplicated = []
        used_indices = set()
        
        for i, detection in enumerate(all_detections):
            if i in used_indices:
                continue
            
            # Ищем перекрывающиеся детекции
            overlapping_group = [detection]
            used_indices.add(i)
            
            for j, other_detection in enumerate(all_detections[i+1:], i+1):
                if j in used_indices:
                    continue
                
                if self._detections_overlap(detection, other_detection):
                    overlapping_group.append(other_detection)
                    used_indices.add(j)
            
            # Выбираем лучшую детекцию из группы
            best_detection = max(overlapping_group, key=lambda x: x.get('confidence', 0))
            deduplicated.append(best_detection)
        
        return deduplicated
    
    def _detections_overlap(self, det1: Dict[str, Any], det2: Dict[str, Any], threshold: float = 0.5) -> bool:
        """
        Проверяет, перекрываются ли две детекции
        
        Args:
            det1, det2: Детекции для сравнения
            threshold: Порог перекрытия
            
        Returns:
            True если перекрываются
        """
        pos1 = det1.get('position', {})
        pos2 = det2.get('position', {})
        
        start1, end1 = pos1.get('start', 0), pos1.get('end', 0)
        start2, end2 = pos2.get('start', 0), pos2.get('end', 0)
        
        overlap_start = max(start1, start2)
        overlap_end = min(end1, end2)
        
        if overlap_start >= overlap_end:
            return False
        
        overlap_length = overlap_end - overlap_start
        min_length = min(end1 - start1, end2 - start2)
        
        return (overlap_length / min_length) >= threshold if min_length > 0 else False
    
    def _extract_spacy_entities(self, doc: Doc) -> List[Dict[str, Any]]:
        """Извлекает именованные сущности через spaCy NER"""
        entities = []
        
        # Маппинг spaCy меток на наши категории из конфига
        category_map = self.config.get_spacy_entity_mapping()
        
        for ent in doc.ents:
            if ent.label_ in category_map:
                category = category_map[ent.label_]
                
                # Детализируем метод spaCy NER
                method_detail = f"spacy_ner_{ent.label_.lower()}"
                
                detection = {
                    'category': category,
                    'original_value': ent.text,
                    'confidence': self.config.get_spacy_ner_confidence(),
                    'position': {
                        'start': ent.start_char,
                        'end': ent.end_char
                    },
                    'method': method_detail,
                    'spacy_label': ent.label_,  # Добавляем оригинальную метку spaCy
                    'uuid': 'placeholder'  # Временный placeholder, UUID будет генерироваться централизованно в FormatterApplier
                }
                entities.append(detection)
        
        return entities
    
    def _extract_spacy_entities_for_category(self, doc: Doc, category: str) -> List[Dict[str, Any]]:
        """Извлекает spaCy NER сущности для конкретной категории"""
        entities = []
        
        # Специальная обработка для информационных систем
        if category == 'information_system':
            return self._extract_information_systems(doc)
        
        # Маппинг spaCy меток на наши категории из конфига
        category_map = self.config.get_spacy_entity_mapping()
        
        # Фильтруем только нужную категорию
        relevant_labels = [label for label, cat in category_map.items() if cat == category]
        
        for ent in doc.ents:
            if ent.label_ in relevant_labels:
                detection = self.detection_factory.create_detection(
                    method=f"spacy_ner_{ent.label_.lower()}",
                    category=category,
                    original_value=ent.text,
                    position=(ent.start_char, ent.end_char),
                    additional_info={
                        'spacy_confidence': getattr(ent, 'confidence', None),
                        'spacy_label': ent.label_
                    }
                )
                entities.append(detection)
        
        return entities
    
    def _init_information_system_strategy(self):
        """Инициализирует и кеширует стратегию информационных систем при старте"""
        try:
            from information_system_strategy import InformationSystemStrategy
            strategy_settings = self.config.get_detection_strategy_settings('information_system')
            # Передаем уже загруженную spaCy модель для избежания повторной загрузки
            self._is_strategy = InformationSystemStrategy(strategy_settings, self.nlp)
        except ImportError as e:
            self._is_strategy = None
        except Exception as e:
            self._is_strategy = None
    
    def _extract_information_systems(self, doc: Doc) -> List[Dict[str, Any]]:
        """Специальная функция для извлечения информационных систем"""
        try:
            # Используем уже инициализированную стратегию
            if self._is_strategy is None:
                return []
            
            # Запускаем детекцию с кешированной стратегией
            detections = self._is_strategy.detect_information_systems_in_text(doc.text, doc)
            
            return detections
            
        except Exception as e:
            return []
    
    def _extract_regex_patterns_for_category(self, text: str, category: str) -> List[Dict[str, Any]]:
        """Извлекает regex паттерны для конкретной категории"""
        detections = []
        
        # Получаем паттерны только для нужной категории
        if category not in self.pattern_configs:
            return []
        
        category_pattern_configs = self.pattern_configs[category]
        
        for pattern_config in category_pattern_configs:
            pattern = pattern_config['pattern']
            pattern_type = pattern_config['pattern_type']
            # Пропускаем non-regex паттерны или пустые паттерны
            if pattern_type != 'regex' or pd.isna(pattern):
                continue
            flags = self.config.get_regex_flags_for_category(category)
            try:
                matches = re.finditer(pattern, text, flags)
                for match in matches:
                    match_text = match.group()
                    # Для person_name применяем морфологическую фильтрацию ТОЛЬКО для полных ФИО (3 слова)
                    if category == 'person_name':
                        # Фильтрация по справочникам ФИО (имена/фамилии)
                        if not self._fio_dictionary_filter(match_text):
                            continue
                        # Для 3-словных ФИО также морфологическая фильтрация
                        if len(match_text.split()) == 3 and '.' not in match_text:
                            if not self._is_valid_person_name_regex(match_text):
                                continue
                    if self._validate_context(text, match, category):
                        detection = self.detection_factory.create_detection(
                            method='regex',
                            category=category,
                            original_value=match_text,
                            position=(match.start(), match.end()),
                            additional_info={
                                'pattern_type': pattern_type,
                                'pattern_complexity': len(pattern) / 100.0,  # Простая метрика сложности
                                'has_context': True
                            }
                        )
                        detections.append(detection)
            except re.error as e:
                # if self.config.should_log_pattern_loading():
                #     pass
                pass
        return detections
    
    def _extract_morphological_names_for_category(self, doc: Doc, category: str) -> List[Dict[str, Any]]:
        """Извлекает имена через морфологический анализ для конкретной категории"""
        if category != 'person_name' or not self.morph:
            return []
        
        detections = []
        
        # Ищем потенциальные имена по морфологическим признакам
        for token in doc:
            # Пропускаем стоп-слова, пунктуацию и короткие токены
            if token.is_stop or token.is_punct or len(token.text) < 2:
                continue
            
            # Ищем слова с большой буквы (потенциальные имена)
            if token.text[0].isupper() and token.pos_ == 'PROPN':
                if self._is_likely_person_name_morph(token.text):
                    detection = self.detection_factory.create_detection(
                        method='morphological_enhanced',
                        category=category,
                        original_value=token.text,
                        position=(token.idx, token.idx + len(token.text)),
                        additional_info={
                            'morphological_tags': ['enhanced'],
                            'pos_tag': token.pos_
                        }
                    )
                    detections.append(detection)
                elif self._is_likely_person_name(token, doc):
                    detection = self.detection_factory.create_detection(
                        method='morphological',
                        category=category,
                        original_value=token.text,
                        position=(token.idx, token.idx + len(token.text)),
                        additional_info={
                            'morphological_tags': ['basic'],
                            'pos_tag': token.pos_
                        }
                    )
                    detections.append(detection)
        
        return detections
    
    def _extract_custom_matches_for_category(self, doc: Doc, category: str) -> List[Dict[str, Any]]:
        """Извлекает кастомные матчеры для конкретной категории"""
        detections = []
        
        if not self.matcher:
            return []
        
        # Используем Matcher для сложных паттернов
        matches = self.matcher(doc)
        
        for match_id, start, end in matches:
            span = doc[start:end]
            label = self.nlp.vocab.strings[match_id]
            
            # Определяем категорию по метке и фильтруем
            if label == "full_name" or label == "initials_lastname":
                detected_category = "person_name"
            elif label == "quoted_organization":
                detected_category = "organization"
            else:
                detected_category = "unknown"
            
            if detected_category == category:
                # Фильтрация по справочникам ФИО
                if category == 'person_name' and not self._fio_dictionary_filter(span.text):
                    continue
                detection = self.detection_factory.create_detection(
                    method='custom_matcher',
                    category=category,
                    original_value=span.text,
                    position=(span.start_char, span.end_char),
                    additional_info={
                        'matcher_label': label,
                        'is_structured': True,
                        'match_accuracy': 0.9  # Высокая точность для структурированных паттернов
                    }
                )
                detections.append(detection)
        
        return detections
    
    def _extract_context_matches_for_category(self, doc: Doc, category: str) -> List[Dict[str, Any]]:
        """Извлекает контекстные матчеры для конкретной категории"""
        detections = []
        
        # Сначала пробуем умный матчер, если доступен для этой категории
        if category in self.smart_phrase_matchers:
            try:
                smart_matcher = self.smart_phrase_matchers[category]
                smart_matches = smart_matcher.find_matches(doc)
                
                # Конвертируем умные совпадения в детекции
                smart_detections = smart_matcher.convert_to_detections(
                    matches=smart_matches,
                    category=category,
                    method='smart_phrase_matcher'
                )
                
                detections.extend(smart_detections)
                
                # Если умный матчер нашел совпадения, используем только их
                if smart_detections:
                    return detections
                
            except Exception as e:
                # Продолжаем с обычным матчером
                pass
        
        # Fallback к обычному phrase matcher
        if not self.phrase_matcher:
            return detections
        
        # Применяем phrase matcher
        matches = self.phrase_matcher(doc)
        
        for match_id, start, end in matches:
            span = doc[start:end]
            label = self.nlp.vocab.strings[match_id]
            
            # Определяем категорию на основе конфигурации phrase patterns
            detected_category = self._get_phrase_category(label)
            
            if detected_category == category:
                detection = self.detection_factory.create_detection(
                    method='phrase_matcher',
                    category=category,
                    original_value=span.text,
                    position=(span.start_char, span.end_char),
                    additional_info={
                        'phrase_label': label,
                        'match_accuracy': 0.8
                    }
                )
                detections.append(detection)
        
        return detections
    
    def _get_phrase_category(self, label: str) -> str:
        """Определяет категорию по метке phrase matcher"""
        # Маппинг меток на категории
        label_to_category = {
            'position_phrases': 'position',
            'organization_phrases': 'organization', 
            'department_phrases': 'organization',
            'salary_phrases': 'financial_amount',
            'health_info_phrases': 'medical',
            'trade_secret_phrases': 'confidential',
            'government_org_phrases': 'government_org'  # Новая категория
        }
        
        return label_to_category.get(label, 'unknown')
    
    def _extract_regex_patterns(self, text: str) -> List[Dict[str, Any]]:
        """Извлекает данные через regex паттерны"""
        detections = []
        
        for category, configs in self.pattern_configs.items():
            for config in configs:
                if config['pattern_type'] != 'regex' or not config['pattern']:
                    continue
                
                try:
                    pattern = config['pattern']
                    
                    # Получаем флаги regex из конфигурации
                    regex_flags = self.config.get_regex_flags_for_category(category)
                    matches = re.finditer(pattern, text, regex_flags)
                    
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
                            'uuid': 'placeholder'  # Временный placeholder, UUID будет генерироваться централизованно в FormatterApplier
                        }
                        detections.append(detection)
                
                except re.error as e:
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
                'uuid': 'placeholder'  # Временный placeholder, UUID будет генерироваться централизованно в FormatterApplier
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
                        'confidence': self.config.get_morphological_enhanced_confidence(),
                        'position': {
                            'start': token.idx,
                            'end': token.idx + len(token.text)
                        },
                        'method': 'morphological_enhanced',
                        'uuid': 'placeholder'  # Временный placeholder, UUID будет генерироваться централизованно в FormatterApplier
                    }
                    detections.append(detection)
                elif self._is_likely_person_name(token, doc):
                    # Fallback на старый метод
                    detection = {
                        'category': 'person_name',
                        'original_value': token.text,
                        'confidence': self.config.get_morphological_fallback_confidence(),
                        'position': {
                            'start': token.idx,
                            'end': token.idx + len(token.text)
                        },
                        'method': 'morphological',
                        'uuid': 'placeholder'  # Временный placeholder, UUID будет генерироваться централизованно в FormatterApplier
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
            
            # Получаем теги из конфигурации
            person_name_tags = self.config.get_morphological_person_name_tags()
            animated_noun_tags = self.config.get_morphological_animated_noun_tags()
            
            for parse in parsed:
                # Проверяем теги для имен
                for tag in person_name_tags:
                    if tag in parse.tag:
                        return True
                
                # Также проверяем одушевленные существительные
                if all(tag in parse.tag for tag in animated_noun_tags):
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
                confidence = self.config.get_custom_matcher_confidence('person_name')
            elif label == "quoted_organization":
                category = "organization"
                confidence = self.config.get_custom_matcher_confidence('organization')
            else:
                category = "unknown"
                confidence = self.config.get_custom_matcher_confidence('unknown')
            
            detection = {
                'category': category,
                'original_value': span.text,
                'confidence': confidence,
                'position': {
                    'start': span.start_char,
                    'end': span.end_char
                },
                'method': 'custom_matcher',
                'uuid': 'placeholder'  # Временный placeholder, UUID будет генерироваться централизованно в FormatterApplier
            }
            detections.append(detection)
        
        return detections
    
    def _validate_context(self, text: str, match: re.Match, category: str) -> bool:
        """Валидирует контекст найденного совпадения"""
        # Получаем контекст вокруг совпадения
        context_size = self.config.get_context_window_size()
        start = max(0, match.start() - context_size)
        end = min(len(text), match.end() + context_size)
        context = text[start:end].lower()
        
        # Контекстные слова для разных категорий из конфига
        context_keywords = self.config.get_context_keywords_for_category(category)
        
        if context_keywords:
            return any(keyword in context for keyword in context_keywords)
        
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
        context_words = self.config.get_context_keywords_for_category('person_name')
        
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
    
    def _map_positions_to_original(self, detections: List[Dict[str, Any]], 
                                  original_text: str, normalized_text: str) -> List[Dict[str, Any]]:
        """
        Маппит позиции из нормализованного текста обратно к оригинальному
        
        Args:
            detections: Список детекций с позициями в нормализованном тексте
            original_text: Оригинальный текст
            normalized_text: Нормализованный текст
            
        Returns:
            Список детекций с позициями в оригинальном тексте
        """
        if original_text == normalized_text:
            return detections
        
        mapped_detections = []
        
        for detection in detections:
            try:
                # Получаем найденный текст из нормализованной версии
                start_norm = detection['position']['start']
                end_norm = detection['position']['end']
                found_text = normalized_text[start_norm:end_norm]
                
                # Ищем соответствующую позицию в оригинальном тексте
                original_start = self._find_text_position_in_original(
                    found_text, original_text, start_norm, normalized_text
                )
                
                if original_start is not None:
                    # Создаем новую детекцию с правильными позициями
                    mapped_detection = detection.copy()
                    mapped_detection['position'] = {
                        'start': original_start,
                        'end': original_start + len(found_text)
                    }
                    # Обновляем original_value для соответствия оригинальному тексту
                    mapped_detection['original_value'] = original_text[
                        original_start:original_start + len(found_text)
                    ]
                    mapped_detections.append(mapped_detection)
                else:
                    # Если не можем найти соответствие, пропускаем
                    pass
                    
            except Exception as e:
                # В случае ошибки добавляем оригинальную детекцию
                mapped_detections.append(detection)
        
        return mapped_detections
    
    def _find_text_position_in_original(self, found_text: str, original_text: str, 
                                       approximate_pos: int, normalized_text: str) -> Optional[int]:
        """
        Находит позицию текста в оригинальном тексте
        
        Args:
            found_text: Найденный текст
            original_text: Оригинальный текст
            approximate_pos: Приблизительная позиция в нормализованном тексте
            normalized_text: Нормализованный текст
            
        Returns:
            Позиция в оригинальном тексте или None, если не найдено
        """
        # Простая стратегия: ищем точное совпадение
        position = original_text.find(found_text)
        if position != -1:
            return position
        
        # Ищем без учета регистра
        position = original_text.lower().find(found_text.lower())
        if position != -1:
            return position
        
        # Ищем с учетом возможных переносов строк
        # Заменяем переносы строк в найденном тексте на пробелы и ищем снова
        text_with_spaces = found_text.replace('\n', ' ').replace('\r', ' ')
        text_variants = [text_with_spaces, text_with_spaces.strip()]
        
        for variant in text_variants:
            position = original_text.find(variant)
            if position != -1:
                return position
            
            position = original_text.lower().find(variant.lower())
            if position != -1:
                return position
        
        return None
