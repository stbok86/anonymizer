#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from docx import Document

doc = Document('test_docs/test_01_1_4_SD33_anon.docx')

# Проверяем секцию 1 (первая с содержимым)
header = doc.sections[1].header

print("=" * 80)
print("ПРОВЕРКА ЗАГОЛОВКОВ В АНОНИМИЗИРОВАННОМ ДОКУМЕНТЕ")
print("=" * 80)

# Параграфы
print("\n1. ПАРАГРАФЫ:")
for i, p in enumerate(header.paragraphs):
    print(f"   Параграф {i}: {p.text}")

# SDT элементы (Structured Document Tags)
print("\n2. SDT ЭЛЕМЕНТЫ:")
try:
    sdt_elements = header._element.xpath('.//w:sdt', namespaces={'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'})
except TypeError:
    sdt_elements = header._element.xpath('.//w:sdt')

for i, sdt in enumerate(sdt_elements):
    # Получаем текст из SDT
    try:
        text_elements = sdt.xpath('.//w:t', namespaces={'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'})
    except TypeError:
        text_elements = sdt.xpath('.//w:t')
    
    text_content = ''.join([t.text for t in text_elements if t.text])
    print(f"   SDT {i}: {text_content}")

# Проверим, есть ли где-то оригинальные значения
print("\n3. ПОИСК ОРИГИНАЛЬНЫХ ЗНАЧЕНИЙ:")
search_values = ['ЕИСУФХД.13/ОК-2023.3.ПМ.1', '312822699534']
for search in search_values:
    found = False
    try:
        all_text = header._element.xpath('.//w:t', namespaces={'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'})
    except TypeError:
        all_text = header._element.xpath('.//w:t')
    
    for t in all_text:
        if t.text and search in t.text:
            found = True
            print(f"   ❌ НАЙДЕН оригинал: '{search}' в тексте: '{t.text}'")
    
    if not found:
        print(f"   ✅ Оригинал '{search}' НЕ найден (заменён)")

print("\n" + "=" * 80)
