#!/usr/bin/env python3
"""
Детальная диагностика поиска текста в параграфе
"""

from docx import Document
from app.block_builder import BlockBuilder

def analyze_text_search():
    print("🔍 АНАЛИЗ ПОИСКА ТЕКСТА")
    print("=" * 60)
    
    # Открываем документ
    doc = Document("test_docs/test_01_1_4_S.docx")
    builder = BlockBuilder()
    blocks = builder.build_blocks(doc)
    
    # Находим paragraph_82
    target_paragraph = None
    for block in blocks:
        if block['block_id'] == 'paragraph_82':
            target_paragraph = block['element']
            print(f"✅ Найден paragraph_82")
            print(f"   Тип элемента: {type(target_paragraph)}")
            print(f"   Полный текст: '{target_paragraph.text}'")
            break
    
    if not target_paragraph:
        print("❌ paragraph_82 не найден!")
        return
    
    # Искомый текст из фронтенда  
    search_text = "Общество с ограниченной ответственностью «КАМА Технологии»"
    full_text = target_paragraph.text
    
    print(f"\n🎯 СРАВНЕНИЕ ТЕКСТОВ:")
    print(f"   Ищем:     '{search_text}'")
    print(f"   В тексте: '{full_text}'")
    print(f"   Длина искомого: {len(search_text)}")
    print(f"   Длина полного:  {len(full_text)}")
    
    # Проверим найдется ли
    found = search_text in full_text
    print(f"   Найден: {found}")
    
    # Найдем индекс если есть
    if found:
        index = full_text.find(search_text)
        print(f"   Позиция: {index}")
    else:
        print("\n🔍 ПОСИМВОЛЬНЫЙ АНАЛИЗ:")
        
        # Найдем где начинается "Общество"
        start_word = "Общество"
        start_index = full_text.find(start_word)
        if start_index >= 0:
            print(f"   '{start_word}' найдено на позиции {start_index}")
            
            # Покажем символы вокруг
            context_start = max(0, start_index - 10)
            context_end = min(len(full_text), start_index + len(search_text) + 10)
            context = full_text[context_start:context_end]
            print(f"   Контекст: '{context}'")
            
            # Извлечем ровно столько символов сколько в искомом тексте
            extracted = full_text[start_index:start_index + len(search_text)]
            print(f"   Извлеченный текст: '{extracted}'")
            print(f"   Равен искомому: {extracted == search_text}")
            
            # Поищем различия
            if extracted != search_text:
                print("\n🔬 РАЗЛИЧИЯ ПО СИМВОЛАМ:")
                for i, (c1, c2) in enumerate(zip(extracted, search_text)):
                    if c1 != c2:
                        print(f"      Позиция {i}: получен '{c1}' ({ord(c1)}), ожидался '{c2}' ({ord(c2)})")
                
                if len(extracted) != len(search_text):
                    print(f"      Длина различается: {len(extracted)} vs {len(search_text)}")

    # Проверим также анализ runs
    print(f"\n🔧 АНАЛИЗ RUNS:")
    print(f"   Количество runs: {len(target_paragraph.runs)}")
    for i, run in enumerate(target_paragraph.runs):
        print(f"   Run {i}: '{run.text}'")
        
    # Соберем полный текст из runs
    runs_text = "".join([run.text for run in target_paragraph.runs])
    print(f"   Полный текст из runs: '{runs_text}'")
    print(f"   Равен paragraph.text: {runs_text == full_text}")
    
    # Поищем в полном тексте из runs  
    found_in_runs = search_text in runs_text
    print(f"   Найден в runs_text: {found_in_runs}")

if __name__ == "__main__":
    analyze_text_search()