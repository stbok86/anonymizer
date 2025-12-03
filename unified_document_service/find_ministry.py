from docx import Document

doc = Document('test_docs/test_01_1_4_SD33.docx')

print("Все упоминания 'министерств':")
for i, para in enumerate(doc.paragraphs):
    if 'инистерств' in para.text.lower():
        print(f"\nПараграф {i}:")
        print(f"  Текст: {para.text[:150]}")
