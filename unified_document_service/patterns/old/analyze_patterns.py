import pandas as pd

df = pd.read_excel('sensitive_patterns.xlsx')
print('Все паттерны в Rule Engine:')

for cat in df.category.unique():
    patterns = df[df.category==cat]
    print(f'  {cat}: {len(patterns)} правил')
    for _, row in patterns.iterrows():
        print(f'    - {row.pattern[:80]}...')
    print()