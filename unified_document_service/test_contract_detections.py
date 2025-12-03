#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
sys.path.insert(0, 'app')

from block_builder import BlockBuilder
from docx import Document

doc_path = 'test_docs/test_01_1_4_SD33.docx'

print("=" * 80)
print("АНАЛИЗ ДЕТЕКЦИЙ ДЛЯ КОНТРАКТА")
print("=" * 80)

# Загружаем документ
doc = Document(doc_path)
builder = BlockBuilder()
blocks = builder.build_blocks(doc)

# Находим блок с контрактом
target = "Контракту от 14 августа 2023 г. № 13/ОК-2023"

print(f"\n🔍 Ищем блоки содержащие: '{target}'")

for block in blocks:
    text = block.get('text', '') or block.get('content', '')
    if "13/ОК-2023" in text:
        print(f"\n📦 Block ID: {block['block_id']}")
        print(f"   Type: {block.get('type', 'unknown')}")
        print(f"   Text: '{text[:200]}...'")

# Теперь проверим детекции от NLP Service
print("\n\n🤖 Проверка детекций NLP Service...")

import requests

# Отправляем блоки в NLP Service
response = requests.post('http://localhost:8006/detect', json={'blocks': blocks[:30]})  # Первые 30 блоков

if response.status_code == 200:
    result = response.json()
    detections = result.get('detections', [])
    
    contract_detections = [d for d in detections if '13/ОК-2023' in d.get('text', '') or 'августа 2023' in d.get('text', '')]
    
    print(f"Всего детекций NLP: {len(detections)}")
    print(f"Детекций с контрактом: {len(contract_detections)}")
    
    for i, d in enumerate(contract_detections):
        print(f"\n{i+1}. Детекция:")
        print(f"   Text: '{d.get('text', 'N/A')}'")
        print(f"   Category: {d.get('category', 'N/A')}")
        print(f"   Method: {d.get('method', 'N/A')}")
        print(f"   Position: {d.get('position', 'N/A')}")
        print(f"   Block ID: {d.get('block_id', 'N/A')}")

# Проверим Rule Engine
print("\n\n📋 Проверка детекций Rule Engine...")

from rule_adapter import RuleEngineAdapter

adapter = RuleEngineAdapter(patterns_path='patterns/sensitive_patterns.xlsx')
rule_detections = adapter.find_matches_in_blocks(blocks[:30])

contract_rule_detections = [d for d in rule_detections if '13/ОК-2023' in d.get('original_value', '') or 'августа 2023' in d.get('original_value', '')]

print(f"Всего детекций Rule Engine: {len(rule_detections)}")
print(f"Детекций с контрактом: {len(contract_rule_detections)}")

for i, d in enumerate(contract_rule_detections):
    print(f"\n{i+1}. Детекция:")
    print(f"   Original value: '{d.get('original_value', 'N/A')}'")
    print(f"   Category: {d.get('category', 'N/A')}")
    print(f"   Position: {d.get('position', 'N/A')}")
    print(f"   Block ID: {d.get('block_id', 'N/A')}")

print("\n" + "=" * 80)
