import sys
sys.path.insert(0, 'app')

from full_anonymizer import FullAnonymizer

# Создаём anonymizer
anonymizer = FullAnonymizer(
    nlp_service_url="http://localhost:8006",
    rule_engine_url="http://localhost:8007"
)

# Анонимизируем документ
result = anonymizer.anonymize_document(
    file_path="test_docs/test_01_1_4_SD33.docx"
)

print("\n" + "="*80)
print("РЕЗУЛЬТАТ АНОНИМИЗАЦИИ")
print("="*80)
print(f"Успех: {result.get('success', False)}")
print(f"Всего замен: {result.get('total_replacements', 0)}")
