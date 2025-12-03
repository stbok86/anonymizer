from rule_adapter import RuleEngineAdapter

# Создаем адаптер
adapter = RuleEngineAdapter(patterns_file='../patterns/sensitive_patterns.xlsx')

# Тестовый текст с датами
test_text = """
Государственный контракт от 14 августа 2023 г. № 13/ОК-2023
Дата рождения: 15.08.1990
Договор № 123 от 01.12.2024
Срок действия до 31/12/2025
"""

print("🧪 Тестирование после деактивации паттернов 'date'\n")

# Ищем совпадения
matches = adapter.find_sensitive_data(test_text)

# Проверяем наличие date
date_matches = [m for m in matches if m.get('category') == 'date']

print(f"Всего найдено совпадений: {len(matches)}")
print(f"Совпадений категории 'date': {len(date_matches)}")
print()

if date_matches:
    print("❌ ОШИБКА: Паттерны date все еще активны:")
    for m in date_matches:
        print(f"  - '{m['original_value']}'")
else:
    print("✅ SUCCESS: Паттерны date деактивированы")
    
print("\nДругие найденные категории:")
for category in set(m.get('category', 'unknown') for m in matches):
    count = len([m for m in matches if m.get('category') == category])
    print(f"  - {category}: {count} совпадений")
