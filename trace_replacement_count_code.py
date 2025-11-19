#!/usr/bin/env python3
"""
ТРАССИРОВКА КОДА: "Выполнено замен: 25"  
=====================================

Показывает точные места в коде, где происходит подсчет и отображение значения.
"""

print("""
🔍 ТРАССИРОВКА КОДА: "Выполнено замен: 25"
═════════════════════════════════════════

📁 1. ПОДСЧЕТ ЗАМЕН В BACKEND
─────────────────────────────

📄 unified_document_service/app/formatter_applier.py
└── FormatterApplier.apply_replacements_to_document() [строки 40-100]
    ├── Инициализирует: stats = {'total_replacements': 0, ...}
    ├── Группирует замены по блокам
    └── Для каждого блока:
        └── FormatterApplier._apply_replacements_to_block() [строки 115-150]
            ├── Инициализирует: block_stats = {'replacements_made': 0, ...}
            └── Для каждой замены в блоке:
                └── FormatterApplier._apply_single_replacement() [строки 155-250]
                    ├── Если замена успешна: return True
                    └── block_stats['replacements_made'] += 1  ← СЧЕТЧИК +1
            └── stats['total_replacements'] += block_stats['replacements_made']

📄 unified_document_service/app/full_anonymizer.py  
└── FullAnonymizer.anonymize_selected_items() [строки 252-340]
    ├── replacement_stats = self.formatter.apply_replacements_to_document(...)
    └── return {'replacements_applied': replacement_stats.get('total_replacements', 0)}

📄 unified_document_service/app/main.py
└── POST /anonymize_selected [строки 407-450]
    ├── result = anonymizer.anonymize_selected_items(...)
    └── return result  # содержит 'replacements_applied'

📁 2. ПЕРЕДАЧА В FRONTEND
─────────────────────────

📄 frontend/streamlit_app.py
└── anonymize_document_full_api() [строки 630-680]
    ├── response = requests.post("/anonymize_selected", ...)
    ├── result = response.json()
    └── st.session_state.anonymization_stats = {
        'replacement_stats': result.get('statistics', {}),  ← СЮДА
        'replacements_applied': result.get('replacements_applied', 0)
    }

📁 3. ОТОБРАЖЕНИЕ НА ШАГЕ 3  
─────────────────────────────

📄 frontend/streamlit_app.py
└── step3_download_results() [строки 383-390]
    ├── stats = st.session_state.anonymization_stats
    ├── replacement_stats = stats.get('replacement_stats', {})
    ├── replacements_count = replacement_stats.get('total_replacements', 0)
    └── st.info(f"✅ Выполнено замен: {replacements_count}")  ← ОТОБРАЖАЕТСЯ!

🎯 КЛЮЧЕВЫЕ МОМЕНТЫ:
─────────────────────

1️⃣ ИСТОЧНИК ЗНАЧЕНИЯ:
FormatterApplier._apply_single_replacement() возвращает True/False
Каждый True добавляет +1 к счетчику

2️⃣ ПУТЬ ДАННЫХ:
FormatterApplier → FullAnonymizer → API Response → Frontend → UI

3️⃣ ОТОБРАЖЕНИЕ:
stats.replacement_stats.total_replacements → "✅ Выполнено замен: X"

📊 ПРИМЕР ВЫПОЛНЕНИЯ:
───────────────────

Пользователь выбрал 25 элементов:
• element_1 → _apply_single_replacement() → True → counter += 1
• element_2 → _apply_single_replacement() → True → counter += 1  
• ...
• element_25 → _apply_single_replacement() → True → counter += 1

ИТОГО: total_replacements = 25
ОТОБРАЖЕНИЕ: "✅ Выполнено замен: 25"

🚨 ВОЗМОЖНЫЕ ОШИБКИ:
──────────────────

Если _apply_single_replacement() вернет False (ошибка замены):
• element_10 → _apply_single_replacement() → False → counter += 0

Тогда: total_replacements = 24 (вместо 25)
ОТОБРАЖЕНИЕ: "✅ Выполнено замен: 24"

💡 ВЫВОД:
───────
Значение "Выполнено замен: 25" = количество успешных вызовов 
FormatterApplier._apply_single_replacement() для выбранных элементов.
""")

if __name__ == "__main__":
    pass