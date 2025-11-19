#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Диагностика PhraseMatcher - проверяем точно какие фразы ищет и находит
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'patterns'))

import spacy
from spacy.matcher import PhraseMatcher
from government_organizations import GOVERNMENT_ORGANIZATIONS

def diagnose_phrase_matcher_detailed():
    """Детальная диагностика PhraseMatcher"""
    
    print("=" * 80)
    print("🔬 ДЕТАЛЬНАЯ ДИАГНОСТИКА PHRASEMATCHER")
    print("=" * 80)
    
    # Загружаем spaCy модель
    nlp = spacy.load("ru_core_news_sm")
    
    # Создаем PhraseMatcher
    phrase_matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
    
    print(f"📚 СЛОВАРЬ СОДЕРЖИТ {len(GOVERNMENT_ORGANIZATIONS)} ОРГАНИЗАЦИЙ:")
    print("-" * 60)
    
    # Добавляем фразы и показываем их
    patterns = []
    for i, org in enumerate(GOVERNMENT_ORGANIZATIONS, 1):
        pattern_doc = nlp(org.lower())
        patterns.append(pattern_doc)
        word_count = len(org.split())
        print(f"   {i:2d}. '{org}' ({word_count} слов)")
        if word_count >= 6:
            print(f"       ✅ ДЛИННОЕ НАЗВАНИЕ - ПРИОРИТЕТ")
        elif word_count >= 4:
            print(f"       🟡 СРЕДНЕЕ НАЗВАНИЕ")
        else:
            print(f"       🔸 КОРОТКОЕ НАЗВАНИЕ")
    
    # Добавляем все паттерны в matcher
    phrase_matcher.add("government_org", patterns)
    
    # Тестовый текст с переносами
    test_text = "МИНИСТЕРСТВО ИНФОРМАЦИОННОГО РАЗВИТИЯ И СВЯЗИ\nПЕРМСКОГО КРАЯ"
    normalized_text = "МИНИСТЕРСТВО ИНФОРМАЦИОННОГО РАЗВИТИЯ И СВЯЗИ ПЕРМСКОГО КРАЯ"
    
    print(f"\n📝 ИСХОДНЫЙ ТЕКСТ:")
    print(f"   '{test_text}'")
    print(f"\n📝 НОРМАЛИЗОВАННЫЙ ТЕКСТ:")
    print(f"   '{normalized_text}'")
    
    # Обрабатываем оба варианта
    for text_type, text in [("ИСХОДНЫЙ", test_text), ("НОРМАЛИЗОВАННЫЙ", normalized_text)]:
        print(f"\n🔍 АНАЛИЗ {text_type} ТЕКСТА:")
        print("-" * 60)
        
        doc = nlp(text.lower())
        
        # Показываем токенизацию
        print("🎯 ТОКЕНИЗАЦИЯ:")
        for i, token in enumerate(doc):
            token_type = "SPACE" if token.is_space else "WORD"
            print(f"   {i}: '{token.text}' ({token_type})")
        
        # Ищем совпадения
        matches = phrase_matcher(doc)
        
        print(f"\n🎯 НАЙДЕННЫЕ СОВПАДЕНИЯ: {len(matches)}")
        
        if matches:
            # Сортируем по длине (самые длинные сначала)
            matches_with_info = []
            for match_id, start, end in matches:
                matched_text = doc[start:end].text
                char_start = doc[start].idx
                char_end = doc[end-1].idx + len(doc[end-1].text)
                matches_with_info.append({
                    'text': matched_text,
                    'start': start,
                    'end': end,
                    'char_start': char_start,
                    'char_end': char_end,
                    'length': len(matched_text.split())
                })
            
            # Сортируем по длине (самые длинные сначала)
            matches_with_info.sort(key=lambda x: x['length'], reverse=True)
            
            for i, match_info in enumerate(matches_with_info, 1):
                print(f"   {i}. '{match_info['text']}' (токены {match_info['start']}-{match_info['end']}, {match_info['length']} слов)")
                print(f"      Позиция в тексте: {match_info['char_start']}-{match_info['char_end']}")
                
                # Ищем соответствующую фразу в словаре
                for org in GOVERNMENT_ORGANIZATIONS:
                    if org.lower() == match_info['text']:
                        print(f"      ✅ ТОЧНОЕ СООТВЕТСТВИЕ: '{org}'")
                        break
                else:
                    print(f"      ❓ Частичное соответствие или неточность")
        else:
            print("   ❌ НИ ОДНОГО СОВПАДЕНИЯ НЕ НАЙДЕНО")
    
    # Проверяем, есть ли в словаре полное название
    print(f"\n🎯 ПРОВЕРКА СЛОВАРЯ НА ПОЛНОЕ НАЗВАНИЕ:")
    print("-" * 60)
    
    full_name = "министерство информационного развития и связи пермского края"
    partial_name = "министерство информационного развития"
    
    full_found = any(org.lower() == full_name for org in GOVERNMENT_ORGANIZATIONS)
    partial_found = any(org.lower() == partial_name for org in GOVERNMENT_ORGANIZATIONS)
    
    print(f"   Полное название '{full_name}': {'✅ ЕСТЬ' if full_found else '❌ НЕТ'}")
    print(f"   Частичное '{partial_name}': {'✅ ЕСТЬ' if partial_found else '❌ НЕТ'}")
    
    if full_found and partial_found:
        print("   ⚠️ КОНФЛИКТ: И полное, и частичное названия в словаре!")
        print("   💡 PhraseMatcher может находить первое встреченное (более короткое)")
    elif full_found:
        print("   ✅ ХОРОШО: Только полное название в словаре")
    elif partial_found:
        print("   ⚠️ ПРОБЛЕМА: Только частичное название в словаре")
    else:
        print("   ❌ ОШИБКА: Ни полного, ни частичного названия нет в словаре")


if __name__ == "__main__":
    diagnose_phrase_matcher_detailed()