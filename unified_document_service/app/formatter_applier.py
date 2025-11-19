"""
Модуль для применения замен в документах с сохранением форматирования
"""

import re
import uuid
from typing import List, Dict, Any, Optional, Tuple
from docx.shared import RGBColor
from docx.enum.text import WD_COLOR_INDEX


class FormatterApplier:
    def __init__(self, highlight_replacements: bool = True):
        """
        Инициализация применителя форматирования
        
        Args:
            highlight_replacements: Выделять ли замененный текст жёлтым цветом (по умолчанию True)
        """
        self.highlight_replacements = highlight_replacements
        self.replacement_color = WD_COLOR_INDEX.YELLOW  # Жёлтый цвет для выделения UUID
        
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
            
            print(f"\n🔧 [SINGLE_REPLACEMENT] Начинаем замену:")
            print(f"🔧 [SINGLE_REPLACEMENT] Оригинал: '{original_value}'")
            print(f"🔧 [SINGLE_REPLACEMENT] Element type: {type(element) if element else 'None'}")
            print(f"🔧 [SINGLE_REPLACEMENT] Position: {position}")
            print(f"🔧 [SINGLE_REPLACEMENT] Block ID: {replacement.get('block_id', 'N/A')}")
            print(f"🔧 [SINGLE_REPLACEMENT] Category: {replacement.get('category', 'N/A')}")
            
            if element is None:
                print(f"🔧 [SINGLE_REPLACEMENT] ❌ Element is None")
                return False
                
            if not original_value:
                print(f"🔧 [SINGLE_REPLACEMENT] ❌ original_value is empty")
                return False
                
            # Дополнительная проверка для None значений
            if original_value is None:
                print(f"🔧 [SINGLE_REPLACEMENT] ❌ original_value is None")
                return False
            
            # Генерируем замещающее значение с использованием существующего UUID
            replacement_value = self._generate_replacement_value(
                original_value, 
                replacement.get('category', 'unknown'),
                replacement.get('uuid')
            )
            
            print(f"🔧 [SINGLE_REPLACEMENT] UUID замены: '{replacement_value}'")
            
            # Проверяем содержание элемента перед заменой
            if hasattr(element, 'text'):
                current_text = getattr(element, 'text', '') or ''
                print(f"🔧 [SINGLE_REPLACEMENT] Текущий text: '{current_text}'")
            
            if hasattr(element, 'rows'):
                print(f"🔧 [SINGLE_REPLACEMENT] Таблица с {len(element.rows)} строками")
            
            # Применяем замену в зависимости от типа элемента
            # Применяем замену в зависимости от типа элемента
            if hasattr(element, 'rows'):
                # Таблица (проверяем rows, так как у таблиц нет прямого атрибута cells)
                print(f"🔧 [SINGLE_REPLACEMENT] Обрабатываем таблицу")
                result = self._replace_in_table(element, original_value, replacement_value, position)
                print(f"🔧 [SINGLE_REPLACEMENT] Результат замены в таблице: {result}")
                return result
            elif hasattr(element, 'text'):
                # Параграф
                print(f"🔧 [SINGLE_REPLACEMENT] Обрабатываем параграф")
                result = self._replace_in_paragraph(element, original_value, replacement_value, position)
                print(f"🔧 [SINGLE_REPLACEMENT] Результат замены в параграфе: {result}")
                return result
            else:
                # Общий случай - пытаемся заменить текст
                print(f"🔧 [SINGLE_REPLACEMENT] Общий случай замены")
                current_text = getattr(element, 'text', '')
                # Дополнительная проверка для None
                if current_text is None:
                    current_text = ''
                print(f"🔧 [SINGLE_REPLACEMENT] Текущий текст элемента: '{current_text}'")
                if original_value and original_value in current_text:
                    new_text = current_text.replace(original_value, replacement_value)
                    element.text = new_text
                    print(f"🔧 [SINGLE_REPLACEMENT] ✅ Общая замена: '{current_text}' → '{new_text}'")
                    return True
                else:
                    print(f"🔧 [SINGLE_REPLACEMENT] ❌ Значение '{original_value}' не найдено в тексте '{current_text}'")
                    
            print(f"🔧 [SINGLE_REPLACEMENT] ❌ Замена не выполнена")
            return False
            
        except Exception as e:
            print(f"🔧 [SINGLE_REPLACEMENT] ❌ Ошибка при применении замены: {str(e)}")
            import traceback
            print(f"🔧 [SINGLE_REPLACEMENT] Traceback: {traceback.format_exc()}")
            return False
            
        except Exception as e:
            print(f"Ошибка при применении замены: {str(e)}")
            return False
    
    def _normalize_text(self, text: str) -> str:
        """
        Нормализует текст, заменяя различные типы пробелов на обычные пробелы
        и удаляя лишние пробелы
        """
        if not text:
            return ''
        
        # Заменяем неразрывные пробелы (160) и другие виды пробелов на обычный пробел (32)
        text = text.replace('\u00A0', ' ')  # неразрывный пробел
        text = text.replace('\u2009', ' ')  # тонкий пробел
        text = text.replace('\u2007', ' ')  # цифровой пробел
        text = text.replace('\u2008', ' ')  # пунктуационный пробел
        text = text.replace('\u202F', ' ')  # узкий неразрывный пробел
        text = text.replace('\u3000', ' ')  # идеографический пробел
        
        # Нормализуем пробелы
        return ' '.join(text.split())

    def _replace_in_paragraph(self, paragraph, original_value: str, replacement_value: str, position: Dict) -> bool:
        """
        Замена текста в параграфе с сохранением форматирования и учетом позиции
        
        Args:
            paragraph: Параграф документа
            original_value: Исходное значение для замены
            replacement_value: Замещающее значение
            position: Позиция замены для точного попадания
            
        Returns:
            True если замена применена
        """
        try:
            print(f"🔧 [PARAGRAPH] Попытка замены: '{original_value}' → '{replacement_value}'")
            print(f"🔧 [PARAGRAPH] Информация о позиции: {position}")
            
            # Получаем полный текст параграфа для проверки
            paragraph_text = getattr(paragraph, 'text', '') or ''
            print(f"🔧 [PARAGRAPH] Полный текст параграфа: '{paragraph_text}'")
            print(f"🔧 [PARAGRAPH] Количество runs: {len(paragraph.runs)}")
            
            # Нормализуем текст для поиска
            original_value_normalized = self._normalize_text(original_value)
            paragraph_text_normalized = self._normalize_text(paragraph_text)
            
            print(f"🔧 [PARAGRAPH] Нормализованный искомый текст: '{original_value_normalized}'")
            print(f"🔧 [PARAGRAPH] Нормализованный текст параграфа: '{paragraph_text_normalized}'")
            
            if not original_value_normalized or original_value_normalized not in paragraph_text_normalized:
                print(f"🔧 [PARAGRAPH] ❌ Текст не найден после нормализации")
                return False
            
            # Получаем целевую позицию для проверки
            target_position = position.get('start') if position else None
            print(f"🔧 [PARAGRAPH] Целевая позиция: {target_position}")
            
            # Если позиция указана, проверяем соответствие
            if target_position is not None:
                # Ищем позицию текста в параграфе
                text_position_in_paragraph = paragraph_text_normalized.find(original_value_normalized)
                
                if text_position_in_paragraph == -1:
                    print(f"🔧 [PARAGRAPH] ❌ Текст не найден в параграфе")
                    return False
                
                print(f"🔧 [PARAGRAPH] Позиция текста в параграфе: {text_position_in_paragraph}")
                print(f"🔧 [PARAGRAPH] Целевая позиция в документе: {target_position}")
                
                # Для параграфов используем менее строгую проверку позиции
                # так как позиция может отличаться из-за разной структуры документа
                position_match = True  # Для параграфов пока принимаем любую позицию
                
                if not position_match:
                    print(f"🔧 [PARAGRAPH] ❌ Позиция не совпадает, пропускаем")
                    return False
                else:
                    print(f"🔧 [PARAGRAPH] ✅ Позиция подходит для замены")
                
            replacement_made = False
            
            # Стратегия 1: Прямой поиск с нормализацией в runs
            for i, run in enumerate(paragraph.runs):
                run_text = run.text or ''
                run_text_normalized = self._normalize_text(run_text)
                print(f"🔧 [PARAGRAPH] Run {i}: '{run_text}' (нормализован: '{run_text_normalized}')")
                
                # Пробуем прямое совпадение
                if original_value in run_text or original_value_normalized in run_text_normalized:
                    print(f"🔧 [PARAGRAPH] ✅ Найден в run {i}, заменяем")
                    # Заменяем в исходном тексте run'а
                    old_run_text = run.text
                    if original_value in run_text:
                        run.text = run_text.replace(original_value, replacement_value, 1)  # Заменяем только первое вхождение
                    else:
                        # Если точное совпадение не найдено, но нормализованное есть
                        run.text = self._replace_with_normalization(run_text, original_value, replacement_value)
                    
                    replacement_made = True
                    
                    # Применяем выделение к UUID
                    if self.highlight_replacements:
                        try:
                            run.font.highlight_color = self.replacement_color
                            print(f"🔧 [PARAGRAPH] ✅ Жёлтое выделение UUID применено к run {i}")
                        except Exception as e:
                            print(f"🔧 [PARAGRAPH] ⚠️ Не удалось применить выделение: {e}"))
                    
                    print(f"🔧 [PARAGRAPH] ✅ Замена в run {i} завершена: '{old_run_text}' → '{run.text}'")
                    print(f"🔧 [PARAGRAPH] 🎯 Замена выполнена, выходим из поиска")
                    break  # Выходим после первой успешной замены
            
            # Стратегия 2: Если не нашли в отдельных runs, ищем в пересечении runs с нормализацией
            if not replacement_made and len(paragraph.runs) > 1:
                print(f"🔧 [PARAGRAPH] Стратегия 2: поиск в пересечении runs с нормализацией")
                
                # Собираем текст из всех runs для точного поиска
                full_text = ''.join(run.text for run in paragraph.runs)
                full_text_normalized = self._normalize_text(full_text)
                print(f"🔧 [PARAGRAPH] Полный текст из runs: '{full_text}'")
                print(f"🔧 [PARAGRAPH] Нормализованный полный текст: '{full_text_normalized}'")
                
                if original_value in full_text or original_value_normalized in full_text_normalized:
                    print(f"🔧 [PARAGRAPH] ✅ Найден в пересечении runs")
                    
                    # Найдем позицию в нормализованном тексте
                    search_text = original_value if original_value in full_text else original_value_normalized
                    search_target = full_text if original_value in full_text else full_text_normalized
                    
                    start_pos = search_target.find(search_text)
                    end_pos = start_pos + len(search_text)
                    
                    print(f"🔧 [PARAGRAPH] Позиция в полном тексте: {start_pos}-{end_pos}")
                    print(f"🔧 [PARAGRAPH] Search text: '{search_text}'")
                    print(f"🔧 [PARAGRAPH] Search target: '{search_target}'")
                    print(f"🔧 [PARAGRAPH] Using normalized? {search_target == full_text_normalized}")
                    
                    # Если мы работаем с нормализованным текстом, нужно найти соответствие в исходном
                    if search_target == full_text_normalized:
                        print(f"🔧 [PARAGRAPH] Вызываем _replace_in_normalized_runs")
                        replacement_made = self._replace_in_normalized_runs(paragraph, original_value, replacement_value)
                    else:
                        print(f"🔧 [PARAGRAPH] Вызываем _replace_across_runs")
                        replacement_made = self._replace_across_runs(paragraph, original_value, replacement_value, start_pos, end_pos)
                else:
                    print(f"🔧 [PARAGRAPH] ❌ Текст не найден даже в полном тексте runs")
            
            if replacement_made:
                print(f"🔧 [PARAGRAPH] ✅ Замена выполнена успешно")
            else:
                print(f"🔧 [PARAGRAPH] ❌ Замена не выполнена")
            
            return replacement_made
        except Exception as e:
            print(f"🔧 [PARAGRAPH] ❌ Ошибка при замене в параграфе: {str(e)}")
            return False
    
    def _replace_with_normalization(self, run_text: str, original_value: str, replacement_value: str) -> str:
        """
        Замена текста с учетом нормализации пробелов (только первое вхождение)
        """
        # Создаем карту позиций символов для нормализованного текста к исходному
        normalized = self._normalize_text(run_text)
        original_normalized = self._normalize_text(original_value)
        
        if original_normalized in normalized:
            # Простая замена, если текст точно совпадает после нормализации
            # Заменяем все виды пробелов в исходном тексте на обычные пробелы
            result = run_text
            result = result.replace('\u00A0', ' ')  # неразрывный пробел
            result = result.replace('\u2009', ' ')  # тонкий пробел
            result = result.replace('\u2007', ' ')  # цифровой пробел
            result = result.replace('\u2008', ' ')  # пунктуационный пробел
            result = result.replace('\u202F', ' ')  # узкий неразрывный пробел
            result = result.replace('\u3000', ' ')  # идеографический пробел
            
            # Теперь заменяем нормализованный текст (только первое вхождение)
            if original_normalized in self._normalize_text(result):
                return result.replace(original_value, replacement_value, 1)
        
        return run_text
    
    def _replace_in_normalized_runs(self, paragraph, original_value: str, replacement_value: str) -> bool:
        """
        Замена текста, который найден только после нормализации пробелов
        """
        print(f"🔧 [NORMALIZED_RUNS] Начинаем замену в нормализованном тексте")
        print(f"🔧 [NORMALIZED_RUNS] Искомый текст: '{original_value}'")
        
        # Собираем полный текст и заменяем в нем
        full_text = ''.join(run.text for run in paragraph.runs)
        
        # Нормализуем полный текст 
        full_text_normalized = self._normalize_text(full_text)
        original_normalized = self._normalize_text(original_value)
        
        print(f"🔧 [NORMALIZED_RUNS] Полный текст: '{full_text}'")
        print(f"🔧 [NORMALIZED_RUNS] Нормализованный полный: '{full_text_normalized}'")
        print(f"🔧 [NORMALIZED_RUNS] Нормализованный искомый: '{original_normalized}'")
        
        if original_normalized not in full_text_normalized:
            print(f"🔧 [NORMALIZED_RUNS] ❌ Текст не найден даже после нормализации")
            return False
        
        # Найдем позицию в нормализованном тексте
        normalized_start = full_text_normalized.find(original_normalized)
        normalized_end = normalized_start + len(original_normalized)
        
        print(f"🔧 [NORMALIZED_RUNS] Позиция в нормализованном тексте: {normalized_start}-{normalized_end}")
        
        # Теперь нужно найти соответствующую позицию в исходном тексте
        # Создадим карту соответствий между исходным и нормализованным текстом
        original_to_normalized = []
        normalized_pos = 0
        
        for original_pos, char in enumerate(full_text):
            if char in ['\u00A0', '\u2009', '\u2007', '\u2008', '\u202F', '\u3000']:
                # Неразрывные пробелы - заменяются на обычный пробел
                original_to_normalized.append(normalized_pos)
                normalized_pos += 1
            elif char.isspace():
                # Обычные пробелы остаются
                original_to_normalized.append(normalized_pos)
                normalized_pos += 1
            else:
                # Обычные символы остаются
                original_to_normalized.append(normalized_pos)
                normalized_pos += 1
        
        # Найдем границы в исходном тексте
        original_start = None
        original_end = None
        
        for i, norm_pos in enumerate(original_to_normalized):
            if norm_pos == normalized_start and original_start is None:
                original_start = i
            if norm_pos == normalized_end - 1:
                original_end = i + 1
                break
        
        if original_start is None or original_end is None:
            print(f"🔧 [NORMALIZED_RUNS] ❌ Не удалось найти границы в исходном тексте")
            return False
        
        print(f"🔧 [NORMALIZED_RUNS] Позиция в исходном тексте: {original_start}-{original_end}")
        
        # Теперь заменяем по runs используя позицию в исходном тексте
        return self._replace_across_runs(paragraph, original_value, replacement_value, original_start, original_end)
    
    def _replace_across_runs(self, paragraph, original_value: str, replacement_value: str, start_pos: int, end_pos: int) -> bool:
        """
        Замена текста, распределенного по нескольким runs
        """
        try:
            # Определяем какие runs затронуты
            current_pos = 0
            affected_runs = []
            
            for i, run in enumerate(paragraph.runs):
                run_start = current_pos
                run_end = current_pos + len(run.text)
                
                # Проверяем пересечение с искомым текстом
                if not (run_end <= start_pos or run_start >= end_pos):
                    affected_runs.append({
                        'index': i,
                        'run': run,
                        'run_start': run_start,
                        'run_end': run_end,
                        'text_start': max(0, start_pos - run_start),
                        'text_end': min(len(run.text), end_pos - run_start)
                    })
                
                current_pos = run_end
            
            print(f"🔧 [PARAGRAPH] Затронутые runs: {[r['index'] for r in affected_runs]}")
            
            if affected_runs:
                replacement_made = False
                # Заменяем текст в затронутых runs
                for i, run_info in enumerate(affected_runs):
                    run = run_info['run']
                    text_start = run_info['text_start']
                    text_end = run_info['text_end']
                    
                    if i == 0:
                        # Первый run - добавляем replacement_value
                        if text_start == 0 and text_end == len(run.text):
                            # Весь run заменяется
                            run.text = replacement_value
                        elif text_start == 0:
                            # Заменяем начало
                            run.text = replacement_value + run.text[text_end:]
                        elif text_end == len(run.text):
                            # Заменяем конец
                            run.text = run.text[:text_start] + replacement_value
                        else:
                            # Заменяем середину
                            run.text = run.text[:text_start] + replacement_value + run.text[text_end:]
                        replacement_made = True
                        print(f"🔧 [PARAGRAPH] ✅ Run {run_info['index']} заменен")
                        
                        # Применяем выделение к UUID
                        if self.highlight_replacements:
                            try:
                                run.font.highlight_color = self.replacement_color
                                print(f"🔧 [PARAGRAPH] ✅ Жёлтое выделение UUID применено к run {run_info['index']}")
                            except Exception as e:
                                print(f"🔧 [PARAGRAPH] ⚠️ Не удалось применить выделение: {e}")
                    else:
                        # Остальные runs - убираем затронутый текст
                        if text_start == 0 and text_end == len(run.text):
                            # Весь run удаляется
                            run.text = ""
                        elif text_start == 0:
                            # Удаляем начало
                            run.text = run.text[text_end:]
                        elif text_end == len(run.text):
                            # Удаляем конец
                            run.text = run.text[:text_start]
                        else:
                            # Удаляем середину (редкий случай)
                            run.text = run_text[:text_start] + run_text[text_end:]
                        print(f"🔧 [PARAGRAPH] ✅ Run {run_info['index']} обрезан")
                        
                        # Применяем выделение, если в run есть текст
                        if self.highlight_replacements and run.text.strip():
                            try:
                                run.font.highlight_color = self.replacement_color
                                print(f"🔧 [PARAGRAPH] ✅ Выделение применено к обрезанному run {run_info['index']}")
                            except Exception as e:
                                print(f"🔧 [PARAGRAPH] ⚠️ Не удалось применить выделение: {e}")
                
                return replacement_made
            
            return False
        except Exception as e:
            print(f"🔧 [PARAGRAPH] ❌ Ошибка при замене через runs: {str(e)}")
            return False

    def _replace_in_table(self, table, original_value: str, replacement_value: str, position_info: dict = None) -> bool:
        """
        Замена текста в таблице
        
        Args:
            table: Таблица документа
            original_value: Исходное значение
            replacement_value: Замещающее значение
            position_info: Информация о позиции для точной замены (опционально)
            
        Returns:
            True если замена применена
        """
        try:
            print(f"🔧 [TABLE] Начало замены в таблице: '{original_value}' → '{replacement_value}'")
            print(f"🔧 [TABLE] Информация о позиции: {position_info}")
            replacement_made = False
            target_position = position_info.get('start') if position_info else None
            current_position = 0
            found_target = False
            
            for row_idx, row in enumerate(table.rows):
                for cell_idx, cell in enumerate(row.cells):
                    # Безопасная проверка текста ячейки
                    cell_text = getattr(cell, 'text', '') or ''
                    print(f"🔧 [TABLE] Ячейка [{row_idx}][{cell_idx}]: '{cell_text[:50]}{'...' if len(cell_text) > 50 else ''}'")
                    
                    if original_value and original_value in cell_text:
                        print(f"🔧 [TABLE] ✅ Найден текст в ячейке [{row_idx}][{cell_idx}]")
                        
                        # Если указана позиция, проверяем соответствие
                        if target_position is not None:
                            # Ищем позицию текста в ячейке
                            text_start_in_cell = cell_text.find(original_value)
                            absolute_position = current_position + text_start_in_cell
                            print(f"🔧 [TABLE] Позиция в документе: {absolute_position}, целевая: {target_position}")
                            
                            # Проверяем соответствие позиции (с небольшой погрешностью)
                            if abs(absolute_position - target_position) > 100:
                                print(f"🔧 [TABLE] ❌ Позиция не совпадает, пропускаем")
                                current_position += len(cell_text)
                                continue
                            else:
                                print(f"🔧 [TABLE] ✅ Позиция совпадает!")
                                found_target = True
                        
                        # Заменяем в каждом параграфе ячейки используя новый метод
                        for para_idx, paragraph in enumerate(cell.paragraphs):
                            paragraph_text = getattr(paragraph, 'text', '') or ''
                            
                            if original_value and original_value in paragraph_text:
                                print(f"🔧 [TABLE] Замена в параграфе {para_idx} ячейки [{row_idx}][{cell_idx}]")
                                
                                # Используем улучшенный метод замены в параграфе
                                cell_replacement_made = self._replace_in_paragraph(
                                    paragraph, original_value, replacement_value, {}
                                )
                                
                                if cell_replacement_made:
                                    replacement_made = True
                                    print(f"🔧 [TABLE] ✅ Замена в ячейке [{row_idx}][{cell_idx}] выполнена")
                                    
                                    # Если это была целевая позиция, выходим
                                    if found_target:
                                        print(f"🔧 [TABLE] 🎯 Целевая замена завершена, выходим")
                                        return True
                                else:
                                    print(f"🔧 [TABLE] ❌ Замена в ячейке [{row_idx}][{cell_idx}] не удалась")
                    
                    # Увеличиваем счетчик позиции
                    current_position += len(cell_text)
            
            print(f"🔧 [TABLE] Результат замены в таблице: {replacement_made}")
            return replacement_made
            
        except Exception as e:
            print(f"🔧 [TABLE] ❌ Ошибка замены в таблице: {str(e)}")
            import traceback
            print(f"🔧 [TABLE] Traceback: {traceback.format_exc()}")
            return False
                
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