#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Диагностика проблемы PhraseMatcher с неполным обнаружением названий
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'app'))

import spacy
from spacy.matcher import PhraseMatcher

def diagnose_phrase_matcher_issue():
    """Диагностируем проблему с неполным обнаружением"""
    
    print("🔍 ДИАГНОСТИКА ПРОБЛЕМЫ PHRASE MATCHER")
    print("=" * 60)
    
    # Тестовый текст из реального документа
    test_text = "МИНИСТЕРСТВО ИНФОРМАЦИОННОГО РАЗВИТИЯ И СВЯЗИ\nПЕРМСКОГО КРАЯ"
    
    print(f"📝 Тестовый текст:")
    print(f"'{test_text}'")
    print(f"Длина: {len(test_text)} символов")
    print()
    
    # Загружаем spaCy модель
    nlp = spacy.load("ru_core_news_sm")
    
    # Анализируем токенизацию
    print("1️⃣ АНАЛИЗ ТОКЕНИЗАЦИИ:")
    print("-" * 30)
    doc = nlp(test_text)
    
    for i, token in enumerate(doc):
        print(f"  {i:2d}: '{token.text}' (pos: {token.pos_}, lemma: '{token.lemma_}')")
    print()
    
    # Проверяем наш словарь организаций
    print("2️⃣ АНАЛИЗ СЛОВАРЯ ОРГАНИЗАЦИЙ:")
    print("-" * 40)
    
    try:
        from government_organizations import GOVERNMENT_ORGANIZATIONS
        
        # Ищем совпадения в словаре
        target_phrases = []
        for org in GOVERNMENT_ORGANIZATIONS:
            if "министерство информационного развития" in org.lower():
                target_phrases.append(org)
                print(f"  📋 Найдено в словаре: '{org}'")
        
        print(f"\n  📊 Всего релевантных фраз: {len(target_phrases)}")
        print()
        
    except ImportError:
        print("  ❌ Не удалось загрузить словарь организаций")
        # Fallback фразы для тестирования
        target_phrases = [
            "Министерство информационного развития",
            "Министерство информационного развития и связи Пермского края"
        ]
    
    # Тестируем PhraseMatcher
    print("3️⃣ ТЕСТИРОВАНИЕ PHRASE MATCHER:")
    print("-" * 40)
    
    phrase_matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
    
    # Добавляем фразы по одной и проверяем
    for phrase in target_phrases:
        print(f"\n  🧪 Тестируем фразу: '{phrase}'")
        
        # Создаем документ фразы
        phrase_doc = nlp(phrase)
        print(f"     Токенов в фразе: {len(phrase_doc)}")
        for j, token in enumerate(phrase_doc):
            print(f"       {j}: '{token.text}'")
        
        # Добавляем в matcher
        matcher_copy = PhraseMatcher(nlp.vocab, attr="LOWER")
        matcher_copy.add("TEST_PHRASE", [phrase_doc])
        
        # Ищем совпадения
        matches = matcher_copy(doc)
        print(f"     Найдено совпадений: {len(matches)}")
        
        for match_id, start, end in matches:
            span = doc[start:end]
            print(f"       ✅ Совпадение: '{span.text}' (токены {start}-{end})")
    
    print()
    
    # Тестируем полный PhraseMatcher как в реальном коде
    print("4️⃣ ТЕСТИРОВАНИЕ РЕАЛЬНОГО PHRASE MATCHER:")
    print("-" * 50)
    
    real_matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
    
    # Добавляем все фразы сразу как в реальном коде
    phrase_docs = [nlp(phrase) for phrase in target_phrases]
    real_matcher.add("government_org_phrases", phrase_docs)
    
    print(f"  📊 Добавлено фраз в matcher: {len(phrase_docs)}")
    
    matches = real_matcher(doc)
    print(f"  🎯 Найдено совпадений: {len(matches)}")
    
    for match_id, start, end in matches:
        span = doc[start:end]
        label = nlp.vocab.strings[match_id]
        print(f"    - '{span.text}' (токены {start}-{end}, метка: '{label}')")
    
    print()
    
    # Анализ причин проблемы
    print("5️⃣ АНАЛИЗ ПРИЧИН ПРОБЛЕМЫ:")
    print("-" * 35)
    
    print("  🔍 Возможные причины:")
    print("    1. Переносы строк в тексте разбивают фразу")
    print("    2. Различия в регистре (ВЕРХНИЙ vs нижний)")
    print("    3. Неполное совпадение токенов")
    print("    4. Порядок фраз в словаре влияет на приоритет")
    
    # Проверим текст без переносов
    print("\n  🧪 ТЕСТ БЕЗ ПЕРЕНОСОВ СТРОК:")
    clean_text = test_text.replace('\n', ' ').replace('\r', '')
    print(f"    Исходный: '{test_text}'")
    print(f"    Очищенный: '{clean_text}'")
    
    clean_doc = nlp(clean_text)
    clean_matches = real_matcher(clean_doc)
    print(f"    Совпадений в очищенном тексте: {len(clean_matches)}")
    
    for match_id, start, end in clean_matches:
        span = clean_doc[start:end]
        print(f"      ✅ '{span.text}' (токены {start}-{end})")
    
    print()
    
    # Рекомендации по решению
    print("6️⃣ РЕКОМЕНДАЦИИ ПО РЕШЕНИЮ:")
    print("-" * 40)
    
    print("  💡 Возможные решения:")
    print("    1. Нормализация текста перед PhraseMatcher")
    print("    2. Добавление вариантов фраз с переносами")
    print("    3. Использование более гибкого Matcher с regex")
    print("    4. Постобработка для объединения частичных совпадений")
    print("    5. Изменение порядка фраз в словаре (длинные первыми)")

if __name__ == "__main__":
    diagnose_phrase_matcher_issue()