"""
Проверка детерминизма UUID для одинаковых значений
"""
import pandas as pd

# Читаем Excel таблицу
excel_path = "test_replacements.xlsx"
df = pd.read_excel(excel_path)

print("=" * 80)
print("🔍 ПРОВЕРКА ДЕТЕРМИНИЗМА UUID")
print("=" * 80)
print()

# Группируем по оригинальному значению
grouped = df.groupby('Исходные данные')

print("📊 Анализ повторяющихся значений:")
print()

duplicates_found = False
all_consistent = True

for original, group in grouped:
    if len(group) > 1:
        duplicates_found = True
        uuids = group['Замена (идентификатор)'].unique()
        
        if len(uuids) == 1:
            status = "✅ UUID одинаковый"
        else:
            status = f"❌ РАЗНЫЕ UUID: {len(uuids)} вариантов!"
            all_consistent = False
        
        print(f"{status}")
        print(f"   Значение: '{original}'")
        print(f"   Встречается: {len(group)} раз")
        print(f"   UUID: {list(uuids)}")
        print()

if not duplicates_found:
    print("ℹ️ Нет повторяющихся значений")
else:
    print("=" * 80)
    if all_consistent:
        print("✅ ТЕСТ ПРОЙДЕН: Все одинаковые значения имеют одинаковые UUID")
    else:
        print("❌ ТЕСТ НЕ ПРОЙДЕН: Найдены одинаковые значения с разными UUID")
    print("=" * 80)
