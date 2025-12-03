# -*- coding: utf-8 -*-
import sys, os
sys.path.append(os.getcwd())

from nlp_adapter import NLPAdapter

nlp = NLPAdapter()

# Реальные тексты из документа test_01_1_4_SD2.docx
test_cases = [
    ('МИНИСТЕРСТВО ИНФОРМАЦИОННОГО РАЗВИТИЯ И СВЯЗИ', 'ministry uppercase'),
    ('Министерство информационного развития и связи', 'ministry titlecase'),
    ('ГБУ ПК «Центр информационного развития Пермского края»', 'GBU full'),
    ('ООО «КАМА Технологии»', 'OOO quoted'),
    ('Начальник управления цифровых технологий Министерства информационного развития и связи Пермского края', 'full context'),
    ('ГБУ\xa0ПК «Центр информационного', 'GBU with nbsp partial'),
]

for text, description in test_cases:
    print(f"\n{'='*60}")
    print(f"TEST: {description}")
    print(f"Text: {repr(text)}")
    detections = nlp.find_sensitive_data(text)
    print(f"RESULT: Found {len(detections)} detections")
    if detections:
        for d in detections:
            print(f"  - {d['category']}: '{d['original_value']}' (conf={d['confidence']:.2f}, method={d['method']})")
    else:
        print("  NONE FOUND")
