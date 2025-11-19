#!/usr/bin/env python3
"""
Пример использования Phrase Matcher для детекции государственных организаций
"""

import spacy
from spacy.matcher import PhraseMatcher
from typing import List, Dict, Any

class GovernmentOrgPhraseDetector:
    """Детектор государственных организаций через Phrase Matcher"""
    
    def __init__(self):
        self.nlp = spacy.load("ru_core_news_lg")
        self.phrase_matcher = PhraseMatcher(self.nlp.vocab, attr="LOWER")
        
        # Инициализируем словари названий
        self._load_government_phrases()
    
    def _load_government_phrases(self):
        """Загружает словари государственных организаций"""
        
        # 1. Полные официальные названия
        official_names = [
            "Министерство внутренних дел Российской Федерации",
            "Федеральная налоговая служба",
            "Федеральная служба безопасности",
            "Министерство здравоохранения Российской Федерации",
            "Министерство образования и науки Российской Федерации",
            "Федеральное агентство по туризму",
            "Администрация Президента Российской Федерации",
            "Правительство Российской Федерации",
            "Министерство информационного развития и связи Пермского края",
            "Департамент образования и науки Кировской области",
            "Управление внутренних дел по Свердловской области"
        ]
        
        # 2. Сокращенные названия
        abbreviated_names = [
            "МВД России", "МВД РФ", "ФНС России", "ФСБ России",
            "Минздрав России", "Минобрнауки России", "Ростуризм",
            "Роскомнадзор", "Росреестр", "Росстат",
            "Правительство РФ", "Администрация Президента"
        ]
        
        # 3. Региональные и местные органы (паттерны)
        regional_patterns = [
            "Администрация города",
            "Городская дума",
            "Законодательное собрание",
            "Правительство края",
            "Правительство области",
            "Министерство края",
            "Министерство области",
            "Департамент города"
        ]
        
        # Создаем phrase patterns
        self._add_phrases("official_full", official_names, 0.95)
        self._add_phrases("abbreviated", abbreviated_names, 0.90)
        self._add_phrases("regional", regional_patterns, 0.85)
    
    def _add_phrases(self, category: str, phrases: List[str], confidence: float):
        """Добавляет фразы в matcher с указанной категорией"""
        # Преобразуем строки в spaCy документы
        phrase_docs = [self.nlp(phrase) for phrase in phrases]
        
        # Добавляем в matcher
        self.phrase_matcher.add(category, phrase_docs)
        
        # Сохраняем метаданные для каждой фразы
        if not hasattr(self, '_phrase_metadata'):
            self._phrase_metadata = {}
        
        self._phrase_metadata[category] = {
            'confidence': confidence,
            'phrases': phrases
        }
    
    def detect_government_orgs(self, text: str) -> List[Dict[str, Any]]:
        """Детектирует государственные организации через phrase matching"""
        doc = self.nlp(text)
        matches = self.phrase_matcher(doc)
        
        detections = []
        
        for match_id, start, end in matches:
            # Получаем метаданные совпадения
            category = self.nlp.vocab.strings[match_id]
            metadata = self._phrase_metadata[category]
            
            # Извлекаем совпавшую фразу
            matched_span = doc[start:end]
            matched_text = matched_span.text
            
            detection = {
                'category': 'government_org',
                'original_value': matched_text,
                'confidence': metadata['confidence'],
                'position': {
                    'start': matched_span.start_char,
                    'end': matched_span.end_char
                },
                'method': 'phrase_matcher',
                'phrase_category': category,
                'detection_type': self._classify_detection_type(category)
            }
            
            detections.append(detection)
        
        # Удаляем дубликаты и возвращаем результат
        return self._remove_overlapping_detections(detections)
    
    def _classify_detection_type(self, category: str) -> str:
        """Классифицирует тип детекции для лучшего понимания"""
        type_mapping = {
            'official_full': 'Полное официальное название',
            'abbreviated': 'Сокращенное название',
            'regional': 'Региональный/муниципальный орган'
        }
        return type_mapping.get(category, 'Неизвестный тип')
    
    def _remove_overlapping_detections(self, detections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Удаляет пересекающиеся детекции, предпочитая более точные"""
        if not detections:
            return detections
        
        # Сортируем по confidence (убывание) и по длине (убывание)
        detections.sort(key=lambda x: (-x['confidence'], -(x['position']['end'] - x['position']['start'])))
        
        filtered = []
        
        for detection in detections:
            is_overlapping = False
            
            for existing in filtered:
                if self._is_overlapping(detection['position'], existing['position']):
                    is_overlapping = True
                    break
            
            if not is_overlapping:
                filtered.append(detection)
        
        return filtered
    
    def _is_overlapping(self, pos1: Dict[str, int], pos2: Dict[str, int]) -> bool:
        """Проверяет пересечение двух позиций"""
        return not (pos1['end'] <= pos2['start'] or pos2['end'] <= pos1['start'])

# Демонстрация преимуществ Phrase Matcher
def demonstrate_phrase_matcher():
    """Показывает, как Phrase Matcher улучшает детекцию"""
    
    detector = GovernmentOrgPhraseDetector()
    
    test_cases = [
        # Тест 1: Полные названия
        "Министерство внутренних дел Российской Федерации провело операцию.",
        
        # Тест 2: Сокращения
        "МВД России и ФНС России подписали соглашение.",
        
        # Тест 3: Региональные органы
        "Администрация города Перми объявила конкурс.",
        
        # Тест 4: Склонения и вариации
        "Сотрудники Роскомнадзора провели проверку.",
        
        # Тест 5: Смешанный текст
        "Правительство РФ и Министерство здравоохранения обсуждают реформы."
    ]
    
    print("🎯 ДЕМОНСТРАЦИЯ PHRASE MATCHER ДЛЯ ГОСУДАРСТВЕННЫХ ОРГАНИЗАЦИЙ")
    print("=" * 80)
    
    total_detected = 0
    
    for i, text in enumerate(test_cases, 1):
        print(f"\n📝 Тест {i}: {text}")
        detections = detector.detect_government_orgs(text)
        
        if detections:
            print(f"✅ Найдено {len(detections)} совпадений:")
            for det in detections:
                print(f"   • '{det['original_value']}' (confidence: {det['confidence']})")
                print(f"     Тип: {det['detection_type']}")
                print(f"     Категория: {det['phrase_category']}")
            total_detected += len(detections)
        else:
            print("❌ Совпадения не найдены")
    
    print(f"\n📊 ИТОГО: Обнаружено {total_detected} государственных организаций")
    
    # Сравнение с regex подходом
    print(f"\n🔄 СРАВНЕНИЕ С REGEX:")
    print(f"✅ Phrase Matcher преимущества:")
    print(f"   • Автоматическая обработка морфологии и склонений")
    print(f"   • Быстрее чем сложные regex (O(n) vs O(n*m))")
    print(f"   • Легко добавлять новые фразы без regex знаний")
    print(f"   • Понимает контекст и границы слов")
    print(f"   • Поддерживает различные атрибуты токенов (LOWER, LEMMA)")

if __name__ == "__main__":
    demonstrate_phrase_matcher()