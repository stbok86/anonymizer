#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест инициализации стратегии информационных систем
"""

import sys
import os

sys.path.insert(0, r'C:\Projects\Anonymizer\nlp_service\app')

from nlp_adapter import NLPAdapter

def test_is_strategy():
    """Проверяем инициализацию стратегии"""
    
    print("=" * 100)
    print("ТЕСТ ИНИЦИАЛИЗАЦИИ СТРАТЕГИИ ИНФОРМАЦИОННЫХ СИСТЕМ")
    print("=" * 100)
    
    try:
        print("\n1️⃣ Создаем NLPAdapter...")
        adapter = NLPAdapter()
        print(f"   ✅ NLPAdapter создан")
        
        print(f"\n2️⃣ Проверяем стратегию ИС...")
        print(f"   - _is_strategy существует: {hasattr(adapter, '_is_strategy')}")
        print(f"   - _is_strategy is None: {adapter._is_strategy is None}")
        
        if adapter._is_strategy is not None:
            print(f"   ✅ Стратегия инициализирована")
            print(f"   - Тип: {type(adapter._is_strategy)}")
            print(f"   - is_initialized: {getattr(adapter._is_strategy, 'is_initialized', 'N/A')}")
        else:
            print(f"   ❌ Стратегия НЕ инициализирована!")
            
        print(f"\n3️⃣ Проверяем доступные категории...")
        categories = adapter.config.get_available_categories()
        print(f"   Всего категорий: {len(categories)}")
        print(f"   information_system в списке: {'information_system' in categories}")
        
        if 'information_system' in categories:
            print(f"\n4️⃣ Проверяем настройки information_system...")
            enabled_methods = adapter.config.get_enabled_methods_for_category('information_system')
            print(f"   - Включенные методы: {enabled_methods}")
            
            strategy_name = adapter.config.get_detection_strategy_name('information_system')
            print(f"   - Название стратегии: {strategy_name}")
            
        print(f"\n5️⃣ Тестируем детекцию...")
        test_text = "ЕДИНАЯ ИНФОРМАЦИОННАЯ СИСТЕМА УПРАВЛЕНИЯ"
        
        print(f"   Тестовый текст: '{test_text}'")
        detections = adapter.find_sensitive_data(test_text)
        
        print(f"\n   📊 Результаты:")
        print(f"   - Всего детекций: {len(detections)}")
        
        is_detections = [d for d in detections if d.get('category') == 'information_system']
        print(f"   - Детекций ИС: {len(is_detections)}")
        
        if is_detections:
            for det in is_detections:
                print(f"     ✅ {det}")
        else:
            print(f"     ❌ Информационные системы НЕ НАЙДЕНЫ")
            
            # Показываем что найдено
            if detections:
                print(f"\n   Найдены другие категории:")
                for det in detections[:5]:
                    print(f"     - {det.get('category')}: '{det.get('original_value', '')}'")
        
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_is_strategy()
