#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
from docx import Document

# Шаг 1: Анонимизация через API
print("=" * 80)
print("ТЕСТ ОБРАБОТКИ МЕТАДАННЫХ")
print("=" * 80)

doc_path = 'test_docs/test_01_1_4_SD33.docx'

print("\n📤 Отправка документа на анонимизацию...")

with open(doc_path, 'rb') as f:
    files = {'file': ('test.docx', f, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')}
    data = {
        'patterns_file': 'patterns/sensitive_patterns.xlsx',
        'generate_excel_report': 'true'
    }
    
    response = requests.post('http://localhost:8009/anonymize_full', files=files, data=data, timeout=120)

if response.status_code == 200:
    result = response.json()
    print(f"✅ Анонимизация выполнена")
    print(f"   Всего замен: {result.get('statistics', {}).get('total_replacements', 0)}")
    
    # Сохраняем анонимизированный документ
    import base64
    doc_data = base64.b64decode(result['files_base64']['anonymized_document_base64'])
    anon_path = 'test_docs/test_metadata_check_anon.docx'
    with open(anon_path, 'wb') as f:
        f.write(doc_data)
    
    print(f"   Сохранено: {anon_path}")
    
    # Шаг 2: Проверяем метаданные
    print("\n🔍 Проверка метаданных...")
    
    import zipfile
    import xml.etree.ElementTree as ET
    
    with zipfile.ZipFile(anon_path, 'r') as docx_zip:
        if 'docProps/core.xml' in docx_zip.namelist():
            core_xml_content = docx_zip.read('docProps/core.xml')
            
            search_values = ['312822699534', 'ЕИСУФХД']
            
            for search in search_values:
                if search in core_xml_content.decode('utf-8'):
                    print(f"   ❌ НАЙДЕНО: '{search}' присутствует в core.xml")
                else:
                    print(f"   ✅ НЕ НАЙДЕНО: '{search}' отсутствует в core.xml (заменено)")
else:
    print(f"❌ Ошибка: {response.status_code}")
    print(response.text)

print("\n" + "=" * 80)
