#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Отладочный скрипт для проверки замен в реальном документе
"""

import sys
import os
import tempfile
from docx import Document

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from full_anonymizer import FullAnonymizer

def debug_anonymization():
    """Отлаживаем процесс анонимизации"""
    
    input_path = r'C:\Projects\Anonymizer\unified_document_service\test_docs\test_01_1_4_SD2.docx'
    
    # Создаем временный файл для вывода
    temp_output = tempfile.NamedTemporaryFile(suffix='.docx', delete=False)
    output_path = temp_output.name
    temp_output.close()
    
    print("=" * 80)
    print("ОТЛАДКА ПРОЦЕССА АНОНИМИЗАЦИИ")
    print("=" * 80)
    
    # Запускаем анонимизацию
    fa = FullAnonymizer()
    result = fa.anonymize_document(input_path, output_path)
    
    print("\n" + "=" * 80)
    print("РЕЗУЛЬТАТЫ АНОНИМИЗАЦИИ")
    print("=" * 80)
    print(f"Статус: {result.get('status', 'unknown')}")
    
    if result.get('status') == 'error':
        print(f"ОШИБКА: {result.get('error_message', 'Unknown error')}")
        print(f"Тип ошибки: {result.get('error_type', 'Unknown')}")
        return result, None
    
    print(f"Всего совпадений: {result.get('matches_count', 'N/A')}")
    print(f"Всего замен: {result.get('statistics', {}).get('total_replacements', 0)}")
    print(f"\nПо категориям:")
    for category, count in result.get('statistics', {}).get('categories', {}).items():
        print(f"  - {category}: {count}")
    
    # Проверяем проблемные строки в выходном документе
    print("\n" + "=" * 80)
    print("ПРОВЕРКА ПРОБЛЕМНЫХ СТРОК В АНОНИМИЗИРОВАННОМ ДОКУМЕНТЕ")
    print("=" * 80)
    
    doc = Document(output_path)
    
    # Проверяем ячейки таблиц
    for table_idx, table in enumerate(doc.tables[:2]):
        print(f"\n📋 Таблица {table_idx + 1}:")
        for row_idx, row in enumerate(table.rows[:3]):
            print(f"  Строка {row_idx}:")
            for cell_idx, cell in enumerate(row.cells[:3]):
                cell_text = cell.text
                print(f"    Ячейка [{row_idx}][{cell_idx}]: {repr(cell_text[:80])}")
                
                # Проверяем наличие проблемных строк
                if "Мясников" in cell_text:
                    print(f"      ⚠️  НАЙДЕНА НЕЗАМЕНЕННАЯ ФИО 'Мясников'!")
                if "ГБУ ПК" in cell_text or "ГБУ\xa0ПК" in cell_text:
                    print(f"      ⚠️  НАЙДЕНА НЕЗАМЕНЕННАЯ ОРГАНИЗАЦИЯ 'ГБУ ПК'!")
                if "Щукина" in cell_text:
                    print(f"      ⚠️  НАЙДЕНА НЕЗАМЕНЕННАЯ ФИО 'Щукина'!")
    
    print(f"\n📄 Анонимизированный документ сохранен: {output_path}")
    
    return result, output_path

if __name__ == "__main__":
    result, output_path = debug_anonymization()
