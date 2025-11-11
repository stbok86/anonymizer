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
            
            if not element or not original_value:
                return False
            
            # Генерируем замещающее значение
            replacement_value = self._generate_replacement_value(
                original_value, 
                replacement.get('category', 'unknown')
            )
            
            # Применяем замену в зависимости от типа элемента
            if hasattr(element, 'text'):
                # Параграф
                return self._replace_in_paragraph(element, original_value, replacement_value, position)
            elif hasattr(element, 'cells'):
                # Таблица
                return self._replace_in_table(element, original_value, replacement_value)
            else:
                # Общий случай - пытаемся заменить текст
                current_text = getattr(element, 'text', '')
                if original_value in current_text:
                    new_text = current_text.replace(original_value, replacement_value)
                    element.text = new_text
                    return True
                    
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
            if original_value in paragraph.text:
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
            
            for row in table.rows:
                for cell in row.cells:
                    if original_value in cell.text:
                        # Заменяем в каждом параграфе ячейки
                        for paragraph in cell.paragraphs:
                            if original_value in paragraph.text:
                                paragraph.text = paragraph.text.replace(original_value, replacement_value)
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
    
    def _generate_replacement_value(self, original_value: str, category: str) -> str:
        """
        Генерация замещающего значения на основе категории
        
        Args:
            original_value: Исходное значение
            category: Категория найденных данных
            
        Returns:
            Замещающее значение
        """
        # Генерируем UUID для замены
        replacement_uuid = str(uuid.uuid4())[:8].upper()
        
        # Выбираем префикс в зависимости от категории
        if category.lower() in ['name', 'person', 'имя', 'фио']:
            prefix = "PERSON"
        elif category.lower() in ['phone', 'телефон', 'номер']:
            prefix = "PHONE" 
        elif category.lower() in ['email', 'почта']:
            prefix = "EMAIL"
        elif category.lower() in ['address', 'адрес']:
            prefix = "ADDRESS"
        elif category.lower() in ['passport', 'паспорт']:
            prefix = "PASSPORT"
        elif category.lower() in ['inn', 'инн']:
            prefix = "INN"
        elif category.lower() in ['snils', 'снилс']:
            prefix = "SNILS"
        else:
            prefix = "DATA"
        
        return f"[{prefix}_{replacement_uuid}]"
    
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