import sys
import os
sys.path.insert(0, 'app')

from full_anonymizer import FullAnonymizer
from docx import Document

# Перенаправляем вывод в файл для анализа
log_file = open('detailed_anonymization_log.txt', 'w', encoding='utf-8')
original_stdout = sys.stdout
sys.stdout = log_file

try:
    # Создаём anonymizer
    anonymizer = FullAnonymizer(
        nlp_service_url="http://localhost:8006"
    )
    
    # Анонимизируем документ
    result = anonymizer.anonymize_document(
        input_path="test_docs/test_01_1_4_SD33.docx",
        output_path="test_docs/test_01_1_4_SD33_anon.docx",
        excel_report_path="test_docs/test_01_1_4_SD33_report.xlsx"
    )
    
    print("\n" + "="*80)
    print("РЕЗУЛЬТАТ АНОНИМИЗАЦИИ")
    print("="*80)
    print(f"Успех: {result.get('status')}")
    print(f"Всего замен: {result.get('statistics', {}).get('total_replacements', 0)}")
    
finally:
    sys.stdout = original_stdout
    log_file.close()

print("Лог сохранён в detailed_anonymization_log.txt")
print("Просматриваю лог...")

# Ищем детекции министерства в логе
with open('detailed_anonymization_log.txt', 'r', encoding='utf-8') as f:
    lines = f.readlines()
    
in_diagnostic = False
for i, line in enumerate(lines):
    if 'ДИАГНОСТИКА' in line and 'Список всех обнаруженных значений' in line:
        in_diagnostic = True
        print("\n" + "="*80)
        print("НАЙДЕННЫЕ ДЕТЕКЦИИ:")
        print("="*80)
        
    if in_diagnostic:
        print(line.rstrip())
        if line.strip() == '':
            in_diagnostic = False
            
# Ищем попытки замены министерства
print("\n" + "="*80)
print("ПОПЫТКИ ЗАМЕНЫ МИНИСТЕРСТВА:")
print("="*80)

found_ministry_replacement = False
for i, line in enumerate(lines):
    if 'МИНИСТЕРСТВО' in line.upper() and 'SINGLE_REPLACEMENT' in line:
        found_ministry_replacement = True
        # Печатаем контекст: 5 строк до и 20 строк после
        start = max(0, i - 5)
        end = min(len(lines), i + 20)
        for j in range(start, end):
            print(lines[j].rstrip())
        print("-" * 80)
        break

if not found_ministry_replacement:
    print("❌ НЕ НАЙДЕНО попыток замены МИНИСТЕРСТВА в логе SINGLE_REPLACEMENT!")
