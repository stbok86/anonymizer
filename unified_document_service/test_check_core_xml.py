#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from docx import Document
import zipfile
import xml.etree.ElementTree as ET

# Путь к анонимизированному документу
anon_doc_path = 'test_docs/test_01_1_4_SD33_anon.docx'

print("=" * 80)
print("ПРОВЕРКА МЕТАДАННЫХ CORE.XML")
print("=" * 80)

# Открываем документ как zip-архив
with zipfile.ZipFile(anon_doc_path, 'r') as docx_zip:
    # Читаем core.xml
    if 'docProps/core.xml' in docx_zip.namelist():
        core_xml_content = docx_zip.read('docProps/core.xml')
        
        print("\n📄 Содержимое docProps/core.xml:")
        print("-" * 80)
        print(core_xml_content.decode('utf-8'))
        print("-" * 80)
        
        # Парсим XML
        root = ET.fromstring(core_xml_content)
        
        print("\n🔍 Поиск конкретных значений:")
        search_values = ['312822699534', 'ЕИСУФХД']
        
        for search in search_values:
            if search in core_xml_content.decode('utf-8'):
                print(f"   ❌ НАЙДЕНО: '{search}' присутствует в core.xml")
            else:
                print(f"   ✅ НЕ НАЙДЕНО: '{search}' отсутствует в core.xml")
        
        # Выводим все текстовые значения
        print("\n📋 Все текстовые значения в core.xml:")
        for elem in root.iter():
            if elem.text and elem.text.strip():
                print(f"   <{elem.tag}>: {elem.text}")
    else:
        print("❌ Файл docProps/core.xml не найден в документе")

print("\n" + "=" * 80)
