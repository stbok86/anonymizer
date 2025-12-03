"""
ИТОГОВЫЙ ТЕСТ: Проверка отсутствия случайной генерации UUID
"""
import requests
import base64
import re
from docx import Document
import pandas as pd

print("=" * 80)
print("🎯 ФИНАЛЬНАЯ ПРОВЕРКА: ОТСУТСТВИЕ СЛУЧАЙНОЙ ГЕНЕРАЦИИ UUID")
print("=" * 80)
print()

# Тестовый документ
doc_path = "test_docs/test_01_1_4_SD33.docx"

print("🔄 Анонимизируем документ 3 раза...")
print()

results = []

for i in range(1, 4):
    print(f"   Попытка #{i}...")
    
    with open(doc_path, 'rb') as f:
        files = {'file': ('test.docx', f, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')}
        data = {
            'patterns_file': 'patterns/sensitive_patterns.xlsx',
            'generate_excel_report': 'true'
        }
        
        response = requests.post('http://localhost:8009/anonymize_full', files=files, data=data, timeout=60)
    
    if response.status_code == 200:
        result = response.json()
        
        # Сохраняем Excel
        excel_data = base64.b64decode(result['files_base64']['excel_report_base64'])
        excel_path = f"test_run_{i}.xlsx"
        with open(excel_path, 'wb') as f:
            f.write(excel_data)
        
        # Читаем UUID
        df = pd.read_excel(excel_path)
        uuids = set(df['Замена (идентификатор)'].tolist())
        
        results.append({
            'run': i,
            'uuids': uuids,
            'count': len(uuids)
        })

print()
print("=" * 80)
print("📊 СРАВНЕНИЕ РЕЗУЛЬТАТОВ:")
print("=" * 80)
print()

# Сравниваем UUID между запусками
run1_uuids = results[0]['uuids']
run2_uuids = results[1]['uuids']
run3_uuids = results[2]['uuids']

print(f"Запуск #1: {results[0]['count']} UUID")
print(f"Запуск #2: {results[1]['count']} UUID")
print(f"Запуск #3: {results[2]['count']} UUID")
print()

if run1_uuids == run2_uuids == run3_uuids:
    print("✅ ВСЕ UUID ИДЕНТИЧНЫ во всех 3 запусках!")
    print("✅ Случайная генерация UUID полностью устранена")
    print()
    print("=" * 80)
    print("🎉 ТЕСТ ПРОЙДЕН: UUID ДЕТЕРМИНИСТИЧНЫ")
    print("=" * 80)
else:
    print("❌ UUID ОТЛИЧАЮТСЯ между запусками!")
    
    diff_1_2 = run1_uuids.symmetric_difference(run2_uuids)
    diff_1_3 = run1_uuids.symmetric_difference(run3_uuids)
    diff_2_3 = run2_uuids.symmetric_difference(run3_uuids)
    
    print(f"   Различий между #1 и #2: {len(diff_1_2)}")
    print(f"   Различий между #1 и #3: {len(diff_1_3)}")
    print(f"   Различий между #2 и #3: {len(diff_2_3)}")
    print()
    print("=" * 80)
    print("❌ ТЕСТ НЕ ПРОЙДЕН: ЕСТЬ СЛУЧАЙНАЯ ГЕНЕРАЦИЯ UUID")
    print("=" * 80)
