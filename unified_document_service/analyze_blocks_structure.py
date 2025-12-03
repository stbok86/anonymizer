import sys
sys.path.insert(0, 'app')

from block_builder import BlockBuilder
from docx import Document

doc = Document('test_docs/test_01_1_4_SD33.docx')
builder = BlockBuilder()

blocks = builder.build_blocks(doc)

print("="*80)
print("СТРУКТУРА БЛОКОВ ДОКУМЕНТА")
print("="*80)

# Собираем текст с offset'ами
full_text = ""
block_offsets = []

for block in blocks[:10]:  # Первые 10 блоков
    block_text = block.get('text', block.get('content', ''))
    if block_text.strip():
        block_start = len(full_text)
        full_text += block_text + "\n"
        block_end = len(full_text) - 1
        
        print(f"\nБлок {block['block_id']}:")
        print(f"  Тип: {block.get('block_type', block.get('type', 'unknown'))}")
        print(f"  Позиция: {block_start}-{block_end}")
        print(f"  Длина: {len(block_text)}")
        print(f"  Текст: '{block_text[:100]}{'...' if len(block_text) > 100 else ''}'")
        
        block_offsets.append({
            'block_id': block['block_id'],
            'start': block_start,
            'end': block_end,
            'original_text': block_text
        })

print("\n" + "="*80)
print("АНАЛИЗ ДЕТЕКЦИИ МИНИСТЕРСТВО")
print("="*80)

ministry_text = "МИНИСТЕРСТВО ИНФОРМАЦИОННОГО РАЗВИТИЯ И СВЯЗИ\nПЕРМСКОГО КРАЯ\nЕДИНАЯ"
ministry_start = full_text.find(ministry_text)
ministry_end = ministry_start + len(ministry_text) if ministry_start != -1 else -1

print(f"\nТекст детекции: '{ministry_text[:50]}...'")
print(f"Позиция в full_text: {ministry_start}-{ministry_end}")

if ministry_start != -1:
    # Проверяем, в какие блоки попадает
    print(f"\nПроверяем вхождение в блоки:")
    for block_info in block_offsets:
        if ministry_start >= block_info['start'] and ministry_end <= block_info['end']:
            print(f"  ✅ ПОЛНОСТЬЮ входит в блок {block_info['block_id']}")
        elif ministry_start < block_info['end'] and ministry_end > block_info['start']:
            print(f"  ⚠️  ЧАСТИЧНО пересекается с блоком {block_info['block_id']}")
            print(f"      Блок: {block_info['start']}-{block_info['end']}")
            print(f"      Детекция: {ministry_start}-{ministry_end}")
else:
    print("❌ Детекция не найдена в full_text!")
    print(f"\nПервые 200 символов full_text:")
    print(full_text[:200])
