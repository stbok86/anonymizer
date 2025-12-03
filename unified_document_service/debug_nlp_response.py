import requests
from docx import Document

# Читаем документ
doc = Document('test_docs/test_01_1_4_SD33.docx')
full_text = '\n'.join(p.text for p in doc.paragraphs)

print("="*80)
print("ОТПРАВЛЯЕМ В NLP SERVICE")
print("="*80)
print(f"Длина текста: {len(full_text)} символов")
print(f"Первые 500 символов:\n{full_text[:500]}")

# Отправляем в NLP Service ПРАВИЛЬНО через /analyze
payload = {
    "blocks": [
        {
            "content": full_text,
            "block_id": "doc_block_1",
            "block_type": "text"
        }
    ],
    "options": {}
}

response = requests.post(
    "http://localhost:8006/analyze",
    json=payload,
    timeout=30
)

print("\n" + "="*80)
print("ОТВЕТ ОТ NLP SERVICE")
print("="*80)

if response.status_code == 200:
    result = response.json()
    detections = result.get('detections', [])
    print(f"Всего детекций: {len(detections)}")
    
    # Ищем все детекции организаций
    org_detections = [d for d in detections if d.get('category') == 'organization']
    print(f"\nДетекций организаций: {len(org_detections)}")
    
    for i, det in enumerate(org_detections, 1):
        print(f"\n{i}. Организация:")
        print(f"   original_value: '{det.get('original_value', 'N/A')}'")
        print(f"   position: {det.get('position', {})}")
        print(f"   confidence: {det.get('confidence', 0)}")
        print(f"   method: {det.get('method', 'N/A')}")
else:
    print(f"ERROR: Status {response.status_code}")
    print(f"Response: {response.text}")
