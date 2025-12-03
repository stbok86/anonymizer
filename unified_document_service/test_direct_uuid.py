#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
sys.path.insert(0, 'app')

from full_anonymizer import FullAnonymizer
from docx import Document

doc_path = 'test_docs/test_01_1_4_SD33.docx'

print("=" * 80)
print("ПРЯМОЙ ТЕСТ: UUID Консистентность")
print("=" * 80)

anonymizer = FullAnonymizer(patterns_path='patterns/sensitive_patterns.xlsx')

result = anonymizer.anonymize_document(
    input_path=doc_path,
    output_path='test_direct_anon.docx',
    excel_report_path='test_direct_report.xlsx'
)

print(f"\nРезультат: {result['status']}")
print(f"Всего замен: {result.get('statistics', {}).get('total_replacements', 0)}")

# Проверяем normalized_replacements
normalized = result.get('statistics', {}).get('normalized_replacements', [])
print(f"\nНормализованных замен: {len(normalized)}")

if len(normalized) > 0:
    print(f"\nПервые 3 нормализованные замены:")
    for i, r in enumerate(normalized[:3], 1):
        print(f"{i}. '{r.get('original_value', 'N/A')[:50]}' → '{r.get('uuid', 'N/A')}'")
else:
    print("\n⚠️ normalized_replacements пустой или отсутствует!")

print("\n" + "=" * 80)
