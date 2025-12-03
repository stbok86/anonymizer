"""
Детальный анализ UUID в таблице замен
"""
import pandas as pd
import re
from docx import Document

# Читаем Excel таблицу
excel_path = "test_replacements.xlsx"
df = pd.read_excel(excel_path)

print("=" * 80)
print("📋 ДЕТАЛЬНЫЙ АНАЛИЗ ТАБЛИЦЫ ЗАМЕН")
print("=" * 80)
print()

print(f"Всего записей в таблице: {len(df)}")
print()

# Читаем документ
doc = Document("test_anonymized.docx")
doc_text = "\n".join([p.text for p in doc.paragraphs])

# Для каждой записи проверяем, есть ли UUID в документе
print("🔍 Проверка каждой записи:")
print()

missing_in_doc = []
found_in_doc = []

for idx, row in df.iterrows():
    num = row['№']
    original = row['Исходные данные']
    uuid_val = row['Замена (идентификатор)']
    
    # Проверяем, есть ли UUID в документе
    if uuid_val in doc_text:
        found_in_doc.append((num, original, uuid_val))
        status = "✅ Есть в документе"
    else:
        missing_in_doc.append((num, original, uuid_val))
        status = "❌ НЕТ в документе"
    
    print(f"{num:2}. {status}")
    print(f"    Оригинал: '{original}'")
    print(f"    UUID:     {uuid_val}")
    print()

print("=" * 80)
print("📊 СВОДКА:")
print("=" * 80)
print(f"✅ Найдено в документе:  {len(found_in_doc)}")
print(f"❌ Отсутствует в документе: {len(missing_in_doc)}")
print()

if missing_in_doc:
    print("⚠️ Записи отсутствующие в документе:")
    for num, original, uuid_val in missing_in_doc:
        print(f"   {num}. '{original}'")
    print()
    
    # Проверим, есть ли оригинальные значения в документе
    print("🔎 Проверка: может быть оригинальные значения не заменились?")
    for num, original, uuid_val in missing_in_doc:
        if original in doc_text:
            print(f"   ⚠️ ПРОБЛЕМА #{num}: '{original}' ОСТАЛОСь БЕЗ ЗАМЕНЫ в документе!")
        else:
            print(f"   ✅ #{num}: '{original}' нет в документе (возможно не нужно было заменять)")
