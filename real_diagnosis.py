#!/usr/bin/env python3
"""
РЕАЛЬНАЯ ДИАГНОСТИКА ПРОБЛЕМЫ ЗАМЕНЫ
===================================

Практический инструмент для выявления настоящей причины пропуска замены
конкретного элемента "Общество с ограниченной ответственностью «КАМА Технологии»"
"""

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path

# Добавляем пути к модулям
unified_service_path = os.path.join(os.path.dirname(__file__), 'unified_document_service', 'app')
sys.path.append(unified_service_path)

def real_diagnosis():
    """
    Реальная диагностика что происходит при замене
    """
    print("🔧 РЕАЛЬНАЯ ДИАГНОСТИКА ПРОБЛЕМЫ ЗАМЕНЫ")
    print("=" * 80)
    
    try:
        from docx import Document
        from block_builder import BlockBuilder
        from full_anonymizer import FullAnonymizer
        from formatter_applier import FormatterApplier
        
        print("✅ Модули импортированы успешно")
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        return
    
    # Путь к тестовому документу
    doc_path = "unified_document_service/test_docs/test_01_1_4_S.docx"
    
    if not os.path.exists(doc_path):
        print(f"❌ Файл не найден: {doc_path}")
        return
    
    print(f"📄 Анализ файла: {doc_path}")
    print()
    
    # ЭТАП 1: Реальный анализ документа через BlockBuilder
    print("🔍 ЭТАП 1: АНАЛИЗ ЧЕРЕЗ BLOCKBUILDER")
    print("-" * 40)
    
    doc = Document(doc_path)
    block_builder = BlockBuilder()
    
    # Получаем блоки как их видит система
    blocks = block_builder.build_blocks(doc)
    
    target_text = "Общество с ограниченной ответственностью «КАМА Технологии»"
    print(f"🎯 Ищем текст: '{target_text}'")
    print(f"📊 Найдено блоков: {len(blocks)}")
    print()
    
    # Ищем блоки содержащие наш текст
    matching_blocks = []
    for block in blocks:
        content = block.get('content', '')
        if target_text in content:
            matching_blocks.append(block)
            print(f"✅ НАЙДЕН в блоке: {block['block_id']}")
        elif 'КАМА Технологии' in content:
            matching_blocks.append(block)
            print(f"⚠️  ЧАСТИЧНО найден в блоке: {block['block_id']} - содержит 'КАМА Технологии'")
    
    if not matching_blocks:
        print("❌ Блоки с искомым текстом НЕ найдены!")
        print("\n🔍 Показываем все блоки для анализа:")
        for i, block in enumerate(blocks[:10]):
            content = block.get('content', '')[:100]
            print(f"  {block['block_id']}: '{content}{'...' if len(block.get('content', '')) > 100 else ''}'")
        return
    
    print(f"\n📋 Найдено подходящих блоков: {len(matching_blocks)}")
    
    # ЭТАП 2: Детальный анализ найденных блоков
    print("\n🔬 ЭТАП 2: ДЕТАЛЬНЫЙ АНАЛИЗ БЛОКОВ")
    print("-" * 35)
    
    for block in matching_blocks:
        print(f"\n📦 Блок: {block['block_id']}")
        print(f"   Тип: {block.get('block_type', 'unknown')}")
        print(f"   Содержимое: '{block.get('content', '')}' (длина: {len(block.get('content', ''))})")
        print(f"   Element: {type(block.get('element')) if block.get('element') else 'None'}")
        
        # Если это параграф, анализируем runs
        element = block.get('element')
        if element and hasattr(element, 'runs'):
            print(f"   📝 Анализ runs в параграфе:")
            print(f"      Количество runs: {len(element.runs)}")
            for i, run in enumerate(element.runs):
                run_text = run.text or ''
                print(f"      Run {i}: '{run_text}' (длина: {len(run_text)})")
                
                # Проверяем форматирование
                try:
                    print(f"         Bold: {run.bold}, Italic: {run.italic}")
                except:
                    print("         Форматирование: недоступно")
    
    # ЭТАП 3: Симуляция реального процесса замены
    print("\n⚡ ЭТАП 3: СИМУЛЯЦИЯ РЕАЛЬНОГО ПРОЦЕССА ЗАМЕНЫ")
    print("-" * 50)
    
    # Берем первый подходящий блок
    target_block = matching_blocks[0]
    print(f"🎯 Используем блок: {target_block['block_id']}")
    
    # Создаем реальный объект замены как это делает система
    fake_uuid = "12345678-1234-1234-1234-123456789012"
    replacement_item = {
        'block_id': target_block['block_id'],
        'original_value': target_text,
        'uuid': fake_uuid,
        'position': {'start': 0, 'end': len(target_text)},
        'element': target_block.get('element'),
        'category': 'organization'
    }
    
    print(f"🔄 Замена: '{target_text}' → '{fake_uuid}'")
    
    # Применяем замену через FormatterApplier
    formatter = FormatterApplier(highlight_replacements=True)
    
    print("\n🔧 ВЫЗОВ FormatterApplier._apply_single_replacement:")
    print("-" * 55)
    
    # Включаем детальное логирование прямо здесь
    element = replacement_item.get('element')
    original_value = replacement_item.get('original_value')
    
    if element:
        print(f"✅ Element найден: {type(element)}")
        
        if hasattr(element, 'text'):
            current_text = getattr(element, 'text', '') or ''
            print(f"📝 Текущий text элемента: '{current_text}'")
            print(f"📏 Длина current_text: {len(current_text)}")
            print(f"📏 Длина original_value: {len(original_value)}")
            
            # Проверяем точное совпадение
            if original_value == current_text:
                print("✅ ТОЧНОЕ СОВПАДЕНИЕ!")
            elif original_value in current_text:
                print("✅ ЧАСТИЧНОЕ СОВПАДЕНИЕ!")
                start_pos = current_text.find(original_value)
                print(f"   Позиция: {start_pos}")
            else:
                print("❌ СОВПАДЕНИЯ НЕТ!")
                print(f"   Искали: '{original_value}'")
                print(f"   В тексте: '{current_text}'")
                
                # Проверяем побайтово
                print(f"\n🔬 ПОБАЙТОВОЕ СРАВНЕНИЕ:")
                orig_bytes = original_value.encode('utf-8')
                curr_bytes = current_text.encode('utf-8')
                print(f"   original_value bytes: {orig_bytes}")
                print(f"   current_text bytes:   {curr_bytes}")
                
                # Ищем различия
                min_len = min(len(original_value), len(current_text))
                for i in range(min_len):
                    if original_value[i] != current_text[i]:
                        print(f"   РАЗЛИЧИЕ на позиции {i}: '{original_value[i]}' != '{current_text[i]}'")
                        print(f"   ord({original_value[i]}) = {ord(original_value[i])}")
                        print(f"   ord({current_text[i]}) = {ord(current_text[i])}")
                        break
        
        if hasattr(element, 'runs'):
            print(f"\n📋 АНАЛИЗ RUNS:")
            for i, run in enumerate(element.runs):
                run_text = run.text or ''
                print(f"   Run {i}: '{run_text}'")
                if original_value in run_text:
                    print(f"      ✅ НАЙДЕНО в run {i}!")
                elif 'КАМА' in run_text:
                    print(f"      ⚠️  Частично найдено в run {i}")
    
    else:
        print("❌ Element is None!")
    
    # ЭТАП 4: Реальный вызов метода замены
    print("\n🎮 ЭТАП 4: РЕАЛЬНЫЙ ВЫЗОВ ЗАМЕНЫ")
    print("-" * 35)
    
    try:
        result = formatter._apply_single_replacement(replacement_item)
        print(f"📊 Результат замены: {result}")
        
        # Проверяем что изменилось
        if element and hasattr(element, 'text'):
            new_text = element.text or ''
            print(f"📄 Текст после замены: '{new_text}'")
            
            if fake_uuid in new_text:
                print("✅ ЗАМЕНА ПРИМЕНЕНА!")
            else:
                print("❌ ЗАМЕНА НЕ ПРИМЕНЕНА!")
                
    except Exception as e:
        print(f"❌ ОШИБКА при вызове замены: {e}")
        import traceback
        print(f"🔧 Traceback: {traceback.format_exc()}")
    
    print("\n" + "=" * 80)
    print("🎯 ДИАГНОСТИКА ЗАВЕРШЕНА")
    print("Теперь вы видите РЕАЛЬНУЮ причину проблемы!")

if __name__ == "__main__":
    real_diagnosis()