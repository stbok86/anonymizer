#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Прямой тест NLP Service для информационных систем
"""

import requests
import json

def test_nlp_is():
    """Тестируем детекцию информационных систем"""
    
    # Тестовые тексты с информационными системами
    test_blocks = [
        {
            "block_id": "test_1",
            "content": "ЕДИНАЯ ИНФОРМАЦИОННАЯ СИСТЕМА УПРАВЛЕНИЯ ФИНАНСОВО-ХОЗЯЙСТВЕННОЙ ДЕЯТЕЛЬНОСТЬЮ ОРГАНИЗАЦИЙ БЮДЖЕТНОЙ СФЕРЫ ПЕРМСКОГО КРАЯ"
        },
        {
            "block_id": "test_2", 
            "content": "Единой информационной системы управления финансово-хозяйственной деятельностью организаций бюджетной сферы Пермского края"
        },
        {
            "block_id": "test_3",
            "content": "подсистемы «Управление имуществом»"
        },
        {
            "block_id": "test_4",
            "content": "развитие подсистемы «Управление имуществом» (2 очередь)"
        },
        {
            "block_id": "test_5",
            "content": "ЕИС УФХД"
        }
    ]
    
    print("=" * 100)
    print("ПРЯМОЙ ТЕСТ NLP SERVICE - ИНФОРМАЦИОННЫЕ СИСТЕМЫ")
    print("=" * 100)
    
    url = "http://localhost:8006/analyze"
    
    for block in test_blocks:
        print(f"\n{'='*100}")
        print(f"Тест блока: {block['block_id']}")
        print(f"Содержимое: '{block['content']}'")
        print(f"{'='*100}")
        
        try:
            response = requests.post(
                url,
                json={"blocks": [block]},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                detections = result.get('detections', [])
                
                print(f"\nСтатус: {response.status_code}")
                print(f"Всего детекций: {len(detections)}")
                
                # Фильтруем информационные системы
                is_detections = [d for d in detections if d.get('category') == 'information_system']
                
                print(f"Детекций information_system: {len(is_detections)}")
                
                if is_detections:
                    for i, det in enumerate(is_detections, 1):
                        print(f"\n  Детекция {i}:")
                        print(f"    - Текст: '{det.get('original_value', '')}'")
                        print(f"    - Уверенность: {det.get('confidence', 0):.2f}")
                        print(f"    - Метод: {det.get('method', 'N/A')}")
                        print(f"    - Позиция: {det.get('position', {}).get('start', 0)}-{det.get('position', {}).get('end', 0)}")
                else:
                    print("\n  Информационные системы НЕ НАЙДЕНЫ!")
                
                # Показываем все детекции для справки
                if detections and not is_detections:
                    print(f"\n  Найдены другие типы (первые 5):")
                    for det in detections[:5]:
                        print(f"    - {det.get('category')}: '{det.get('original_value', '')[:50]}'")
                
            else:
                print(f"\nОшибка: {response.status_code}")
                print(f"   Ответ: {response.text[:500]}")
                
        except Exception as e:
            print(f"\nИсключение: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_nlp_is()
