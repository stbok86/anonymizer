"""
Прямая проверка NLP Service
"""
import requests

text = """МИНИСТЕРСТВО ИНФОРМАЦИОННОГО РАЗВИТИЯ И СВЯЗИ
ПЕРМСКОГО КРАЯ
ЕДИНАЯ ИНФОРМАЦИОННАЯ СИСТЕМА"""

blocks = [{"block_id": "test", "content": text}]

response = requests.post("http://localhost:8006/analyze", json={"blocks": blocks})

if response.status_code == 200:
    result = response.json()
    
    print("=" * 80)
    print("🤖 NLP SERVICE RESPONSE")
    print("=" * 80)
    print()
    
    for detection in result.get('detections', []):
        print(f"Категория: {detection.get('category')}")
        print(f"Текст: '{detection.get('text')}'")
        print(f"Метод: {detection.get('method')}")
        print(f"Confidence: {detection.get('confidence')}")
        print()
else:
    print(f"Ошибка: {response.status_code}")
