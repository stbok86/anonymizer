#!/usr/bin/env python3
"""Анализ блоков с sensitive_matches"""

import json

# Загружаем результат теста
with open('test_result.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

blocks = data['blocks']
print(f"Всего блоков: {len(blocks)}")

# Находим блоки с sensitive_matches
matches = [b for b in blocks if 'sensitive_matches' in b]
print(f"Найдено блоков с sensitive_matches: {len(matches)}")

# Показываем детали
for b in matches[:10]:  # Показываем первые 10
    print(f"\n  {b['block_id']} ({b['type']}):")
    print(f"    Текст: {b['text'][:100]}...")
    print(f"    Совпадения: {len(b['sensitive_matches'])}")
    for m in b['sensitive_matches']:
        print(f"      - {m['source']}: {m['text']}")

# Проверяем типы header блоков
header_blocks = [b for b in blocks if 'header' in b.get('type', '')]
print(f"\nНайдено header блоков: {len(header_blocks)}")
for hb in header_blocks:
    print(f"  {hb['block_id']}: {hb['text']}")
    print(f"    applies_to: {hb.get('applies_to', 'не указано')}")