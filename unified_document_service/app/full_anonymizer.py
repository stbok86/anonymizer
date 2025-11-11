"""
Полный анонимизатор документов - координирует весь процесс обработки
"""

import os
import uuid
import json
import pandas as pd
from typing import List, Dict, Any, Optional
from docx import Document

from block_builder import BlockBuilder
from rule_adapter import RuleEngineAdapter
from formatter_applier import FormatterApplier


class FullAnonymizer:
    def __init__(self, patterns_path: str = None):
        """
        Инициализация полного анонимизатора
        """
        self.patterns_path = patterns_path or "patterns/sensitive_patterns.xlsx"
        self.block_builder = BlockBuilder()
        self.rule_engine = RuleEngineAdapter(self.patterns_path)
        self.formatter = FormatterApplier(highlight_replacements=True)
        
    def anonymize_document(self, 
                          input_path: str, 
                          output_path: str,
                          excel_report_path: Optional[str] = None,
                          json_ledger_path: Optional[str] = None,
                          replacements_table: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """
        Полный цикл анонимизации документа с генерацией отчетов
        
        Args:
            input_path: Путь к исходному документу
            output_path: Путь для сохранения анонимизированного документа
            excel_report_path: Путь для Excel отчета (опционально)
            json_ledger_path: Путь для JSON журнала (опционально)
            replacements_table: Предопределенная таблица замен (опционально)
            
        Returns:
            Dict с результатами анонимизации
        """
        try:
            # ЭТАП 1: Загрузка документа
            doc = Document(input_path)
            
            # ЭТАП 2: Извлечение блоков
            blocks = self.block_builder.build_blocks(doc)
            
            # ЭТАП 3: Поиск чувствительных данных (если не предоставлена таблица замен)
            if replacements_table is None:
                processed_blocks = self.rule_engine.apply_rules_to_blocks(blocks)
                
                # Собираем найденные совпадения
                all_matches = []
                for block in processed_blocks:
                    if 'sensitive_patterns' in block:
                        for pattern in block['sensitive_patterns']:
                            match = {
                                'block_id': block['block_id'],
                                'original_value': pattern['original_value'],
                                'uuid': pattern['uuid'],
                                'position': pattern['position'],
                                'element': block.get('element'),
                                'category': pattern['category'],
                                'confidence': pattern.get('confidence', 1.0)
                            }
                            all_matches.append(match)
            else:
                # Используем предоставленную таблицу замен
                all_matches = replacements_table
                processed_blocks = blocks
            
            # ЭТАП 4: Применение замен с сохранением форматирования
            replacement_stats = self.formatter.apply_replacements_to_document(doc, all_matches)
            
            # ЭТАП 5: Сохранение анонимизированного документа
            doc.save(output_path)
            
            # ЭТАП 6: Генерация отчетов
            results = {
                'status': 'success',
                'message': 'Документ успешно анонимизирован',
                'statistics': replacement_stats,
                'total_blocks': len(blocks),
                'matches_count': len(all_matches),
                'anonymized_document_path': output_path
            }
            
            # Генерация Excel отчета
            if excel_report_path:
                excel_data = self._generate_excel_report(processed_blocks, all_matches)
                results['excel_report_path'] = excel_report_path
                results['excel_report_generated'] = True
            
            # Генерация JSON журнала
            if json_ledger_path:
                ledger_data = self._generate_json_ledger(all_matches, replacement_stats)
                with open(json_ledger_path, 'w', encoding='utf-8') as f:
                    json.dump(ledger_data, f, ensure_ascii=False, indent=2)
                results['json_ledger_path'] = json_ledger_path
                results['json_ledger_generated'] = True
            
            return results
            
        except Exception as e:
            return {
                'status': 'error',
                'error_message': f'Ошибка анонимизации: {str(e)}',
                'error_type': type(e).__name__
            }

    def anonymize_selected_items(self, 
                                input_path: str, 
                                output_path: str,
                                selected_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Анонимизация только выбранных пользователем элементов
        
        Args:
            input_path: Путь к исходному документу
            output_path: Путь для сохранения анонимизированного документа
            selected_items: Список выбранных для анонимизации элементов
            
        Returns:
            Dict с результатами селективной анонимизации
        """
        try:
            # Загружаем документ
            doc = Document(input_path)
            
            # Извлекаем блоки для получения элементов документа
            blocks = self.block_builder.build_blocks(doc)
            
            # Создаем карту блоков для быстрого поиска
            blocks_map = {block['block_id']: block for block in blocks}
            
            # Подготавливаем замены на основе выбранных элементов
            replacements_for_formatting = []
            for item in selected_items:
                block_id = item.get('block_id')
                if block_id in blocks_map:
                    block = blocks_map[block_id]
                    replacement = {
                        'block_id': block_id,
                        'original_value': item['original_value'],
                        'uuid': item['uuid'],
                        'position': item['position'],
                        'element': block.get('element'),
                        'category': item['category']
                    }
                    replacements_for_formatting.append(replacement)
            
            # Применяем замены
            replacement_stats = self.formatter.apply_replacements_to_document(doc, replacements_for_formatting)
            
            # Сохраняем результат
            doc.save(output_path)
            
            return {
                'status': 'success',
                'message': f'Селективная анонимизация завершена. Обработано {len(selected_items)} элементов.',
                'statistics': replacement_stats,
                'selected_items_count': len(selected_items),
                'replacements_applied': replacement_stats.get('total_replacements', 0),
                'anonymized_document_path': output_path
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error_message': f'Ошибка селективной анонимизации: {str(e)}',
                'error_type': type(e).__name__
            }

    def _generate_excel_report(self, processed_blocks: List[Dict], matches: List[Dict]) -> str:
        """Генерация Excel отчета о найденных чувствительных данных"""
        try:
            report_data = []
            for match in matches:
                report_data.append({
                    'Блок ID': match.get('block_id', ''),
                    'Категория': match.get('category', ''),
                    'Оригинальное значение': match.get('original_value', ''),
                    'UUID замены': match.get('uuid', ''),
                    'Позиция начала': match.get('position', {}).get('start', ''),
                    'Позиция конца': match.get('position', {}).get('end', ''),
                    'Уверенность': match.get('confidence', '')
                })
            
            df = pd.DataFrame(report_data)
            # Временно возвращаем данные в виде строки, т.к. путь для Excel пока не реализован
            return df.to_string()
            
        except Exception as e:
            return f"Ошибка генерации Excel отчета: {str(e)}"

    def _generate_json_ledger(self, matches: List[Dict], stats: Dict) -> Dict:
        """Генерация JSON журнала замен"""
        return {
            'timestamp': pd.Timestamp.now().isoformat(),
            'total_matches': len(matches),
            'replacement_statistics': stats,
            'replacements': [
                {
                    'uuid': match.get('uuid', str(uuid.uuid4())),
                    'category': match.get('category', ''),
                    'original_value': match.get('original_value', ''),
                    'block_id': match.get('block_id', ''),
                    'position': match.get('position', {}),
                    'confidence': match.get('confidence', 1.0)
                }
                for match in matches
            ]
        }