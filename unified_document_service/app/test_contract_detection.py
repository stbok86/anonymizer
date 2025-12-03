import requests
import json
from docx import Document

# Читаем реальный документ
doc = Document(r'C:\Projects\Anonymizer\unified_document_service\test_docs\test_01_1_4_SD33.docx')
text = '\n'.join([p.text for p in doc.paragraphs])

# Ищем все упоминания контракта в тексте
test_cases = [
    "Государственный контракт от 14 августа 2023 г. № 13/ОК-2023",
    "Контракту от 14 августа 2023 г. № 13/ОК-2023",
    "Контракта от 14 августа 2023 г. № 13/ОК-2023",
    "Государственного контракта от 14 августа 2023 г. № 13/ОК-2023",
    "договор № 123/ОК-2023 от 15.08.2023",
]

print("🧪 Тестирование обнаружения номеров контрактов/договоров\n")

for test_text in test_cases:
    response = requests.post(
        "http://localhost:8006/analyze",
        json={"blocks": [{"block_id": "t", "content": test_text}], "categories": ["contract_number"]}
    )
    
    if response.status_code == 200:
        result = response.json()
        detections = result.get("detections", [])
        contract_detections = [d for d in detections if d["category"] == "contract_number"]
        
        if contract_detections:
            print(f"✅ '{test_text}'")
            for d in contract_detections:
                text_val = d.get('text', d.get('value', 'N/A'))
                conf = d.get('confidence', 0)
                method = d.get('detection_method', 'N/A')
                print(f"   → найдено: '{text_val}' (confidence: {conf}, method: {method})")
        else:
            print(f"❌ '{test_text}' - НЕ обнаружено")
    else:
        print(f"❌ Ошибка API: {response.status_code}")
    print()

# Теперь проверим на реальном документе
print("\n📄 Проверка на реальном документе test_01_1_4_SD33.docx:")
response = requests.post(
    "http://localhost:8006/analyze",
    json={"blocks": [{"block_id": "doc", "content": text[:3000]}], "categories": ["contract_number"]}
)

if response.status_code == 200:
    result = response.json()
    contract_detections = [d for d in result.get("detections", []) if d["category"] == "contract_number"]
    print(f"Найдено {len(contract_detections)} упоминаний контракта:")
    for d in contract_detections:
        text_val = d.get('text', d.get('value', 'N/A'))
        conf = d.get('confidence', 0)
        method = d.get('detection_method', 'N/A')
        print(f"  - '{text_val}' (conf: {conf}, method: {method})")
else:
    print(f"❌ Ошибка API: {response.status_code}")
