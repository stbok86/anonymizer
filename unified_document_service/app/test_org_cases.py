#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Тест детекции организаций в разных падежах"""

import requests

url = "http://localhost:8006/analyze"

test_cases = [
    "Общество с ограниченной ответственностью «КАМА Технологии»",  # Именительный
    "Общества с ограниченной ответственностью «КАМА Технологии»",  # Родительный
    "Обществу с ограниченной ответственностью «КАМА Технологии»",  # Дательный
    "Обществом с ограниченной ответственностью «КАМА Технологии»", # Творительный
    "Акционерное общество «Тест»",           # Именительный
    "Акционерного общества «Тест»",          # Родительный
    "Закрытое акционерное общество «Компания»",
    "Закрытого акционерного общества «Компания»",
]

print("="*100)
print("ТЕСТ ПАДЕЖЕЙ ОРГАНИЗАЦИЙ")
print("="*100)

for text in test_cases:
    response = requests.post(url, json={"blocks": [{"block_id": "test", "content": text}]}, timeout=10)
    
    if response.status_code == 200:
        result = response.json()
        detections = result.get('detections', [])
        org_detections = [d for d in detections if d.get('category') == 'organization']
        
        status = "✅" if org_detections else "❌"
        print(f"\n{status} '{text}'")
        
        if org_detections:
            for det in org_detections:
                print(f"    Найдено: '{det.get('original_value', '')}' (conf: {det.get('confidence', 0):.2f})")
        else:
            print(f"    НЕ НАЙДЕНО")
