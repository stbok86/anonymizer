"""
Модуль для применения замен в документах с сохранением форматирования
"""

import re
import uuid
from typing import List, Dict, Any, Optional, Tuple
from docx.shared import RGBColor
from docx.enum.text import WD_COLOR_INDEX


class FormatterApplier:
    def __init__(self, highlight_replacements: bool = False):
        """
        Инициализация применителя форматирования
        
        Args:
            highlight_replacements: Выделять ли замененный текст цветом
        """
        self.highlight_replacements = highlight_replacements
        self.replacement_color = WD_COLOR_INDEX.YELLOW  # Цвет выделения замен
        
    def apply_replacements(self, doc, replacements_table: List[Dict]) -> int:
        """
        Метод-алиас для совместимости с предыдущими версиями
        
        Args:
            doc: Документ DOCX
            replacements_table: Таблица замен
            
        Returns:
            Количество применененных замен
        """
        result = self.apply_replacements_to_document(doc, replacements_table)
        return result.get('total_replacements', 0)
    
    def apply_replacements_to_document(self, doc, replacements: List[Dict]) -> Dict[str, Any]:
        """
        Применение замен к документу с сохранением форматирования
        
        Args:
            doc: Документ DOCX 
            replacements: Список замен с информацией о позициях
            
        Returns:
            Статистика применения замен
        """
        print(f"📝 [FORMATTER_APPLIER] Получено замен для обработки: {len(replacements)}")
        for i, match in enumerate(replacements[:5]):  # Показываем первые 5
            print(f"📝 [FORMATTER_APPLIER] Замена {i+1}: '{match.get('original_value', 'N/A')}' → '{match.get('uuid', 'N/A')}'")
        if len(replacements) > 5:
            print(f"📝 [FORMATTER_APPLIER] ... и еще {len(replacements) - 5} замен")
            
        if not replacements:
            return {
                'total_replacements': 0,
                'categories': {},
                'blocks_processed': 0
            }
        
        stats = {
            'total_replacements': 0,
            'categories': {},
            'blocks_processed': 0,
            'replacement_details': []
        }
        
        # Группируем замены по блокам для эффективной обработки
        replacements_by_block = {}
        for replacement in replacements:
            block_id = replacement.get('block_id')
            if block_id not in replacements_by_block:
                replacements_by_block[block_id] = []
            replacements_by_block[block_id].append(replacement)
        
        # Обрабатываем каждый блок
        for block_id, block_replacements in replacements_by_block.items():
            try:
                # Сортируем замены по позиции (в обратном порядке для корректной замены)
                block_replacements.sort(key=lambda x: x.get('position', {}).get('start', 0), reverse=True)
                
                block_stats = self._apply_replacements_to_block(block_replacements)
                
                # Агрегируем статистику
                stats['total_replacements'] += block_stats['replacements_made']
                stats['blocks_processed'] += 1
                
                # Подсчет по категориям
                for replacement in block_replacements:
                    category = replacement.get('category', 'unknown')
                    if category not in stats['categories']:
                        stats['categories'][category] = 0
                    stats['categories'][category] += 1
                
                stats['replacement_details'].extend(block_stats['details'])
                
            except Exception as e:
                print(f"Ошибка при обработке блока {block_id}: {str(e)}")
                continue
        
        return stats
    
    def _apply_replacements_to_block(self, block_replacements: List[Dict]) -> Dict[str, Any]:
        """
        Применение замен к конкретному блоку
        
        Args:
            block_replacements: Список замен для данного блока
            
        Returns:
            Статистика по блоку
        """
        block_stats = {
            'replacements_made': 0,
            'details': []
        }
        
        for replacement in block_replacements:
            try:
                success = self._apply_single_replacement(replacement)
                if success:
                    block_stats['replacements_made'] += 1
                    block_stats['details'].append({
                        'uuid': replacement.get('uuid'),
                        'category': replacement.get('category'),
                        'original_value': replacement.get('original_value'),
                        'success': True
                    })
                    
            except Exception as e:
                print(f"Ошибка при применении замены {replacement.get('uuid', 'unknown')}: {str(e)}")
                block_stats['details'].append({
                    'uuid': replacement.get('uuid'),
                    'category': replacement.get('category'),
                    'original_value': replacement.get('original_value'),
                    'success': False,
                    'error': str(e)
                })
        
        return block_stats
    
    def _apply_single_replacement(self, replacement: Dict) -> bool:
        """
        Применение одной конкретной замены
        
        Args:
            replacement: Информация о замене
            
        Returns:
            True если замена применена успешно
        """
        try:
            element = replacement.get('element')
            original_value = replacement.get('original_value', '')
            position = replacement.get('position', {})
            
            print(f"🔧 Пытаемся применить замену:")
            print(f"   Оригинал: '{original_value}'")
            print(f"   Element: {type(element) if element else 'None'}")
            print(f"   Position: {position}")
            
            if element is None or not original_value:
                print(f"   ❌ Пропуск: element={element}, original_value='{original_value}'")
                return False
                
            # Дополнительная проверка для None значений
            if original_value is None:
                print(f"   ❌ original_value is None")
                return False
            
            # Генерируем замещающее значение с использованием существующего UUID
            replacement_value = self._generate_replacement_value(
                original_value, 
                replacement.get('category', 'unknown'),
                replacement.get('uuid')
            )
            
            print(f"   🔄 Замена: '{original_value}' → '{replacement_value}'")
            
            # Применяем замену в зависимости от типа элемента
            if hasattr(element, 'rows'):
                # Таблица (проверяем rows, так как у таблиц нет прямого атрибута cells)
                result = self._replace_in_table(element, original_value, replacement_value)
                print(f"   📊 Замена в таблице: {result}")
                return result
            elif hasattr(element, 'text'):
                # Параграф
                result = self._replace_in_paragraph(element, original_value, replacement_value, position)
                print(f"   📝 Замена в параграфе: {result}")
                return result
            else:
                # Общий случай - пытаемся заменить текст
                current_text = getattr(element, 'text', '')
                # Дополнительная проверка для None
                if current_text is None:
                    current_text = ''
                print(f"   📄 Текущий текст элемента: '{current_text}'")
                if original_value and original_value in current_text:
                    new_text = current_text.replace(original_value, replacement_value)
                    element.text = new_text
                    print(f"   ✅ Общая замена: '{current_text}' → '{new_text}'")
                    return True
                else:
                    print(f"   ❌ Значение '{original_value}' не найдено в тексте '{current_text}'")
                    
            return False
            
        except Exception as e:
            print(f"Ошибка при применении замены: {str(e)}")
            return False
    
    def _replace_in_paragraph(self, paragraph, original_value: str, replacement_value: str, position: Dict) -> bool:
        """
        Замена текста в параграфе с сохранением форматирования
        
        Args:
            paragraph: Параграф документа
            original_value: Исходное значение для замены
            replacement_value: Замещающее значение
            position: Позиция замены
            
        Returns:
            True если замена применена
        """
        try:
            # Простая замена текста
            paragraph_text = getattr(paragraph, 'text', '')
            if paragraph_text is None:
                paragraph_text = ''
                
            if original_value and original_value in paragraph_text:
                # Сохраняем форматирование первого run
                if paragraph.runs:
                    first_run = paragraph.runs[0]
                    
                    # Заменяем текст
                    paragraph.text = paragraph.text.replace(original_value, replacement_value)
                    
                    # Применяем выделение если включено
                    if self.highlight_replacements and paragraph.runs:
                        for run in paragraph.runs:
                            if replacement_value in run.text:
                                run.font.highlight_color = self.replacement_color
                
                return True
            return False
            
        except Exception as e:
            print(f"Ошибка замены в параграфе: {str(e)}")
            return False
    
    def _replace_in_table(self, table, original_value: str, replacement_value: str) -> bool:
        """
        Замена текста в таблице
        
        Args:
            table: Таблица документа
            original_value: Исходное значение
            replacement_value: Замещающее значение
            
        Returns:
            True если замена применена
        """
        try:
            replacement_made = False
            
            for row_idx, row in enumerate(table.rows):
                for cell_idx, cell in enumerate(row.cells):
                    # Безопасная проверка текста ячейки
                    cell_text = getattr(cell, 'text', '') or ''
                    
                    if original_value and original_value in cell_text:
                        # Заменяем в каждом параграфе ячейки
                        for para_idx, paragraph in enumerate(cell.paragraphs):
                            paragraph_text = getattr(paragraph, 'text', '') or ''
                            
                            if original_value and original_value in paragraph_text:
                                paragraph.text = paragraph_text.replace(original_value, replacement_value)
                                replacement_made = True
                                
                                # Применяем выделение
                                if self.highlight_replacements:
                                    for run in paragraph.runs:
                                        if replacement_value in run.text:
                                            run.font.highlight_color = self.replacement_color
                
            return replacement_made
            
        except Exception as e:
            print(f"Ошибка замены в таблице: {str(e)}")
            return False
    
    def _generate_replacement_value(self, original_value: str, category: str, existing_uuid: str = None) -> str:
        """
        Генерация замещающего значения на основе категории
        
        Args:
            original_value: Исходное значение
            category: Категория найденных данных
            existing_uuid: Существующий UUID из анализа (если есть)
            
        Returns:
            Замещающее значение
        """
        # Используем существующий UUID или генерируем новый
        if existing_uuid:
            # Используем полный UUID как есть
            replacement_uuid = existing_uuid
        else:
            # Генерируем новый UUID для замены (только если не передан существующий)
            replacement_uuid = str(uuid.uuid4())
        
        # Возвращаем только UUID без префиксов
        return replacement_uuid
    
    def generate_replacement_report(self, replacements: List[Dict]) -> Dict[str, Any]:
        """
        Генерация отчета о произведенных заменах
        
        Args:
            replacements: Список замен
            
        Returns:
            Отчет о заменах
        """
        report = {
            'total_replacements': len(replacements),
            'categories': {},
            'confidence_stats': {
                'high': 0,  # > 0.8
                'medium': 0,  # 0.5 - 0.8  
                'low': 0    # < 0.5
            }
        }
        
        for replacement in replacements:
            # Подсчет по категориям
            category = replacement.get('category', 'unknown')
            if category not in report['categories']:
                report['categories'][category] = 0
            report['categories'][category] += 1
            
            # Статистика уверенности
            confidence = replacement.get('confidence', 1.0)
            if confidence > 0.8:
                report['confidence_stats']['high'] += 1
            elif confidence > 0.5:
                report['confidence_stats']['medium'] += 1
            else:
                report['confidence_stats']['low'] += 1
        
        return report