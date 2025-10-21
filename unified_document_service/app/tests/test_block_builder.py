import os
import pytest
from docx import Document
from app.block_builder import BlockBuilder

TEST_DOCS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../test_docs'))

def get_test_docx_files():
	return [os.path.join(TEST_DOCS_DIR, f) for f in os.listdir(TEST_DOCS_DIR) if f.endswith('.docx')]

@pytest.mark.parametrize("docx_path", get_test_docx_files())
def test_block_builder_blocks(docx_path):
	doc = Document(docx_path)
	builder = BlockBuilder()
	blocks = builder.build_blocks(doc)
	# Проверяем, что блоки есть
	assert isinstance(blocks, list)
	assert all('block_id' in b and 'text' in b and 'type' in b and 'element' in b for b in blocks)
	# Проверяем, что типы корректны
	for b in blocks:
		assert b['type'] in ('paragraph', 'table')
		assert isinstance(b['text'], str)
		assert b['text'].strip() != ''
