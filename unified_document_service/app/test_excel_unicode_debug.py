import os
from full_anonymizer import FullAnonymizer

def test_excel_unicode_debug():
    # Путь к реальному docx
    docx_path = r'C:\Projects\Anonymizer\unified_document_service\test_docs\РегламентФермСтат.docx'
    patterns_path = r'C:\Projects\Anonymizer\unified_document_service\patterns\sensitive_patterns.xlsx'
    output_dir = r'C:\Projects\Anonymizer\unified_document_service\test_docs'
    excel_path = os.path.join(output_dir, 'test_excel_unicode_debug.xlsx')

    # Инициализация анонимизатора
    anonymizer = FullAnonymizer(patterns_path=patterns_path)
    doc = anonymizer.block_builder.build_blocks(anonymizer.block_builder.load_docx(docx_path))
    # Сгенерируем тестовые совпадения с unicode-символами
    matches = [
        {'original_value': 'Тест -> символ', 'category': 'test', 'uuid': 'uuid-1', 'block_id': 'block-1'},
        {'original_value': 'Стандартный текст', 'category': 'test', 'uuid': 'uuid-2', 'block_id': 'block-2'},
        {'original_value': 'Ещё один -> пример', 'category': 'test', 'uuid': 'uuid-3', 'block_id': 'block-3'},
    ]
    # Попробуем сгенерировать Excel
    print(f"[DEBUG] Генерируем Excel по пути: {excel_path}")
    anonymizer._generate_excel_report(doc, matches, excel_path)
    print(f"[DEBUG] Готово. Проверьте логи на наличие ошибок UnicodeEncodeError.")

if __name__ == "__main__":
    test_excel_unicode_debug()
