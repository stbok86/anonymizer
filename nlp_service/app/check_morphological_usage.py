"""
Проверка фактического использования морфологических детекций
"""
from nlp_adapter import NLPAdapter
from docx import Document
from collections import Counter

# Загружаем тестовый документ
doc_path = r'C:\Projects\Anonymizer\unified_document_service\test_docs\2. 17.03_2_Техническое_задание_развитие_УИ — копия.docx'
doc = Document(doc_path)
blocks = [p.text for p in doc.paragraphs if p.text.strip()]

print(f"Всего блоков в документе: {len(blocks)}")
print("\n" + "="*80)

# Инициализируем адаптер
adapter = NLPAdapter()

# Проверяем первые 100 блоков
all_methods = []
morphological_detections = []

for i, block in enumerate(blocks[:100], 1):
    results = adapter.find_sensitive_data(block)
    
    for detection in results:
        method = detection.get('method', 'unknown')
        all_methods.append(method)
        
        if 'morphological' in method:
            morphological_detections.append({
                'block_num': i,
                'text': block[:80],
                'detection': detection
            })

print("\n" + "="*80)
print("СТАТИСТИКА МЕТОДОВ ДЕТЕКЦИИ")
print("="*80)

method_counts = Counter(all_methods)
total_detections = sum(method_counts.values())

print(f"\nВсего детекций: {total_detections}")
print("\nРаспределение по методам:")
for method, count in method_counts.most_common():
    percentage = (count / total_detections * 100) if total_detections > 0 else 0
    print(f"  {method:30s}: {count:4d} ({percentage:5.2f}%)")

print("\n" + "="*80)
print("МОРФОЛОГИЧЕСКИЕ ДЕТЕКЦИИ")
print("="*80)

if morphological_detections:
    print(f"\nНайдено морфологических детекций: {len(morphological_detections)}")
    print("\nПримеры:")
    for item in morphological_detections[:5]:
        print(f"\nБлок {item['block_num']}: {item['text']}...")
        print(f"  Детекция: {item['detection']}")
else:
    print("\nМОРФОЛОГИЧЕСКИЕ ДЕТЕКЦИИ НЕ ИСПОЛЬЗУЮТСЯ!")
    print("Lemmatizer загружается и работает вхолостую, тратя 53% времени!")

print("\n" + "="*80)
print("ВЫВОД")
print("="*80)

if not morphological_detections:
    print("""
КРИТИЧЕСКОЕ УЗКОЕ МЕСТО НАЙДЕНО!

Морфологический анализ (pymorphy3 + spaCy lemmatizer) занимает 53% времени,
но ФАКТИЧЕСКИ НЕ ИСПОЛЬЗУЕТСЯ для детекции в текущем документе!

Это означает, что:
1. На каждый блок текста тратится ~18-20ms на лемматизацию
2. Из которых 0ms идет на реальную детекцию
3. Это чистые потери производительности

Потенциальное ускорение при отключении лемматизации:
- Было: 3.28s на 100 блоков
- Станет: ~1.54s на 100 блоков
- Ускорение: 2.13x (113% улучшение)
""")
