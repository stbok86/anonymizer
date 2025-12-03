import requests

# Test 1: All caps
r1 = requests.post('http://localhost:8006/analyze', json={'blocks': [{'block_id': 't', 'content': 'МИНИСТЕРСТВО ИНФОРМАЦИОННОГО РАЗВИТИЯ И СВЯЗИ'}]})
print("Test 1 (ALL CAPS):", len(r1.json()['detections']), "detections")

# Test 2: Normal case  
r2 = requests.post('http://localhost:8006/analyze', json={'blocks': [{'block_id': 't', 'content': 'Министерство информационного развития и связи'}]})
print("Test 2 (Normal):", len(r2.json()['detections']), "detections")
for d in r2.json()['detections']:
    print(f"   - {d.get('category')}: '{d.get('text')}' (method: {d.get('method')})")

# Test 3: From document
r3 = requests.post('http://localhost:8006/analyze', json={'blocks': [{'block_id': 't', 'content': 'МИНИСТЕРСТВО ИНФОРМАЦИОННОГО РАЗВИТИЯ И СВЯЗИ\nПЕРМСКОГО КРАЯ'}]})
print("\nTest 3 (From doc):", len(r3.json()['detections']), "detections")
for d in r3.json()['detections']:
    print(f"   - {d.get('category')}: '{d.get('text')}' (method: {d.get('method')})")
