#!/usr/bin/env python3
"""
Анализ паттернов в nlp_patterns.xlsx
"""
import pandas as pd
import os

def analyze_patterns():
    # Путь к Excel файлу
    excel_path = os.path.join(os.path.dirname(__file__), "nlp_patterns.xlsx")
    
    if not os.path.exists(excel_path):
        print(f"❌ Файл не найден: {excel_path}")
        return
    
    # Загружаем Excel
    try:
        df = pd.read_excel(excel_path)
        print(f"✅ Загружен файл: {excel_path}")
        print(f"📊 Всего записей: {len(df)}")
        print()
        
        # Показываем структуру
        print("📋 Колонки:")
        for col in df.columns:
            print(f"   - {col}")
        print()
        
        # Показываем все категории
        print("🏷️ Категории в файле:")
        categories = df['category'].unique()
        for cat in sorted(categories):
            count = len(df[df['category'] == cat])
            print(f"   - {cat}: {count} паттернов")
        print()
        
        # Проверяем наличие government_org
        if 'government_org' in categories:
            print("✅ Категория 'government_org' найдена!")
            gov_patterns = df[df['category'] == 'government_org']
            print(f"   Количество паттернов: {len(gov_patterns)}")
            for idx, row in gov_patterns.iterrows():
                print(f"   - {row['description']}: {row['pattern']}")
        else:
            print("❌ Категория 'government_org' НЕ найдена!")
            print("   Возможно, она должна быть добавлена в паттерны.")
        
        # Ищем организационные паттерны
        print()
        print("🔍 Организационные паттерны:")
        org_related = df[df['category'].str.contains('org|department', case=False, na=False)]
        for idx, row in org_related.iterrows():
            print(f"   - {row['category']}: {row['description']}")
    
    except Exception as e:
        print(f"❌ Ошибка при анализе: {e}")

if __name__ == "__main__":
    analyze_patterns()