#!/usr/bin/env python3
"""
Тест для множественных замен ВНУТРИ ОДНОГО параграфа/элемента
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from docx import Document
from app.formatter_applier import FormatterApplier
import uuid

def test_multiple_replacements_in_same_element():
    """
    Тест множественных замен внутри одного элемента
    """
    print("🔍 ТЕСТ МНОЖЕСТВЕННЫХ ЗАМЕН ВНУТРИ ОДНОГО ЭЛЕМЕНТА")
    print("=" * 60)
    
    doc_path = r"C:\Projects\Anonymizer\unified_document_service\test_docs\test_01_1_4.docx"
    doc = Document(doc_path)
    
    # Ищем параграф 71, который содержит НЕСКОЛЬКО дат "14 августа 2023"
    target_para = None
    for para_idx, para in enumerate(doc.paragraphs):
        if para_idx == 71:  # Параграф 71 из предыдущего теста
            target_para = para
            break
    
    if not target_para:
        print("❌ Параграф 71 не найден")
        return
        
    para_text = target_para.text
    print(f"📄 Параграф 71:")
    print(f"   Длина: {len(para_text)} символов")
    print(f"   Текст: {para_text[:200]}...")
    
    # Ищем ВСЕ позиции "14 августа 2023" в этом параграфе
    search_text = "14 августа 2023"
    positions = []
    start = 0
    
    while True:
        pos = para_text.find(search_text, start)
        if pos == -1:
            break
        positions.append(pos)
        print(f"   Найдено на позиции {pos}: '{para_text[pos-10:pos+25]}'")
        start = pos + 1
    
    print(f"\n📊 Всего найдено {len(positions)} вхождений в одном параграфе")
    
    if len(positions) < 2:
        print("⚠️ Недостаточно вхождений для теста (нужно минимум 2)")
        return
        
    # Создаем замены с разными UUID для каждой позиции в ОДНОМ параграфе
    test_replacements = []
    
    for i, pos in enumerate(positions):
        test_uuid = str(uuid.uuid4())
        replacement = {
            'uuid': test_uuid,
            'element': target_para,  # ⭐ ОДИН И ТОТ ЖЕ ЭЛЕМЕНТ!
            'original_value': search_text,
            'category': 'date',
            'block_id': f'para_71_position_{pos}',  # Разные блоки по позициям
            'position': {
                'start': pos,
                'end': pos + len(search_text)
            }
        }
        test_replacements.append(replacement)
        print(f"🔧 Замена #{i+1}: UUID={test_uuid[:8]}... на позиции {pos}")
    
    print(f"\n" + "=" * 60)
    print(f"🚀 ТЕСТИРУЕМ {len(test_replacements)} ЗАМЕН В ОДНОМ ПАРАГРАФЕ")
    print("=" * 60)
    
    # ВАЖНО: Сортируем в обратном порядке по позициям (как должно быть)
    test_replacements.sort(key=lambda x: x['position']['start'], reverse=True)
    print("📋 Порядок замен (по позициям в обратном порядке):")
    for i, repl in enumerate(test_replacements):
        print(f"   {i+1}. Позиция {repl['position']['start']}: UUID {repl['uuid'][:8]}...")
    
    formatter = FormatterApplier()
    successful_replacements = 0
    
    for i, replacement in enumerate(test_replacements):
        print(f"\n--- ЗАМЕНА #{i+1} (Позиция {replacement['position']['start']}) ---")
        
        success = formatter._apply_single_replacement(replacement)
        if success:
            successful_replacements += 1
            print(f"Результат: ✅ Успех")
        else:
            print(f"Результат: ❌ Ошибка")
    
    print(f"\n📊 ИТОГ: {successful_replacements}/{len(test_replacements)} замен успешно")
    
    # Анализируем результат
    print("\n" + "=" * 60)
    print("🔍 АНАЛИЗ РЕЗУЛЬТАТА В ПАРАГРАФЕ")
    print("=" * 60)
    
    final_text = target_para.text
    print(f"📄 Финальный текст параграфа:")
    print(f"   Длина: {len(final_text)} символов")
    
    # Ищем оставшиеся оригинальные даты
    remaining_dates = final_text.count(search_text)
    print(f"🔍 Оставшиеся оригинальные даты: {remaining_dates}")
    
    # Ищем UUID в финальном тексте
    uuid_found = {}
    words = final_text.split()
    for word in words:
        if len(word) == 36 and word.count('-') == 4:  # Формат UUID
            if word in uuid_found:
                uuid_found[word] += 1
            else:
                uuid_found[word] = 1
    
    print(f"🔍 Найдено UUID в параграфе: {len(uuid_found)}")
    for uuid_str, count in uuid_found.items():
        print(f"   {uuid_str}: {count} раз(а)")
    
    # Проверяем правильность
    expected_uuids = len(positions)
    expected_remaining = 0  # Все должны быть заменены
    
    if len(uuid_found) == expected_uuids and remaining_dates == expected_remaining:
        all_unique = all(count == 1 for count in uuid_found.values())
        if all_unique:
            print("🎉 ИДЕАЛЬНЫЙ РЕЗУЛЬТАТ: Все вхождения заменены уникальными UUID!")
        else:
            print("❌ ПРОБЛЕМА: Есть дублированные UUID!")
    elif len(uuid_found) == 1 and list(uuid_found.values())[0] > 1:
        print("❌ КРИТИЧЕСКАЯ ПРОБЛЕМА: Один UUID используется несколько раз!")
        print("   Это означает, что логика позиций НЕ работает внутри одного элемента!")
    elif successful_replacements == 1 and len(test_replacements) > 1:
        print("❌ ПРОБЛЕМА: Только первая замена сработала, остальные проигнорированы!")
        print("   Это классическая проблема, которую нужно исправить!")
    else:
        print(f"⚠️ ЧАСТИЧНЫЙ УСПЕХ: {successful_replacements} из {len(test_replacements)} замен")

if __name__ == "__main__":
    test_multiple_replacements_in_same_element()