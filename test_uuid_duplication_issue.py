#!/usr/bin/env python3
"""
ТЕСТ ВОСПРОИЗВЕДЕНИЯ ПРОБЛЕМЫ ДУБЛИРОВАНИЯ UUID
===============================================

Воспроизводим проблему, когда одинаковый текст "14 августа 2023" 
получает один UUID для трех разных позиций
"""

import requests
import json
import tempfile
import shutil

def test_uuid_duplication_issue():
    """Тестирует проблему дублирования UUID"""
    
    print("🔍 ТЕСТ ВОСПРОИЗВЕДЕНИЯ ПРОБЛЕМЫ ДУБЛИРОВАНИЯ UUID")
    print("=" * 70)
    
    test_file = "unified_document_service/test_docs/test_01_1_4_S.docx"
    
    # ЭТАП 1: Анализ документа
    print("📊 ЭТАП 1: АНАЛИЗ ДОКУМЕНТА")
    print("-" * 30)
    
    try:
        with open(test_file, 'rb') as f:
            files = {'file': ('test_document.docx', f, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')}
            data = {
                'patterns_file': 'patterns/sensitive_patterns.xlsx',
                'include_nlp': 'false'  # Пока только Rule Engine
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
            
            print(f"✅ Найдено элементов: {len(found_items)}")
            
            # Анализируем все элементы с "14 августа 2023"
            target_text = "14 августа 2023"
            target_items = [item for item in found_items if item.get('original_value') == target_text]
            
            print(f"\n🎯 ЭЛЕМЕНТЫ С '{target_text}': {len(target_items)}")
            print("-" * 50)
            
            for i, item in enumerate(target_items):
                print(f"📄 Элемент {i+1}:")
                print(f"   block_id: {item.get('block_id')}")
                print(f"   original_value: '{item.get('original_value')}'")
                print(f"   uuid: {item.get('uuid')}")
                print(f"   position: {item.get('position')}")
                print(f"   source: {item.get('source')}")
                print(f"   confidence: {item.get('confidence')}")
                print()
            
            # ЭТАП 2: Симулируем выбор пользователя
            print("👤 ЭТАП 2: СИМУЛИРУЕМ ВЫБОР ПОЛЬЗОВАТЕЛЯ")
            print("-" * 40)
            
            # Пользователь в UI видит только ОДИН элемент "14 августа 2023"
            # но система может выбрать любой из найденных для отправки
            
            # Возьмем первый элемент (как это делает UI при дедупликации визуально)
            if target_items:
                selected_item = target_items[0]  # Берем первый найденный
                print(f"🎯 Пользователь видит и выбирает:")
                print(f"   Текст: '{selected_item.get('original_value')}'")
                print(f"   UUID: {selected_item.get('uuid')}")
                print(f"   block_id: {selected_item.get('block_id')}")
                
                # НО! Frontend может отправить ВСЕ вхождения этого текста
                print(f"\n📤 НО ОТПРАВЛЯЮТСЯ ВСЕ ВХОЖДЕНИЯ:")
                for i, item in enumerate(target_items):
                    print(f"   {i+1}. {item.get('block_id')} - UUID: {item.get('uuid')}")
                
                # ЭТАП 3: Селективная анонимизация
                print(f"\n🔧 ЭТАП 3: СЕЛЕКТИВНАЯ АНОНИМИЗАЦИЯ")
                print("-" * 40)
                
                # Отправляем все найденные элементы (как делает UI)
                selected_items = []
                for item in target_items:
                    selected_item = {
                        'block_id': item.get('block_id', ''),
                        'original_value': item.get('original_value', ''),
                        'uuid': item.get('uuid', ''),  # ВОТ ПРОБЛЕМА! Разные UUID!
                        'position': item.get('position', {}),
                        'category': item.get('category', ''),
                        'confidence': item.get('confidence', 1.0)
                    }
                    selected_items.append(selected_item)
                
                print(f"📝 Отправляем на анонимизацию: {len(selected_items)} элементов")
                
                with open(test_file, 'rb') as f:
                    files = {'file': ('test_document.docx', f, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')}
                    data = {
                        'patterns_file': 'patterns/sensitive_patterns.xlsx',
                        'selected_items': json.dumps(selected_items)
                    }
                    
                    response = requests.post(
                        "http://localhost:8002/anonymize_selected",
                        files=files,
                        data=data,
                        timeout=30
                    )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ Анонимизация завершена")
                    print(f"📊 Результат: {result.get('status')}")
                    print(f"🔢 Замен применено: {result.get('replacements_applied')}")
                    
                    # ЭТАП 4: Анализ результата
                    print(f"\n🔍 ЭТАП 4: АНАЛИЗ РЕЗУЛЬТАТА")
                    print("-" * 30)
                    
                    print(f"💡 ПРОБЛЕМА:")
                    print(f"   • Найдено элементов с '{target_text}': {len(target_items)}")
                    print(f"   • У каждого свой UUID (правильно для анализа)")
                    print(f"   • Но при замене каждый сохраняет СВОЙ UUID")
                    print(f"   • В результате в документе: {len(target_items)} разных UUID для одного текста!")
                    print(f"   • ДОЛЖНО БЫТЬ: 1 UUID для всех вхождений одинакового текста")
                
        else:
            print(f"❌ Ошибка анализа: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Ошибка: {str(e)}")

if __name__ == "__main__":
    test_uuid_duplication_issue()