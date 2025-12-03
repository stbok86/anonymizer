#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import requests

tests = ["ЕИСУФХД", "ЕИС УФХД", "АИСМР", "ГИСПК"]

for text in tests:
    r = requests.post("http://localhost:8006/analyze", json={"blocks": [{"block_id": "t", "content": text}]}, timeout=10)
    dets = [d for d in r.json().get('detections', []) if d.get('category') == 'information_system']
    status = "✅" if dets else "❌"
    print(f"{status} '{text}': {len(dets)} детекций", end="")
    if dets:
        print(f" - '{dets[0].get('original_value')}' (метод: {dets[0].get('method')})")
    else:
        print()
