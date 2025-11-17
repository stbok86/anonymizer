import pandas as pd
import os

# Загружаем исходный файл
file_path = "sensitive_patterns.xlsx"
df = pd.read_excel(file_path)

print(f"🔍 Исходный файл: {len(df)} правил")
print(f"📋 Категории: {list(df['category'].unique())}")

# Удаляем дублирующиеся с NLP Service правила
duplicates_to_remove = ['name', 'address']  # Эти категории есть в NLP Service

# Фильтруем данные
df_clean = df[~df['category'].isin(duplicates_to_remove)]

print(f"🧹 После удаления дубликатов: {len(df_clean)} правил")
print(f"📋 Оставшиеся категории: {list(df_clean['category'].unique())}")
print(f"❌ Удалены категории: {duplicates_to_remove}")

# Сохраняем очищенный файл
output_path = "sensitive_patterns_no_duplicates.xlsx"
df_clean.to_excel(output_path, index=False)

print(f"✅ Создан файл без дубликатов: {output_path}")