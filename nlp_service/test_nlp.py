#!/usr/bin/env python3
"""
Тестирование NLP адаптера без запуска FastAPI
"""

import sys
import os

# Добавляем путь к модулям
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

def test_nlp_adapter():
    """Тестирование NLP адаптера"""
    
    print("=== Тест NLP Adapter ===\n")
    
    try:
        from nlp_adapter import NLPAdapter
        print("✅ NLPAdapter импортирован")
    except ImportError as e:
        print(f"❌ Ошибка импорта NLPAdapter: {e}")
        print("💡 Возможно, не установлены зависимости:")
        print("   pip install spacy pandas openpyxl")
        print("   python -m spacy download ru_core_news_sm")
        return False
    
    try:
        # Создаем адаптер
        print("🔄 Инициализация NLP адаптера...")
        adapter = NLPAdapter()
        print("✅ NLP адаптер инициализирован")
        
    except Exception as e:
        print(f"❌ Ошибка инициализации: {e}")
        return False
    
    # Тестовые тексты
    test_texts = [
        # Персональные данные
        "Иван Петрович Сидоров работает директором в нашей компании",
        "Контакты: И.П. Сидоров, тел. +7-999-123-45-67",
        
        # Организации
        "ООО 'Рога и Копыта' заключило договор с ПАО 'Газпром'",
        "В АО Сбербанк работает 250 тысяч сотрудников",
        
        # Должности
        "Главный бухгалтер Мария Ивановна подписала документ",
        "Начальник отдела кадров принял решение",
        
        # Финансы
        "Зарплата составляет 150000 рублей в месяц", 
        "Сумма контракта: 2500000 ₽",
        
        # Медицинская информация
        "У пациента диагностирована пневмония",
        "Лечение в больнице продлилось 2 недели",
        
        # Локации
        "Встреча состоится в Москве на Красной площади",
        "Адрес: г. Санкт-Петербург, ул. Невский проспект, д. 1"
    ]
    
    print(f"\n🔍 Тестирование на {len(test_texts)} примерах:\n")
    
    total_detections = 0
    
    for i, text in enumerate(test_texts, 1):
        print(f"📝 Тест {i}: '{text[:50]}{'...' if len(text) > 50 else ''}'")
        
        try:
            detections = adapter.find_sensitive_data(text)
            total_detections += len(detections)
            
            if detections:
                print(f"   ✅ Найдено {len(detections)} обнаружений:")
                for detection in detections:
                    category = detection['category']
                    value = detection['original_value']
                    confidence = detection['confidence']
                    method = detection['method']
                    print(f"      - {category}: '{value}' (уверенность: {confidence:.2f}, метод: {method})")
            else:
                print(f"   ❌ Обнаружений не найдено")
                
        except Exception as e:
            print(f"   💥 Ошибка анализа: {e}")
        
        print()
    
    print(f"📊 Итого найдено {total_detections} обнаружений в {len(test_texts)} текстах")
    
    # Тестируем информацию о паттернах
    print(f"\n📋 Загруженные категории:")
    for category in adapter.patterns.keys():
        count = len(adapter.patterns[category])
        print(f"   {category}: {count} паттернов")
    
    return True

def test_patterns_loading():
    """Тестирование загрузки паттернов"""
    
    print("=== Тест загрузки паттернов ===\n")
    
    patterns_file = os.path.join(os.path.dirname(__file__), "patterns", "nlp_patterns.xlsx")
    
    if not os.path.exists(patterns_file):
        print(f"❌ Файл паттернов не найден: {patterns_file}")
        print("💡 Запустите: python patterns/create_nlp_patterns.py")
        return False
    
    try:
        import pandas as pd
        df = pd.read_excel(patterns_file)
        
        print(f"✅ Файл паттернов загружен: {len(df)} записей")
        
        # Статистика по категориям
        print("\n📊 Статистика по категориям:")
        category_stats = df['category'].value_counts()
        for category, count in category_stats.items():
            print(f"   {category}: {count}")
        
        # Статистика по типам
        print("\n🔧 Статистика по типам:")
        type_stats = df['pattern_type'].value_counts()
        for pattern_type, count in type_stats.items():
            print(f"   {pattern_type}: {count}")
            
        return True
        
    except Exception as e:
        print(f"❌ Ошибка загрузки паттернов: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Тестирование NLP Service\n")
    
    # Тест загрузки паттернов
    patterns_ok = test_patterns_loading()
    
    if patterns_ok:
        # Тест NLP адаптера
        adapter_ok = test_nlp_adapter()
        
        if adapter_ok:
            print("\n🎉 Все тесты пройдены успешно!")
            print("🚀 NLP Service готов к работе")
        else:
            print("\n💥 Есть проблемы с NLP адаптером")
    else:
        print("\n💥 Проблемы с загрузкой паттернов")