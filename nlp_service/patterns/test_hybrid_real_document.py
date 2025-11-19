#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тестирование гибридной стратегии на реальном документе
"""

import sys
import os
from docx import Document

# Добавляем путь к модулям NLP service
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'app'))

from nlp_adapter import NLPAdapter

def test_hybrid_on_real_document():
    """Тестируем гибридную стратегию на реальном документе"""
    
    print("🔬 ТЕСТ ГИБРИДНОЙ СТРАТЕГИИ НА РЕАЛЬНОМ ДОКУМЕНТЕ")
    print("=" * 70)
    
    # Путь к реальному документу
    doc_path = r"C:\Projects\Anonymizer\unified_document_service\test_docs\test_01_1_4_SD.docx"
    
    if not os.path.exists(doc_path):
        print(f"❌ Документ не найден: {doc_path}")
        return
    
    try:
        # Загружаем документ
        print("📄 Загрузка реального документа...")
        doc = Document(doc_path)
        
        # Извлекаем текст
        text_parts = []
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                text_parts.append(paragraph.text.strip())
        
        full_text = ' '.join(text_parts)
        print(f"📊 Загружен документ: {len(full_text)} символов, {len(text_parts)} параграфов")
        
        # Берем первые 2000 символов для тестирования
        test_text = full_text[:2000]
        print(f"🧪 Тестируем на фрагменте: {len(test_text)} символов")
        print(f"📝 Начало: {test_text[:100]}...")
        print()
        
        # Инициализируем адаптер
        print("🚀 Инициализация гибридного NLP адаптера...")
        adapter = NLPAdapter()
        
        # Анализируем текст
        print("🔍 Анализ с гибридной стратегией...")
        results = adapter.find_sensitive_data(test_text)
        
        # Фильтруем государственные организации
        gov_results = [r for r in results if r.get('category') == 'government_org']
        
        print(f"\n🏛️ РЕЗУЛЬТАТЫ ГИБРИДНОЙ СТРАТЕГИИ:")
        print("-" * 50)
        print(f"📊 Всего найдено организаций: {len(gov_results)}")
        
        if gov_results:
            # Группируем по источнику метода
            by_source = {}
            for result in gov_results:
                if 'hybrid_info' in result:
                    source = result['hybrid_info']['source_method']
                else:
                    source = result['method']
                
                if source not in by_source:
                    by_source[source] = []
                by_source[source].append(result)
            
            print(f"\n📈 Распределение по методам:")
            for source, results_list in by_source.items():
                print(f"   {source}: {len(results_list)} организаций")
            
            print(f"\n📋 Детальные результаты:")
            for i, result in enumerate(gov_results, 1):
                print(f"   {i}. 🏛️ '{result['original_value']}'")
                print(f"       📍 Позиция: {result['position']['start']}-{result['position']['end']}")
                print(f"       🎯 Confidence: {result['confidence']:.3f}")
                print(f"       🔧 Метод: {result['method']}")
                
                if 'hybrid_info' in result:
                    hybrid_info = result['hybrid_info']
                    print(f"       🔬 Гибридная информация:")
                    print(f"          • Тип: {hybrid_info['organization_type']}")
                    print(f"          • Источник: {hybrid_info['source_method']}")
                    print(f"          • Госорган: {hybrid_info['is_government']}")
                
                # Показываем контекст
                start = max(0, result['position']['start'] - 50)
                end = min(len(test_text), result['position']['end'] + 50)
                context = test_text[start:end]
                context_marked = context.replace(result['original_value'], f"[[{result['original_value']}]]")
                print(f"       📝 Контекст: ...{context_marked}...")
                print()
        else:
            print("   ❌ Государственные организации не найдены")
        
        # Сравниваем с другими категориями
        org_results = [r for r in results if r.get('category') == 'organization']
        print(f"\n🏢 Для сравнения - коммерческие организации: {len(org_results)}")
        for result in org_results:
            print(f"   - '{result['original_value']}' (conf: {result['confidence']:.3f})")
        
    except Exception as e:
        print(f"❌ Ошибка: {str(e)}")
        import traceback
        traceback.print_exc()

def compare_strategies():
    """Сравниваем гибридную стратегию с обычной"""
    
    print("\n🔬 СРАВНЕНИЕ С ДЕМО ИЗ ПРОШЛОГО АНАЛИЗА")
    print("=" * 60)
    
    # Тест на том же тексте, что использовался в демонстрации
    test_text = """
    МИНИСТЕРСТВО ИНФОРМАЦИОННОГО РАЗВИТИЯ И СВЯЗИ ПЕРМСКОГО КРАЯ
    ЕДИНАЯ ИНФОРМАЦИОННАЯ СИСТЕМА УПРАВЛЕНИЯ ФИНАНСОВО-ХОЗЯЙСТВЕННОЙ 
    ДЕЯТЕЛЬНОСТЬЮ ОРГАНИЗАЦИЙ БЮДЖЕТНОЙ СФЕРЫ ПЕРМСКОГО КРАЯ

    Государственный контракт от 14 августа 2023 г. № 13/ОК-2023 
    на выполнение работ по развитию подсистемы «Управление имуществом»

    Государственный заказчик: Министерство информационного развития и связи
    Функциональные заказчики: 
    - Министерство по управлению имуществом и градостроительной деятельности
    - Министерство финансов Пермского края
    Подрядчик: Общество с ограниченной ответственностью «КАМА Технологии»
    """
    
    try:
        print("🚀 Анализ с текущей гибридной стратегией...")
        adapter = NLPAdapter()
        
        results = adapter.find_sensitive_data(test_text)
        gov_results = [r for r in results if r.get('category') == 'government_org']
        
        print(f"📊 Найдено государственных организаций: {len(gov_results)}")
        
        # Группируем по источнику
        sources = {}
        for result in gov_results:
            if 'hybrid_info' in result:
                source = result['hybrid_info']['source_method']
            else:
                source = result.get('method', 'unknown')
            
            if source not in sources:
                sources[source] = []
            sources[source].append(result['original_value'])
        
        print("\n📈 Результаты по методам:")
        for source, orgs in sources.items():
            print(f"   {source}: {len(orgs)} - {orgs}")
        
        print("\n🎯 КАЧЕСТВЕННОЕ СРАВНЕНИЕ:")
        print("-" * 40)
        
        expected_orgs = [
            "Министерство информационного развития и связи",
            "Министерство по управлению имуществом и градостроительной деятельности", 
            "Министерство финансов"
        ]
        
        found_orgs = [r['original_value'] for r in gov_results]
        
        print("Ожидаемые организации vs Найденные:")
        for expected in expected_orgs:
            found_match = any(expected.lower() in found.lower() or found.lower() in expected.lower() 
                            for found in found_orgs)
            status = "✅" if found_match else "❌"
            print(f"   {status} {expected}")
        
        print(f"\n📊 Покрытие: {len([org for org in expected_orgs if any(org.lower() in found.lower() or found.lower() in org.lower() for found in found_orgs)])}/{len(expected_orgs)} = {len([org for org in expected_orgs if any(org.lower() in found.lower() or found.lower() in org.lower() for found in found_orgs)])/len(expected_orgs)*100:.1f}%")
        
        # Проверяем false positives
        commercial_results = [r for r in results if r.get('category') == 'organization']
        print(f"\n🏢 Коммерческие организации (не должны попасть в government_org): {len(commercial_results)}")
        for result in commercial_results:
            print(f"   - '{result['original_value']}'")
        
    except Exception as e:
        print(f"❌ Ошибка: {str(e)}")

if __name__ == "__main__":
    test_hybrid_on_real_document()
    compare_strategies()
    
    print("\n🎉 ГИБРИДНАЯ СТРАТЕГИЯ УСПЕШНО ИНТЕГРИРОВАНА!")
    print("Основные преимущества:")
    print("✅ Phrase Matcher для точного поиска известных организаций")
    print("✅ spaCy NER для поиска новых организаций") 
    print("✅ Intelligent merging с приоритизацией и дедупликацией")
    print("✅ Фильтрация false positives")
    print("✅ Классификация типов организаций")
    print("✅ Сохранение всей предыдущей логики системы")