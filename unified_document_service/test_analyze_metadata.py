#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
sys.path.insert(0, 'app')

from docx_metadata_handler import DocxMetadataHandler

# Тест на оригинальном документе
doc_path = 'test_docs/test_01_1_4_SD33.docx'

print("=" * 80)
print("АНАЛИЗ МЕТАДАННЫХ ОРИГИНАЛЬНОГО ДОКУМЕНТА")
print("=" * 80)

handler = DocxMetadataHandler(doc_path)
metadata = handler.extract_metadata()

print("\n📋 Метаданные core.xml:")
for key, value in metadata.get('core', {}).items():
    print(f"   {key}: {value}")

# Создаем тестовые замены на основе того, что мы знаем
print("\n🔍 Создаем список замен для тестирования find_sensitive_metadata:")

test_replacements = [
    {
        'original_value': 'ЕИСУФХД.13/ОК-2023.3.ПМ.1',
        'uuid': 'test-uuid-001',
        'category': 'information_system'
    },
    {
        'original_value': '312822699534',
        'uuid': 'test-uuid-002',
        'category': 'inn'
    },
    {
        'original_value': 'ЕИСУФХД',
        'uuid': 'test-uuid-003',
        'category': 'information_system'
    }
]

sensitive = handler.find_sensitive_metadata(test_replacements)

print(f"\n🎯 Найдено чувствительных метаданных: {len(sensitive)}")
for i, item in enumerate(sensitive):
    print(f"\n{i+1}. Секция: {item['metadata_section']}")
    print(f"   Свойство: {item.get('metadata_property', 'N/A')}")
    print(f"   Оригинал: '{item['original_value']}'")
    print(f"   UUID: {item.get('uuid', 'N/A')}")
    print(f"   Частичное совпадение: {item.get('partial_match', 'N/A')}")
    print(f"   Confidence: {item.get('confidence', 'N/A')}")
