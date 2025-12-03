#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Проверка формата ответа NLP Service API"""

import requests
import json

url = "http://localhost:8006/analyze"

# Тест с ЕИС УФХД
payload = {
    "blocks": [
        {
            "block_id": "test_abbr",
            "content": "ЕИС УФХД"
        }
    ]
}

print("="*100)
print("ТЕСТ ФОРМАТА ОТВЕТА API")
print("="*100)
print(f"\n📤 Запрос: {json.dumps(payload, ensure_ascii=False, indent=2)}")

response = requests.post(url, json=payload, timeout=10)

print(f"\n✅ Статус: {response.status_code}")
print(f"\n📥 Ответ (RAW JSON):")
print(json.dumps(response.json(), ensure_ascii=False, indent=2))

# Разбор структуры
result = response.json()
detections = result.get('detections', [])

print(f"\n📊 Количество детекций: {len(detections)}")

if detections:
    print("\n🔍 Структура первой детекции:")
    det = detections[0]
    for key, value in det.items():
        print(f"  - {key}: {repr(value)}")
