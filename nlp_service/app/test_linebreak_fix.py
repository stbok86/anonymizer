#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест исправления проблемы с переносами строк в PhraseMatcher
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from nlp_adapter import NLPAdapter
from text_normalizer import TextNormalizer

def test_line_break_fix():
    """Тестирует исправление проблемы с переносами строк"""
    
    print("=" * 80)
    print("🧪 ТЕСТ ИСПРАВЛЕНИЯ ПРОБЛЕМЫ С ПЕРЕНОСАМИ СТРОК")
    print("=" * 80)
    
    # Инициализируем адаптер
    adapter = NLPAdapter()
    
    # Тестовый текст с переносами строк
    test_text_with_linebreaks = """
    Согласно письму от МИНИСТЕРСТВО ИНФОРМАЦИОННОГО РАЗВИТИЯ И СВЯЗИ
    ПЕРМСКОГО КРАЯ от 15.01.2024 № 123 требуется...
    
    Также ДЕПАРТАМЕНТ ОБРАЗОВАНИЯ И НАУКИ
    КИРОВСКОЙ ОБЛАСТИ сообщил...
    """
    
    # Тестовый текст без переносов
    test_text_clean = """
    Согласно письму от МИНИСТЕРСТВО ИНФОРМАЦИОННОГО РАЗВИТИЯ И СВЯЗИ ПЕРМСКОГО КРАЯ от 15.01.2024 № 123 требуется...
    
    Также ДЕПАРТАМЕНТ ОБРАЗОВАНИЯ И НАУКИ КИРОВСКОЙ ОБЛАСТИ сообщил...
    """
    
    print("📝 ИСХОДНЫЙ ТЕКСТ С ПЕРЕНОСАМИ:")
    print(repr(test_text_with_linebreaks))
    print()
    
    # Тестируем нормализатор
    normalizer = TextNormalizer()
    normalized = normalizer.normalize_text(test_text_with_linebreaks)
    
    print("🔧 НОРМАЛИЗОВАННЫЙ ТЕКСТ:")
    print(repr(normalized))
    print()
    
    # Обрабатываем текст с переносами
    print("🔍 ОБРАБОТКА ТЕКСТА С ПЕРЕНОСАМИ СТРОК:")
    print("-" * 50)
    results_with_breaks = adapter.find_sensitive_data(test_text_with_linebreaks)
    
    print(f"\n✅ Найдено {len(results_with_breaks)} элементов:")
    for i, result in enumerate(results_with_breaks, 1):
        if result['category'] == 'government_org':
            start = result['position']['start']
            end = result['position']['end']
            found_text = test_text_with_linebreaks[start:end]
            print(f"   {i}. '{result['original_value']}' (позиция {start}-{end})")
            print(f"      Метод: {result['method']}")
            print(f"      Confidence: {result['confidence']:.3f}")
            print(f"      Реальный текст: '{found_text}'")
            print()
    
    # Обрабатываем чистый текст для сравнения
    print("\n🔍 ОБРАБОТКА ЧИСТОГО ТЕКСТА (для сравнения):")
    print("-" * 50)
    results_clean = adapter.find_sensitive_data(test_text_clean)
    
    print(f"\n✅ Найдено {len(results_clean)} элементов:")
    for i, result in enumerate(results_clean, 1):
        if result['category'] == 'government_org':
            start = result['position']['start']
            end = result['position']['end']
            found_text = test_text_clean[start:end]
            print(f"   {i}. '{result['original_value']}' (позиция {start}-{end})")
            print(f"      Метод: {result['method']}")
            print(f"      Confidence: {result['confidence']:.3f}")
            print(f"      Реальный текст: '{found_text}'")
            print()
    
    # Анализируем результаты
    print("📊 АНАЛИЗ РЕЗУЛЬТАТОВ:")
    print("-" * 50)
    
    gov_orgs_with_breaks = [r for r in results_with_breaks if r['category'] == 'government_org']
    gov_orgs_clean = [r for r in results_clean if r['category'] == 'government_org']
    
    print(f"🏛️ Государственных организаций (с переносами): {len(gov_orgs_with_breaks)}")
    print(f"🏛️ Государственных организаций (чистый текст): {len(gov_orgs_clean)}")
    
    # Проверяем, что нашли полные названия
    full_names_found = []
    partial_names_found = []
    
    for result in gov_orgs_with_breaks:
        name_length = len(result['original_value'].split())
        if name_length >= 6:  # Полные названия обычно длинные
            full_names_found.append(result['original_value'])
        else:
            partial_names_found.append(result['original_value'])
    
    print(f"📏 Полных названий найдено: {len(full_names_found)}")
    for name in full_names_found:
        print(f"   ✅ '{name}' ({len(name.split())} слов)")
    
    print(f"📏 Частичных названий найдено: {len(partial_names_found)}")
    for name in partial_names_found:
        print(f"   ⚠️ '{name}' ({len(name.split())} слов)")
    
    # Проверяем успех исправления
    if len(full_names_found) > len(partial_names_found):
        print("\n🎉 УСПЕХ! Больше полных названий, чем частичных")
    elif len(gov_orgs_with_breaks) > 0:
        print("\n⚠️ ЧАСТИЧНО: Найдены организации, но нужно дополнительная настройка")
    else:
        print("\n❌ НЕУДАЧА: Организации не найдены")
    
    return results_with_breaks, results_clean


if __name__ == "__main__":
    test_line_break_fix()