#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест детекции строк ИЗ РЕАЛЬНОГО ДОКУМЕНТА
"""

import sys
import os

# Добавляем путь к модулям
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from nlp_adapter import NLPAdapter

def test_real_strings():
    """Тестируем строки точно как в документе"""
    
    nlp = NLPAdapter()
    
    test_cases = [
        {
            "name": "FIO from doc - K.S. Myasnikov with nbsp",
            "text": "______________________ К.\xa0С. Мясников",
            "expected_category": "person_name"
        },
        {
            "name": "FIO only - K.S. Myasnikov with nbsp",
            "text": "К.\xa0С. Мясников",
            "expected_category": "person_name"
        },
        {
            "name": "ORG from doc - GBU with nbsp",
            "text": "Главный эксперт управления разработки и развития информационных систем ГБУ\xa0ПК «Центр информационного развития Пермского края»",
            "expected_category": "organization"
        },
        {
            "name": "ORG only - GBU with nbsp",
            "text": "ГБУ\xa0ПК «Центр информационного развития Пермского края»",
            "expected_category": "organization"
        },
    ]
    
    print("=" * 80)
    print("ТЕСТИРОВАНИЕ СТРОК ИЗ РЕАЛЬНОГО ДОКУМЕНТА")
    print("=" * 80)
    
    for case in test_cases:
        print(f"\n{'='*60}")
        print(f"TEST: {case['name']}")
        print(f"Text: {repr(case['text'])}")
        print(f"Expected: {case['expected_category']}")
        print(f"{'='*60}")
        
        # Показываем что происходит с \xa0
        normalized = case['text'].replace('\xa0', ' ')
        if '\xa0' in case['text']:
            print(f"⚠️  CONTAINS \\xa0 (non-breaking space)")
            print(f"   Original: {repr(case['text'][:50])}")
            print(f"   After normalization: {repr(normalized[:50])}")
        
        results = nlp.find_sensitive_data(case['text'])
        
        found_expected = False
        if results:
            print(f"\n✅ Total detections: {len(results)}")
            for detection in results:
                pos = detection.get('position', {})
                start, end = pos.get('start', 0), pos.get('end', 0)
                match_text = case['text'][start:end]
                print(f"   - {detection['category']}: '{match_text}' (conf={detection['confidence']:.2f}, method={detection['method']})")
                if detection['category'] == case['expected_category']:
                    found_expected = True
        else:
            print(f"\n❌ NO DETECTIONS")
        
        if not found_expected:
            print(f"\n⚠️  EXPECTED CATEGORY '{case['expected_category']}' NOT FOUND!")
        else:
            print(f"\n✅ Expected category '{case['expected_category']}' WAS FOUND")

if __name__ == "__main__":
    test_real_strings()
