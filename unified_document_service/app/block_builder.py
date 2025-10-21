

from typing import List, Dict, Any
from docx.document import Document as _Document
from docx.table import Table
from docx.text.paragraph import Paragraph

class BlockBuilder:
	"""
	Класс для нарезки DOCX-документа на блоки с сохранением ссылок на объекты.
	КРИТИЧНО: Обрабатывает ВСЕ элементы включая headers/footers для анонимизации.
	Поддерживает параграфы, таблицы, headers и footers с правильным порядком.
	"""
	def build_blocks(self, document: _Document) -> List[Dict[str, Any]]:
		blocks = []
		
		# Глобальные счетчики для всех типов элементов
		para_idx, table_idx, header_idx, footer_idx = 0, 0, 0, 0
		# Собираем тексты headers/footers для последующего поиска по всему документу
		header_texts: List[str] = []
		footer_texts: List[str] = []
		
		# ЭТАП 1: Сначала обрабатываем ВСЕ Headers (критично для анонимизации)
		for s_idx, section in enumerate(document.sections):
			header = section.header
			# Обрабатываем все элементы в header
			header_blocks = self._extract_header_footer_blocks(header, s_idx, "header")
			blocks.extend(header_blocks)
			header_idx += len(header_blocks)
			# Собираем текстовые представления header для поиска в теле
			for hb in header_blocks:
				if hb.get("text"):
					header_texts.append(hb.get("text"))
		
		# ЭТАП 2: Основное тело документа
		for el in document.element.body:
			if el.tag.endswith('}p'):
				paragraph = Paragraph(el, document)
				# Извлекаем ВСЕ параграфы, даже пустые (могут содержать скрытый текст)
				text_content = self._normalize_text(paragraph.text)
				# Дополнительная проверка на скрытый/форматированный текст
				if text_content or self._has_formatted_content(paragraph):
					blocks.append({
						"block_id": f"paragraph_{para_idx}",
						"text": text_content,
						"type": "paragraph",
						"element": paragraph
					})
				para_idx += 1
			elif el.tag.endswith('}tbl'):
				table = Table(el, document)
				table_text = self._extract_table_text(table)
				if table_text:
					blocks.append({
						"block_id": f"table_{table_idx}",
						"text": table_text,
						"type": "table",
						"element": table
					})
				table_idx += 1
		
		# ЭТАП 3: Все Footers 
		for s_idx, section in enumerate(document.sections):
			footer = section.footer
			footer_blocks = self._extract_header_footer_blocks(footer, s_idx, "footer")
			blocks.extend(footer_blocks)
			footer_idx += len(footer_blocks)
			for fb in footer_blocks:
				if fb.get("text"):
					footer_texts.append(fb.get("text"))
		
		# --- Пост-обработка: отмечаем все вхождения header/footer текста в других блоках
		# Причина: Word хранит header/footer как часть секции, а не как отдельный элемент на каждой странице.
		# Для анонимизации важно пометить каждое вхождение текста колонтитула в теле документа.
		if header_texts or footer_texts:
			for b in blocks:
				# Не ищем внутри самих header/footer блоков
				if b.get("type") in ("header", "header_table", "header_sdt", "footer", "footer_table", "footer_sdt"):
					continue
				text = self._normalize_text(b.get("text") or "")
				matches = []
				for ht in header_texts:
					normalized_ht = self._normalize_text(ht)
					if normalized_ht and normalized_ht in text:
						matches.append({"source": "header", "text": normalized_ht})
				for ft in footer_texts:
					normalized_ft = self._normalize_text(ft)
					if normalized_ft and normalized_ft in text:
						matches.append({"source": "footer", "text": normalized_ft})
				if matches:
					# Добавляем метаданные о совпадениях, это позволит анонимизатору не пропускать данные
					b.setdefault("sensitive_matches", []).extend(matches)
		
		return blocks
	
	def _extract_header_footer_blocks(self, container, section_idx: int, block_type: str) -> List[Dict[str, Any]]:
		"""Извлекает все блоки из header или footer включая SDT элементы"""
		blocks = []
		para_idx, table_idx, sdt_idx = 0, 0, 0
		
		for el in container._element:
			if el.tag.endswith('}p'):
				paragraph = Paragraph(el, container)
				text_content = self._normalize_text(paragraph.text)
				
				# КРИТИЧНО: Извлекаем ВСЕ параграфы из headers/footers для анонимизации
				if text_content or self._has_formatted_content(paragraph):
					blocks.append({
						"block_id": f"{block_type}_{section_idx}_{para_idx}",
						"text": text_content,
						"type": block_type,
						"applies_to": "section",  # Этот header применяется ко всей секции
						"element": paragraph
					})
				para_idx += 1
			elif el.tag.endswith('}tbl'):
				table = Table(el, container)
				table_text = self._extract_table_text(table)
				if table_text:
					blocks.append({
						"block_id": f"{block_type}_table_{section_idx}_{table_idx}",
						"text": table_text,
						"type": f"{block_type}_table",
						"applies_to": "section",
						"element": table
					})
				table_idx += 1
			elif el.tag.endswith('}sdt'):
				# КРИТИЧНО: Обрабатываем Structured Document Tags (содержат текст колонтитулов)
				sdt_text = self._extract_sdt_text(el)
				if sdt_text:
					blocks.append({
						"block_id": f"{block_type}_sdt_{section_idx}_{sdt_idx}",
						"text": sdt_text,
						"type": f"{block_type}_sdt",
						"applies_to": "section",
						"element": el
					})
				sdt_idx += 1
		
		return blocks
	
	def _extract_table_text(self, table: Table) -> str:
		"""Извлекает текст из таблицы с улучшенной обработкой"""
		rows_text = []
		for row in table.rows:
			row_text = []
			for cell in row.cells:
				cell_content = cell.text.strip()
				if cell_content:
					row_text.append(cell_content)
			if row_text:  # Добавляем строку только если в ней есть содержимое
				rows_text.append(" | ".join(row_text))
		
		return "\n".join(rows_text) if rows_text else ""
	
	def _has_formatted_content(self, paragraph: Paragraph) -> bool:
		"""Проверяет наличие форматированного содержимого в параграфе"""
		try:
			# Проверяем runs для форматированного текста
			for run in paragraph.runs:
				if run.text.strip():
					return True
			return False
		except:
			return False
	
	def _extract_sdt_text(self, sdt_element) -> str:
		"""КРИТИЧНО: Извлекает текст из Structured Document Tag элементов с расширенным поиском"""
		try:
			# Рекурсивно ищем все текстовые элементы в SDT
			text_parts = []
			
			# Расширенные namespaces для поиска текста
			ns = {
				'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
				'a': 'http://schemas.openxmlformats.org/drawingml/2006/main'
			}
			
			# РАСШИРЕННЫЙ XPath: ищем все возможные источники текста
			xpath_query = './/w:t | .//w:instrText | .//a:t | .//w:fldSimple/@w:instr'
			elements = sdt_element.xpath(xpath_query, namespaces=ns)
			
			for elem in elements:
				if hasattr(elem, 'text') and elem.text:
					text_parts.append(self._normalize_text(elem.text))
				elif isinstance(elem, str):  # для атрибутов
					text_parts.append(self._normalize_text(elem))
			
			# Дополнительно ищем текст в текстбоксах
			textbox_elements = sdt_element.xpath('.//w:txbxContent//w:t', namespaces=ns)
			for tb_elem in textbox_elements:
				if tb_elem.text:
					text_parts.append(self._normalize_text(tb_elem.text))
			
			# Если ничего не найдено через XPath, пробуем простое извлечение текста
			if not text_parts:
				if hasattr(sdt_element, 'text') and sdt_element.text:
					text_parts.append(self._normalize_text(sdt_element.text))
			
			result = ' '.join(filter(None, text_parts))
			return result
			
		except Exception as e:
			# В случае ошибки возвращаем пустую строку, но логируем проблему
			print(f"Ошибка извлечения SDT текста: {e}")
			return ""
	
	def _normalize_text(self, text: str) -> str:
		"""Нормализует текст для согласованного поиска и анонимизации"""
		import re
		if not text:
			return ""
		
		# Заменяем неразрывные пробелы на обычные
		normalized = text.replace('\xa0', ' ')
		# Сокращаем множественные пробелы
		normalized = re.sub(r'\s+', ' ', normalized)
		# Убираем пробелы в начале и конце
		normalized = normalized.strip()
		
		return normalized
