"""
Отладка включения lemmatizer
"""
from nlp_config import NLPConfig

config = NLPConfig()

print("="*80)
print("ОТЛАДКА КОНФИГУРАЦИИ")
print("="*80)

available = config.get_available_categories()
print(f"\nДоступные категории: {available}")

if 'person_name' in available:
    methods = config.get_enabled_methods_for_category('person_name')
    print(f"person_name enabled_methods: {methods}")
    print(f"'morphological' in methods: {'morphological' in methods}")
    
print("\n" + "="*80)
print("ВЫВОД:")
print("="*80)
print("""
ПРОБЛЕМА: person_name есть в detection_methods конфига, поэтому
get_available_categories() всегда возвращает его, и lemmatizer
всегда включается.

РЕШЕНИЕ: Нужно либо:
1. Убрать person_name из nlp_config.json (если он не используется)
2. ИЛИ добавить флаг enabled: false для person_name
3. ИЛИ проверять не available_categories, а фактическое использование
""")
