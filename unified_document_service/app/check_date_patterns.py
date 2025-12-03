import pandas as pd

df = pd.read_excel(r'C:\Projects\Anonymizer\unified_document_service\patterns\sensitive_patterns.xlsx')

# Показываем все категории
print("Все категории в файле:")
print(df['category'].unique())
print()

# Ищем date паттерны
date_rows = df[df['category'] == 'date']

print(f"Количество паттернов 'date': {len(date_rows)}")
print()

if len(date_rows) > 0:
    print("Паттерны date:")
    for i, row in date_rows.iterrows():
        print(f"  Индекс {i}:")
        print(f"    pattern: {row['pattern']}")
        print(f"    confidence: {row['confidence']}")
        print(f"    description: {row.get('description', 'N/A')}")
        print()
