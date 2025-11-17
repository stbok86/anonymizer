#!/usr/bin/env python3
"""
Конфигурация для NLP Service
"""

import json
import os
import re
from typing import Dict, Any, List, Optional
from pathlib import Path


class NLPConfig:
    """Класс для загрузки и управления конфигурацией NLP Service"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Инициализация конфигурации
        
        Args:
            config_path: Путь к файлу конфигурации. Если None, используется дефолтный
        """
        if config_path is None:
            config_path = os.path.join(
                os.path.dirname(__file__), "..", "config", "nlp_config.json"
            )
        
        self.config_path = config_path
        self.config = self._load_config()
        self._validate_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Загружает конфигурацию из JSON файла"""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Файл конфигурации не найден: {self.config_path}")
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            return config.get('nlp_service_config', {})
        except json.JSONDecodeError as e:
            raise ValueError(f"Ошибка парсинга JSON конфигурации: {e}")
        except Exception as e:
            raise RuntimeError(f"Ошибка загрузки конфигурации: {e}")
    
    def _validate_config(self):
        """Валидирует конфигурацию"""
        required_sections = [
            'models', 'confidence_thresholds', 'regex_settings', 
            'processing_settings', 'file_paths'
        ]
        
        for section in required_sections:
            if section not in self.config:
                raise ValueError(f"Отсутствует секция '{section}' в конфигурации")
    
    # === Методы доступа к настройкам моделей ===
    
    def get_spacy_models(self) -> List[str]:
        """Возвращает список предпочитаемых spaCy моделей в порядке приоритета"""
        return self.config['models']['spacy']['preferred_models']
    
    def get_spacy_fallback_error(self) -> str:
        """Возвращает сообщение об ошибке для случая отсутствия spaCy модели"""
        return self.config['models']['spacy']['fallback_error_message']
    
    def is_morphology_enabled(self) -> bool:
        """Проверяет, включен ли морфологический анализ"""
        return self.config['models']['morphology'].get('enabled', True)
    
    # === Методы доступа к confidence thresholds ===
    
    def get_global_confidence_threshold(self) -> float:
        """Возвращает глобальный порог уверенности для фильтрации"""
        return self.config['confidence_thresholds']['global_filter']
    
    def get_spacy_ner_confidence(self) -> float:
        """Возвращает уверенность для spaCy NER"""
        return self.config['confidence_thresholds']['spacy_ner']
    
    def get_morphological_enhanced_confidence(self) -> float:
        """Возвращает уверенность для улучшенного морфологического анализа"""
        return self.config['confidence_thresholds']['morphological_enhanced']
    
    def get_morphological_fallback_confidence(self) -> float:
        """Возвращает уверенность для fallback морфологического анализа"""
        return self.config['confidence_thresholds']['morphological_fallback']
    
    def get_custom_matcher_confidences(self) -> Dict[str, float]:
        """Возвращает уверенности для кастомных матчеров"""
        thresholds = self.config['confidence_thresholds']
        return {
            'full_names': thresholds['custom_matcher_full_names'],
            'initials': thresholds['custom_matcher_initials'],
            'simple': thresholds['custom_matcher_simple']
        }
    
    def get_custom_matcher_confidence(self, category: str) -> float:
        """Возвращает уверенность для конкретной категории кастомного матчера"""
        category_mapping = {
            'person_name': 'custom_matcher_full_names',
            'organization': 'custom_matcher_simple', 
            'unknown': 'custom_matcher_simple'
        }
        
        threshold_key = category_mapping.get(category, 'custom_matcher_simple')
        return self.config['confidence_thresholds'][threshold_key]
    
    def get_default_pattern_confidence(self) -> float:
        """Возвращает дефолтную уверенность для паттернов"""
        return self.config['confidence_thresholds']['default_pattern_confidence']
    
    # === Методы доступа к regex настройкам ===
    
    def get_regex_flags_for_category(self, category: str) -> int:
        """
        Возвращает флаги regex для указанной категории
        
        Args:
            category: Название категории (например, 'person_name')
            
        Returns:
            Битовая маска флагов regex
        """
        settings = self.config['regex_settings']
        case_sensitive_categories = settings.get('case_sensitive_categories', [])
        
        if category in case_sensitive_categories:
            flags_list = settings['person_name_flags']
        else:
            flags_list = settings['other_categories_flags']
        
        # Преобразуем строковые флаги в битовую маску
        flag_mapping = {
            'IGNORECASE': re.IGNORECASE,
            'UNICODE': re.UNICODE,
            'MULTILINE': re.MULTILINE,
            'DOTALL': re.DOTALL
        }
        
        flags = 0
        for flag_name in flags_list:
            if flag_name in flag_mapping:
                flags |= flag_mapping[flag_name]
        
        return flags
    
    # === Методы доступа к настройкам обработки ===
    
    def get_context_window_size(self) -> int:
        """Возвращает размер окна контекста в символах"""
        return self.config['processing_settings']['context_window_size']
    
    def get_phrase_matcher_attr(self) -> str:
        """Возвращает атрибут для PhraseMatcher"""
        return self.config['processing_settings']['phrase_matcher_attr']
    
    def is_deduplication_enabled(self) -> bool:
        """Проверяет, включена ли дедупликация"""
        return self.config['processing_settings'].get('enable_deduplication', True)
    
    # === Методы доступа к путям файлов ===
    
    def get_patterns_file_path(self) -> str:
        """Возвращает полный путь к файлу паттернов"""
        file_paths = self.config['file_paths']
        relative_path = file_paths['patterns_file']
        base_path_type = file_paths.get('patterns_file_relative_to', 'nlp_service_app_dir')
        
        if base_path_type == 'nlp_service_app_dir':
            # Относительно папки app в nlp_service
            base_path = os.path.dirname(__file__)
            return os.path.join(base_path, "..", relative_path)
        else:
            # Абсолютный путь
            return relative_path
    
    # === Методы доступа к контекстным ключевым словам ===
    
    def get_context_keywords(self) -> Dict[str, List[str]]:
        """Возвращает словарь контекстных ключевых слов"""
        return self.config.get('context_keywords', {})
    
    def get_context_keywords_for_category(self, category: str) -> List[str]:
        """Возвращает контекстные ключевые слова для указанной категории"""
        return self.config.get('context_keywords', {}).get(category, [])
    
    # === Методы доступа к маппингу сущностей ===
    
    def get_spacy_entity_mapping(self) -> Dict[str, str]:
        """Возвращает маппинг spaCy меток на внутренние категории"""
        return self.config.get('entity_mapping', {}).get('spacy_to_internal', {})
    
    # === Методы доступа к настройкам морфологического анализа ===
    
    def get_morphological_person_name_tags(self) -> List[str]:
        """Возвращает теги для идентификации имен через морфологический анализ"""
        return self.config.get('morphological_analysis', {}).get('person_name_tags', [])
    
    def get_morphological_animated_noun_tags(self) -> List[str]:
        """Возвращает теги для идентификации одушевленных существительных"""
        return self.config.get('morphological_analysis', {}).get('animated_noun_tags', [])
    
    def get_morphological_required_pos_tag(self) -> str:
        """Возвращает требуемый POS тег для морфологического анализа"""
        return self.config.get('morphological_analysis', {}).get('required_pos_tag', 'PROPN')
    
    def get_morphological_min_token_length(self) -> int:
        """Возвращает минимальную длину токена для морфологического анализа"""
        return self.config.get('morphological_analysis', {}).get('min_token_length', 2)
    
    # === Методы доступа к настройкам кастомных фраз ===
    
    def get_custom_phrase_category_config(self, category: str) -> Dict[str, Any]:
        """Возвращает конфигурацию для указанной категории кастомных фраз"""
        return self.config.get('custom_phrase_categories', {}).get(category, {})
    
    def is_custom_phrase_category_enabled(self, category: str) -> bool:
        """Проверяет, включена ли указанная категория кастомных фраз"""
        config = self.get_custom_phrase_category_config(category)
        return config.get('enabled', False)
    
    def get_custom_phrase_category_confidence(self, category: str) -> float:
        """Возвращает уверенность для указанной категории кастомных фраз"""
        config = self.get_custom_phrase_category_config(category)
        return config.get('confidence', 0.7)
    
    # === Методы доступа к настройкам валидации ===
    
    def is_context_validation_required(self) -> bool:
        """Проверяет, требуется ли валидация контекста"""
        return self.config.get('validation_settings', {}).get('require_context_validation', True)
    
    def get_validation_min_word_length(self) -> int:
        """Возвращает минимальную длину слова для валидации"""
        return self.config.get('validation_settings', {}).get('min_word_length', 2)
    
    def should_skip_stop_words(self) -> bool:
        """Проверяет, нужно ли пропускать стоп-слова"""
        return self.config.get('validation_settings', {}).get('skip_stop_words', True)
    
    def should_skip_punctuation(self) -> bool:
        """Проверяет, нужно ли пропускать пунктуацию"""
        return self.config.get('validation_settings', {}).get('skip_punctuation', True)
    
    # === Методы доступа к настройкам логирования ===
    
    def get_logging_level(self) -> str:
        """Возвращает уровень логирования"""
        return self.config.get('logging', {}).get('level', 'INFO')
    
    def should_log_model_loading(self) -> bool:
        """Проверяет, нужно ли логировать загрузку моделей"""
        return self.config.get('logging', {}).get('log_model_loading', True)
    
    def should_log_pattern_loading(self) -> bool:
        """Проверяет, нужно ли логировать загрузку паттернов"""
        return self.config.get('logging', {}).get('log_pattern_loading', True)
    
    def should_log_detection_stats(self) -> bool:
        """Проверяет, нужно ли логировать статистику обнаружений"""
        return self.config.get('logging', {}).get('log_detection_stats', True)
    
    # === Настройки методов обнаружения ===
    
    def get_enabled_methods_for_category(self, category: str) -> List[str]:
        """Возвращает список включенных методов для категории"""
        methods_config = self.config.get('detection_methods', {}).get(category, {})
        return methods_config.get('enabled_methods', [])
    
    def get_method_priority_order(self, category: str) -> List[int]:
        """Возвращает порядок приоритетов методов для категории"""
        methods_config = self.config.get('detection_methods', {}).get(category, {})
        return methods_config.get('priority_order', [])
    
    def get_detection_strategy_name(self, category: str) -> str:
        """Возвращает название стратегии комбинирования для категории"""
        methods_config = self.config.get('detection_methods', {}).get(category, {})
        return methods_config.get('strategy', 'best_confidence')
    
    def is_fallback_enabled(self, category: str) -> bool:
        """Проверяет, включен ли fallback для категории"""
        methods_config = self.config.get('detection_methods', {}).get(category, {})
        return methods_config.get('fallback_enabled', True)
    
    def get_max_results_for_category(self, category: str) -> int:
        """Возвращает максимальное количество результатов для категории"""
        methods_config = self.config.get('detection_methods', {}).get(category, {})
        return methods_config.get('max_results', 10)
    
    def get_method_settings(self, category: str, method: str) -> Dict[str, Any]:
        """Возвращает настройки конкретного метода для категории"""
        methods_config = self.config.get('detection_methods', {}).get(category, {})
        method_settings = methods_config.get('method_settings', {})
        return method_settings.get(method, {})
    
    def get_min_confidence_for_method(self, category: str, method: str) -> float:
        """Возвращает минимальную уверенность для метода"""
        method_settings = self.get_method_settings(category, method)
        return method_settings.get('min_confidence', 0.5)
    
    def get_early_exit_threshold(self, category: str, method: str) -> float:
        """Возвращает порог для раннего выхода"""
        method_settings = self.get_method_settings(category, method)
        return method_settings.get('early_exit_threshold', 0.95)
    
    def get_detection_strategy_settings(self, strategy_name: str) -> Dict[str, Any]:
        """Возвращает настройки стратегии детекции"""
        strategies = self.config.get('detection_strategies', {})
        return strategies.get(strategy_name, {})
    
    def get_available_categories(self) -> List[str]:
        """Возвращает список всех доступных категорий"""
        return list(self.config.get('detection_methods', {}).keys())
    
    def get_method_weights(self, strategy_name: str) -> Dict[str, float]:
        """Возвращает веса методов для взвешенной стратегии"""
        strategy_settings = self.get_detection_strategy_settings(strategy_name)
        return strategy_settings.get('method_weights', {})
    
    def should_combine_overlapping(self, strategy_name: str) -> bool:
        """Проверяет, нужно ли комбинировать пересекающиеся результаты"""
        strategy_settings = self.get_detection_strategy_settings(strategy_name)
        return strategy_settings.get('combine_overlapping', False)
    
    def get_dedup_threshold(self, strategy_name: str) -> float:
        """Возвращает порог для удаления дубликатов"""
        strategy_settings = self.get_detection_strategy_settings(strategy_name)
        return strategy_settings.get('dedup_threshold', 0.8)
    
    def should_stop_on_first(self, strategy_name: str) -> bool:
        """Проверяет, нужно ли останавливаться на первом результате"""
        strategy_settings = self.get_detection_strategy_settings(strategy_name)
        return strategy_settings.get('stop_on_first', False)
    
    # === Утилитарные методы ===
    
    def reload_config(self):
        """Перезагружает конфигурацию из файла"""
        self.config = self._load_config()
        self._validate_config()
    
    def get_config_summary(self) -> Dict[str, Any]:
        """Возвращает краткую сводку конфигурации для отладки"""
        return {
            'spacy_models': self.get_spacy_models(),
            'global_confidence_threshold': self.get_global_confidence_threshold(),
            'patterns_file': self.get_patterns_file_path(),
            'morphology_enabled': self.is_morphology_enabled(),
            'context_window_size': self.get_context_window_size(),
            'deduplication_enabled': self.is_deduplication_enabled()
        }