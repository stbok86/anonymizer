#!/usr/bin/env python3
"""
Тестирование обновленного BlockBuilder с поддержкой SDT элементов
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from docx import Document
from app.block_builder import BlockBuilder
import json

def test_updated_block_builder():
    """Тест обновленного BlockBuilder"""
    test_file = r"C:\Projects\Anonymizer\unified_document_service\test_docs\test_01_1_4.docx"
    
    print("=== ТЕСТ ОБНОВЛЕННОГО BLOCKBUILDER ===")
    
    if not os.path.exists(test_file):
        print(f"Файл не найден: {test_file}")
        return
    
    try:
        # Загружаем документ
        doc = Document(test_file)
        print(f"Документ загружен: {len(doc.sections)} секций")
        
        # Создаем BlockBuilder и извлекаем блоки
        builder = BlockBuilder()
        blocks = builder.build_blocks(doc)
        
        print(f"\nОбщее количество блоков: {len(blocks)}")
        
        # Анализируем типы блоков
        block_types = {}
        target_found = []
        
        for block in blocks:
            block_type = block['type']
            block_types[block_type] = block_types.get(block_type, 0) + 1
            
            # Ищем целевые данные
            text = block['text']
            if 'ЕИСУФХД' in text:
                target_found.append({
                    'block_id': block['block_id'],
                    'type': block_type,
                    'text': text
                })
        
        print(f"\nСтатистика по типам блоков:")
        for block_type, count in block_types.items():
            print(f"  {block_type}: {count}")
        
        print(f"\nНайдено блоков с 'ЕИСУФХД': {len(target_found)}")
        for item in target_found:
            print(f"  [{item['type']}] {item['block_id']}: {item['text'][:100]}...")
        
        # Показываем первые несколько блоков каждого типа
        print(f"\nПримеры блоков по типам:")
        shown_types = set()
        for block in blocks:
            block_type = block['type']
            if block_type not in shown_types:
                print(f"\n  === {block_type.upper()} ===")
                print(f"  ID: {block['block_id']}")
                print(f"  Текст: {block['text'][:200]}...")
                shown_types.add(block_type)
                
                if len(shown_types) >= 5:  # Показываем максимум 5 типов для краткости
                    break
        
        # Создаем JSON вывод как в API
        blocks_out = [
            {k: v for k, v in b.items() if k != "element"}
            for b in blocks
        ]
        
        # Сохраняем результат для сравнения
        result_file = "test_result.json"
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump({"blocks": blocks_out}, f, ensure_ascii=False, indent=2)
        
        print(f"\nРезультат сохранен в {result_file}")
        
        return blocks_out
        
    except Exception as e:
        print(f"Ошибка тестирования: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    test_updated_block_builder()