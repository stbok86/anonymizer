#!/usr/bin/env python3
"""
ОТЛАДКА ПОЗИЦИЙ В ДЕДУПЛИКАЦИИ
=============================

Проверяем точные значения позиций в дедупликации
"""

import requests
import json

def debug_deduplication_positions():
    """Отлаживаем позиции в дедупликации"""
    
    print("🔍 ОТЛАДКА ДЕДУПЛИКАЦИИ")
    print("=" * 40)
    
    test_file = "unified_document_service/test_docs/test_01_1_4_S.docx"
    target_text = "14 августа 2023"
    
    try:
        with open(test_file, 'rb') as f:
            files = {'file': ('test_document.docx', f, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')}
            data = {
                'patterns_file': 'patterns/sensitive_patterns.xlsx',
                'include_nlp': 'false'
            }
            
            response = requests.post(
                "http://localhost:8002/analyze_document",
                files=files,
                data=data,
                timeout=30
            )
        
        if response.status_code == 200:
            result = response.json()
            found_items = result.get('found_items', [])
            
            # Фильтруем table_2 элементы
            table_2_items = [
                item for item in found_items 
                if item.get('original_value') == target_text and item.get('block_id') == 'table_2'
            ]
            
            print(f"✅ Элементов table_2: {len(table_2_items)}")
            
            # Анализируем ключи дедупликации
            print(f"\n🔑 КЛЮЧИ ДЕДУПЛИКАЦИИ:")
            dedup_keys = []
            for i, item in enumerate(table_2_items):
                block_id = item.get('block_id')
                original_value = item.get('original_value', '')
                position = item.get('position', {})
                
                # Точно такой же ключ как в коде
                dedup_key = (block_id, original_value, position.get('start'), position.get('end'))
                dedup_keys.append(dedup_key)
                
                print(f"   Элемент {i+1}:")
                print(f"     block_id: '{block_id}'")
                print(f"     original_value: '{original_value}'")
                print(f"     position: {position}")
                print(f"     dedup_key: {dedup_key}")
                print()
            
            # Проверяем уникальность ключей
            unique_keys = set(dedup_keys)
            print(f"📊 РЕЗУЛЬТАТ ДЕДУПЛИКАЦИИ:")
            print(f"   Всего элементов: {len(table_2_items)}")
            print(f"   Уникальных ключей: {len(unique_keys)}")
            print(f"   Дублированы: {len(table_2_items) != len(unique_keys)}")
            
            if len(table_2_items) != len(unique_keys):
                print(f"\n🚨 НАЙДЕНЫ ДУБЛИКАТЫ!")
                for key in unique_keys:
                    count = dedup_keys.count(key)
                    if count > 1:
                        print(f"   Ключ {key} встречается {count} раз(а)")
            else:
                print(f"\n✅ Все ключи уникальны - дедупликация НЕ должна срабатывать")
                print(f"💡 Проблема НЕ в дедупликации, а в чем-то другом!")
        
    except Exception as e:
        print(f"❌ Ошибка: {str(e)}")

if __name__ == "__main__":
    debug_deduplication_positions()