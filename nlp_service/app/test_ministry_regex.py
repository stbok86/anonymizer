import re

text = "Министерство информационного развития и связи Пермского края"

patterns = [
    r"\b(Министерство|министерство|Департамент|департамент|Управление|управление|Агентство|агентство|Служба|служба)\s+[а-яёА-ЯЁ\s]+",
    r"\b(Министерство|министерство)\s+[а-яёА-ЯЁ\s]+",
    r"Министерство\s+[а-яёА-ЯЁ\s]+",
    r"Министерство\s+\w+",
    r"Министерство",
]

print(f"Текст: '{text}'")
print(f"Длина: {len(text)}\n")

for i, pattern in enumerate(patterns, 1):
    print(f"Паттерн {i}: {pattern}")
    matches = list(re.finditer(pattern, text))
    if matches:
        for match in matches:
            print(f"  ✅ Найдено: '{match.group()}' на позициях {match.span()}")
    else:
        print(f"  ❌ Ничего не найдено")
    print()

# Попробуем более точный паттерн
better_pattern = r"\b(Министерство|Департамент|Управление|Агентство|Служба)\s+[а-яёА-ЯЁ]+(?:\s+[а-яёА-ЯЁ]+){1,6}"
print(f"Улучшенный паттерн: {better_pattern}")
matches = list(re.finditer(better_pattern, text))
if matches:
    for match in matches:
        print(f"  ✅ Найдено: '{match.group()}' на позициях {match.span()}")
else:
    print(f"  ❌ Ничего не найдено")
