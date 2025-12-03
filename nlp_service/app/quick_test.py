# -*- coding: utf-8 -*-
import sys, os
sys.path.append(os.getcwd())

from nlp_adapter import NLPAdapter

nlp = NLPAdapter()

# Реальные тексты из документа
test_cases = [
    ('А. С. Щукина', 'normal space'),
    ('К.\xa0С. Мясников', 'nbsp'),
    ('В. В. Евтушенко', 'normal space'),
    ('\n______________________ А. С. Щукина', 'with signature'),
    ('\n______________________ К.\xa0С. Мясников', 'with signature nbsp'),
    ('\n____________________ В. В. Евтушенко', 'with signature normal')
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