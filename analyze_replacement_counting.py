#!/usr/bin/env python3
"""
АНАЛИЗ ПОДСЧЕТА ЗАМЕН - Шаг 3
============================

Детальный анализ того, как рассчитывается значение "Выполнено замен: 25"
на шаге 3 в интерфейсе
"""

import requests
import json
import base64
import tempfile
import os
from docx import Document

def analyze_replacement_counting():
    """Анализирует подсчет замен от детекции до отображения"""
    
    print("🔍 АНАЛИЗ ПОДСЧЕТА ЗАМЕН")
    print("=" * 80)
    
    # Тестовый файл
    test_file = "unified_document_service/test_docs/test_01_1_4_S.docx"
    
    if not os.path.exists(test_file):
        print(f"❌ Тестовый файл не найден: {test_file}")
        return
    
    # ЭТАП 1: Анализ документа (имитация Шага 1)
    print("📊 ЭТАП 1: АНАЛИЗ ДОКУМЕНТА")
    print("-" * 40)
    
    try:
        with open(test_file, 'rb') as f:
            files = {'file': ('test_document.docx', f, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')}
            data = {
                'patterns_file': 'patterns/sensitive_patterns.xlsx',
                'include_nlp': 'true'
            }
            
            response = requests.post(
                "http://localhost:8002/analyze_document",  # Unified Document Service
                files=files,
                data=data,
                timeout=30
            )
        
        if response.status_code == 200:
            result = response.json()
            found_items = result.get('items', [])
            
            print(f"✅ Найдено элементов: {len(found_items)}")
            print(f"   Источники:")
            
            # Анализируем источники
            sources = {}
            for item in found_items:
                source = item.get('source', 'unknown')
                if source not in sources:
                    sources[source] = 0
                sources[source] += 1
            
            for source, count in sources.items():
                print(f"     {source}: {count} элементов")
            
            # Анализируем категории
            categories = {}
            for item in found_items:
                category = item.get('category', 'unknown')
                if category not in categories:
                    categories[category] = 0
                categories[category] += 1
            
            print(f"   Категории:")
            for category, count in categories.items():
                print(f"     {category}: {count} элементов")
        else:
            print(f"❌ Ошибка анализа: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Ошибка при анализе: {str(e)}")
        return
    
    # ЭТАП 2: Симулируем выбор пользователя (имитация Шага 2)
    print(f"\n🎯 ЭТАП 2: ВЫБОР ПОЛЬЗОВАТЕЛЯ")
    print("-" * 40)
    
    # Предположим, что пользователь выбрал 25 элементов из найденных
    user_approved_count = 25
    
    # Выберем первые 25 элементов (как если бы пользователь их одобрил)
    approved_items = found_items[:user_approved_count] if len(found_items) >= user_approved_count else found_items
    actual_approved = len(approved_items)
    
    print(f"👤 Пользователь одобрил к анонимизации: {actual_approved} элементов")
    
    # Показываем примеры одобренных
    for i, item in enumerate(approved_items[:3]):
        print(f"   {i+1}. '{item.get('original_value', 'N/A')}' ({item.get('category', 'N/A')})")
    if len(approved_items) > 3:
        print(f"   ... и еще {len(approved_items) - 3} элементов")
    
    # ЭТАП 3: Селективная анонимизация (backend)
    print(f"\n🔧 ЭТАП 3: СЕЛЕКТИВНАЯ АНОНИМИЗАЦИЯ")
    print("-" * 40)
    
    # Подготавливаем данные для селективной анонимизации
    selected_items = []
    for item in approved_items:
        selected_item = {
            'block_id': item.get('block_id', ''),
            'original_value': item.get('original_value', ''),
            'uuid': item.get('uuid', ''),
            'position': item.get('position', {}),
            'category': item.get('category', ''),
            'confidence': item.get('confidence', 1.0)
        }
        selected_items.append(selected_item)
    
    print(f"📝 Отправляем на анонимизацию: {len(selected_items)} элементов")
    
    try:
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
            print(f"📊 Результат backend:")
            print(f"   • Статус: {result.get('status', 'N/A')}")
            print(f"   • Сообщение: {result.get('message', 'N/A')}")
            print(f"   • Элементов отправлено: {result.get('selected_items_count', 'N/A')}")
            print(f"   • Замен выполнено: {result.get('replacements_applied', 'N/A')}")
            
            # Детальная статистика
            if 'statistics' in result:
                stats = result['statistics']
                print(f"   • Детальная статистика:")
                print(f"     - total_replacements: {stats.get('total_replacements', 'N/A')}")
                print(f"     - blocks_processed: {stats.get('blocks_processed', 'N/A')}")
                print(f"     - categories: {stats.get('categories', {})}")
            
        else:
            print(f"❌ Ошибка анонимизации: {response.status_code}")
            print(f"   Ответ: {response.text}")
            return
            
    except Exception as e:
        print(f"❌ Ошибка при анонимизации: {str(e)}")
        return
    
    # ЭТАП 4: Frontend обработка (имитация отображения на Шаге 3)
    print(f"\n🖥️ ЭТАП 4: ОТОБРАЖЕНИЕ В ИНТЕРФЕЙСЕ")
    print("-" * 40)
    
    # Симулируем логику frontend из streamlit_app.py
    # В anonymize_document_full_api сохраняется статистика:
    frontend_stats = {
        'total_found': len(found_items),  # Количество найденных элементов
        'total_anonymized': len(approved_items),  # Количество отправленных на анонимизацию 
        'replacement_stats': result.get('statistics', {}),  # Детальная статистика замен
        'replacements_applied': result.get('replacements_applied', 0)  # Фактически выполненные замены
    }
    
    print(f"📊 Статистика для отображения:")
    print(f"   • total_found (найдено): {frontend_stats['total_found']}")
    print(f"   • total_anonymized (одобрено): {frontend_stats['total_anonymized']}")
    print(f"   • replacements_applied (выполнено): {frontend_stats['replacements_applied']}")
    
    # В step3_download_results отображается:
    # st.metric(label="🔒 Анонимизировано чувствительных данных", value=f"{stats.get('replacements_applied', stats.get('total_anonymized', 0))} элементов")
    # st.info(f"✅ Выполнено замен: {replacement_stats.get('total_replacements', 0)}")
    
    display_value = frontend_stats.get('replacements_applied', frontend_stats.get('total_anonymized', 0))
    replacement_stats = frontend_stats.get('replacement_stats', {})
    replacements_count = replacement_stats.get('total_replacements', 0)
    
    print(f"\n🎯 ИТОГОВОЕ ОТОБРАЖЕНИЕ НА ШАГЕ 3:")
    print("=" * 50)
    print(f"📊 'Анонимизировано чувствительных данных': {display_value} элементов")
    print(f"✅ 'Выполнено замен': {replacements_count}")
    
    print(f"\n💡 ОБЪЯСНЕНИЕ:")
    print("   • 'Анонимизировано' = количество фактически замененных элементов")
    print("   • 'Выполнено замен' = количество успешных операций замены в документе")
    print("   • Эти значения могут различаться из-за:")
    print("     - Элементов в одном блоке (параграфе/таблице)")
    print("     - Ошибок при замене (неразрывные пробелы, split runs)")
    print("     - Дублирующихся элементов в разных позициях")

if __name__ == "__main__":
    analyze_replacement_counting()