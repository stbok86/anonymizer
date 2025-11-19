#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Диагностика проблем с гибридной стратегией
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'app'))

from nlp_adapter import NLPAdapter

def debug_government_org_detection():
    """Отладка детекции государственных организаций"""
    
    print("🔍 ДИАГНОСТИКА ДЕТЕКЦИИ ГОСУДАРСТВЕННЫХ ОРГАНИЗАЦИЙ")
    print("=" * 70)
    
    test_text = "Министерство информационного развития и связи Пермского края"
    print(f"Тестовый текст: '{test_text}'")
    print()
    
    try:
        adapter = NLPAdapter()
        
        # 1. Проверяем конфигурацию
        print("1️⃣ ПРОВЕРКА КОНФИГУРАЦИИ:")
        print("-" * 30)
        
        # Проверяем доступные методы для government_org
        enabled_methods = adapter.config.get_enabled_methods_for_category('government_org')
        print(f"   Включённые методы: {enabled_methods}")
        
        # Проверяем стратегию
        strategy = adapter.config.get_detection_strategy_name('government_org')
        print(f"   Стратегия: {strategy}")
        
        # Проверяем минимальные confidence для методов
        for method in enabled_methods:
            min_conf = adapter.config.get_min_confidence_for_method('government_org', method)
            print(f"   {method}: min_confidence = {min_conf}")
        
        print()
        
        # 2. Тестируем каждый метод отдельно
        print("2️⃣ ТЕСТИРОВАНИЕ ОТДЕЛЬНЫХ МЕТОДОВ:")
        print("-" * 40)
        
        doc = adapter.nlp(test_text)
        
        # Тест phrase_matcher
        print(f"📚 Phrase Matcher:")
        phrase_results = adapter._extract_context_matches_for_category(doc, 'government_org')
        print(f"   Результаты: {len(phrase_results)}")
        for result in phrase_results:
            print(f"   - '{result['original_value']}' (conf: {result['confidence']})")
        print()
        
        # Тест spacy_ner 
        print(f"🤖 spaCy NER:")
        ner_results = adapter._extract_spacy_entities_for_category(doc, 'government_org')
        print(f"   Результаты: {len(ner_results)}")
        for result in ner_results:
            print(f"   - '{result['original_value']}' (conf: {result['confidence']})")
        print()
        
        # Тест regex
        print(f"🔤 Regex:")
        regex_results = adapter._extract_regex_patterns_for_category(test_text, 'government_org')
        print(f"   Результаты: {len(regex_results)}")
        for result in regex_results:
            print(f"   - '{result['original_value']}' (conf: {result['confidence']})")
        print()
        
        # 3. Проверяем phrase matcher детально
        print("3️⃣ ДЕТАЛЬНАЯ ПРОВЕРКА PHRASE MATCHER:")
        print("-" * 45)
        
        if adapter.phrase_matcher:
            matches = adapter.phrase_matcher(doc)
            print(f"   Найдено совпадений в phrase_matcher: {len(matches)}")
            
            for match_id, start, end in matches:
                span = doc[start:end]
                label = adapter.nlp.vocab.strings[match_id]
                category = adapter._get_phrase_category(label)
                print(f"   - '{span.text}' -> label: '{label}' -> category: '{category}'")
        else:
            print("   ❌ phrase_matcher не инициализирован")
        
        print()
        
        # 4. Проверяем spaCy NER детально  
        print("4️⃣ ДЕТАЛЬНАЯ ПРОВЕРКА SPACY NER:")
        print("-" * 40)
        
        print(f"   Найдено сущностей в spaCy: {len(doc.ents)}")
        
        category_map = adapter.config.get_spacy_entity_mapping()
        print(f"   Маппинг категорий: {category_map}")
        
        government_labels = [label for label, cat in category_map.items() if cat == 'government_org']
        print(f"   Метки для government_org: {government_labels}")
        
        for ent in doc.ents:
            print(f"   - '{ent.text}' -> label: '{ent.label_}' -> mapped: {category_map.get(ent.label_, 'unknown')}")
        
        print()
        
        # 5. Проверяем правильность загрузки словаря
        print("5️⃣ ПРОВЕРКА СЛОВАРЯ ГОСУДАРСТВЕННЫХ ОРГАНИЗАЦИЙ:")
        print("-" * 55)
        
        gov_orgs = adapter._load_government_organizations()
        print(f"   Загружено организаций: {len(gov_orgs)}")
        print("   Первые 10:")
        for i, org in enumerate(gov_orgs[:10], 1):
            print(f"     {i}. {org}")
        
        # Проверяем есть ли наш тест в словаре
        target = "Министерство информационного развития и связи Пермского края"
        if target in gov_orgs:
            print(f"   ✅ Тестовая организация найдена в словаре")
        else:
            # Ищем похожие
            similar = [org for org in gov_orgs if "министерство информационного развития" in org.lower()]
            print(f"   ❌ Тестовая организация НЕ найдена в словаре")
            print(f"   Похожие: {similar}")
        
    except Exception as e:
        print(f"❌ Ошибка: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_government_org_detection()