"""
Полный анонимизатор документов - координирует весь процесс обработки
"""

import os
import uuid
import json
import requests
import pandas as pd
from typing import List, Dict, Any, Optional
from docx import Document

from block_builder import BlockBuilder
from rule_adapter import RuleEngineAdapter
from formatter_applier import FormatterApplier


class FullAnonymizer:
    def __init__(self, patterns_path: str = None, nlp_service_url: str = "http://localhost:8006"):
        """
        Инициализация полного анонимизатора
        """
        self.patterns_path = patterns_path or "patterns/sensitive_patterns.xlsx"
        self.nlp_service_url = nlp_service_url
        self.block_builder = BlockBuilder()
        self.rule_engine = RuleEngineAdapter(self.patterns_path)
        self.formatter = FormatterApplier(highlight_replacements=True)
        
    def _call_nlp_service(self, text: str) -> List[Dict[str, Any]]:
        """
        Вызывает NLP Service для поиска чувствительных данных
        """
        try:
            payload = {
                "blocks": [
                    {
                        "content": text,
                        "block_id": "doc_block_1",
                        "block_type": "text"
                    }
                ],
                "options": {}
            }
            
            response = requests.post(
                f"{self.nlp_service_url}/analyze",
                json=payload,
                timeout=30
            )
            if response.status_code == 200:
                result = response.json()
                return result.get('detections', [])
            else:
                print(f"⚠️  NLP Service error: {response.status_code}")
                print(f"⚠️  Response: {response.text}")
                return []
        except Exception as e:
            print(f"⚠️  NLP Service unavailable: {str(e)}")
            return []
        
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
                # 3.1: Поиск через Rule Engine (старые regex паттерны)
                processed_blocks = self.rule_engine.apply_rules_to_blocks(blocks)
                rule_engine_matches = []
                
                for block in processed_blocks:
                    if 'sensitive_patterns' in block:
                        for pattern in block['sensitive_patterns']:
                            match = {
                                'block_id': block['block_id'],
                                'original_value': pattern['original_value'],
                                'position': pattern['position'],
                                'element': block.get('element'),
                                'category': pattern['category'],
                                'confidence': pattern.get('confidence', 1.0),
                                'source': 'rule_engine',
                                'method': 'regex'
                            }
                            rule_engine_matches.append(match)
                
                # 3.2: Поиск через NLP Service (поблочная обработка)
                nlp_matches = []
                
                print(f"🤖 Вызываем NLP Service для анализа {len(blocks)} блоков")
                
                # Обрабатываем каждый блок отдельно через NLP Service
                for block in blocks:
                    block_text = block.get('text', block.get('content', ''))
                    if not block_text.strip():
                        continue
                    
                    # Вызываем NLP Service для ОДНОГО блока
                    block_detections = self._call_nlp_service(block_text)
                    
                    # Добавляем детекции с привязкой к блоку
                    for detection in block_detections:
                        match = {
                            'block_id': block['block_id'],
                            'original_value': detection['original_value'],
                            'position': detection['position'],  # Уже относительно блока
                            'element': block.get('element'),
                            'category': detection['category'],
                            'confidence': detection['confidence'],
                            'source': 'nlp_service',
                            'method': detection['method']
                        }
                        nlp_matches.append(match)
                
                print(f"🎯 NLP Service нашел {len(nlp_matches)} детекций во всех блоках")
                
                # 3.3: Комбинируем результаты (приоритет NLP Service)
                print(f"📊 Найдено совпадений: Rule Engine={len(rule_engine_matches)}, NLP Service={len(nlp_matches)}")
                
                # Начинаем с NLP Service (более точные)
                all_matches = nlp_matches.copy()
                
                # Добавляем Rule Engine детекции, которые не пересекаются с NLP
                for re_match in rule_engine_matches:
                    is_duplicate = False
                    for nlp_match in nlp_matches:
                        if (re_match['block_id'] == nlp_match['block_id'] and
                            self._positions_overlap(re_match['position'], nlp_match['position'])):
                            is_duplicate = True
                            break
                    
                    if not is_duplicate:
                        all_matches.append(re_match)
                
                print(f"✅ Итого уникальных совпадений: {len(all_matches)}")
                
                # --- ДОБАВЛЯЕМ АНАЛИЗ И АНОНИМИЗАЦИЮ МЕТАДАННЫХ ---
                # ВРЕМЕННО ОТКЛЮЧЕНО из-за отсутствия метода find_patterns_in_text
                metadata_matches = []
                # from docx_metadata_handler import DocxMetadataHandler
                # metadata_handler = DocxMetadataHandler(input_path)
                # metadata = metadata_handler.extract_metadata()
                # # Собираем все значения метаданных в список для анализа
                # for section_name, section in metadata.items():
                #     if isinstance(section, dict):
                #         for value in section.values():
                #             if value:
                #                 # TODO: Нужно реализовать поиск паттернов через NLP Service
                #                 pass
                # --- КОНЕЦ ДОБАВЛЕНИЯ АНАЛИЗА МЕТАДАННЫХ ---
                
            else:
                # Используем предоставленную таблицу замен
                all_matches = replacements_table
                processed_blocks = blocks
            
            # ЭТАП 4: Применение замен с сохранением форматирования
            replacement_stats = self.formatter.apply_replacements_to_document(doc, all_matches)
            
            # 🎯 ВАЖНО: Получаем нормализованные замены с UUID для отчетов
            normalized_matches = replacement_stats.get('normalized_replacements', all_matches)
            
            # ЭТАП 5: Сохранение анонимизированного документа (текст)
            doc.save(output_path)
            
            # ЭТАП 6: Анонимизация метаданных в docProps/core.xml
            print(f"\n🔧 [METADATA] Начинаем анонимизацию метаданных...")
            try:
                from docx_metadata_handler import DocxMetadataHandler
                from uuid_mapper import UUIDMapper
                
                uuid_mapper = self.formatter.uuid_mapper if hasattr(self.formatter, 'uuid_mapper') else UUIDMapper()
                metadata_handler = DocxMetadataHandler(output_path)
                
                # Сначала извлекаем метаданные
                metadata_handler.extract_metadata()
                
                # Ищем совпадения в метаданных используя normalized_matches (с UUID)
                sensitive_metadata = metadata_handler.find_sensitive_metadata(normalized_matches)
                
                if sensitive_metadata:
                    print(f"🔧 [METADATA] Найдено чувствительных данных в метаданных: {len(sensitive_metadata)}")
                    # Генерируем UUID для метаданных если их нет
                    for i, m in enumerate(sensitive_metadata):
                        existing_uuid = m.get('uuid')
                        if not existing_uuid:
                            print(f"⚠️ [METADATA] UUID отсутствует для метаданных #{i}: '{m.get('original_value', 'N/A')[:50]}', partial_match: '{m.get('partial_match', 'N/A')}'")
                            m['uuid'] = uuid_mapper.get_uuid_for_text(m['original_value'], m.get('category', 'unknown'))
                        else:
                            print(f"✅ [METADATA] UUID уже есть для метаданных #{i}: '{m.get('original_value', 'N/A')[:30]}...' → '{existing_uuid}'")
                    
                    # Анонимизируем метаданные в docx
                    metadata_handler.anonymize_metadata_in_docx(output_path, output_path, sensitive_metadata)
                    print(f"🔧 [METADATA] ✅ Метаданные анонимизированы")
                    
                    # 🎯 ВАЖНО: Добавляем метаданные в список замен для отчета
                    # Но сначала удаляем дубликаты из документа
                    print(f"🔧 [DEDUP] Удаление дубликатов перед добавлением метаданных...")
                    print(f"🔧 [DEDUP] До: {len(normalized_matches)} записей в normalized_matches")
                    
                    # Собираем ВСЕ значения из метаданных (и partial_match, и точные совпадения)
                    metadata_values = set()
                    for m in sensitive_metadata:
                        # Для частичных совпадений берем partial_match
                        partial = m.get('partial_match')
                        if partial:
                            metadata_values.add(partial)
                        # Для точных совпадений берем original_value
                        else:
                            metadata_values.add(m.get('original_value', ''))
                    
                    print(f"🔧 [DEDUP] Найдено {len(metadata_values)} уникальных значений в метаданных")
                    
                    # Удаляем из normalized_matches записи, у которых original_value есть в метаданных
                    # И source НЕ metadata_* (т.е. записи из документа)
                    filtered_matches = []
                    removed_count = 0
                    for match in normalized_matches:
                        orig_val = match.get('original_value', '')
                        source = match.get('source', '')
                        
                        # Если это запись из документа И её значение есть в метаданных — удаляем
                        if not source.startswith('metadata_') and orig_val in metadata_values:
                            print(f"🔧 [DEDUP] ❌ Удаляем дубликат: '{orig_val}' (source: {source})")
                            removed_count += 1
                        else:
                            filtered_matches.append(match)
                    
                    normalized_matches = filtered_matches
                    print(f"🔧 [DEDUP] После удаления дубликатов: {len(normalized_matches)} записей (удалено {removed_count})")
                    
                    # Теперь добавляем метаданные
                    normalized_matches.extend(sensitive_metadata)
                    print(f"🔧 [DEDUP] После добавления метаданных: {len(normalized_matches)} записей")
                else:
                    print(f"🔧 [METADATA] ℹ️ Чувствительных данных в метаданных не найдено")
                    
            except Exception as e:
                print(f"🔧 [METADATA] ⚠️ Ошибка при анонимизации метаданных: {str(e)}")
                import traceback
                traceback.print_exc()
            
            # ЭТАП 7: Генерация отчетов
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
                excel_generated = self._generate_excel_report(processed_blocks, normalized_matches, excel_report_path)
                results['excel_report_path'] = excel_report_path
                results['excel_report_generated'] = excel_generated
            # Генерация JSON журнала
            if json_ledger_path:
                ledger_data = self._generate_json_ledger(normalized_matches, replacement_stats)
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
            print(f"🔧 [FULL_ANONYMIZER] Получено элементов для замены: {len(selected_items)}")
            for i, item in enumerate(selected_items[:5]):  # Показываем первые 5
                print(f"🔧 [FULL_ANONYMIZER] Элемент {i+1}: '{item.get('original_value', 'N/A')}' в блоке {item.get('block_id', 'N/A')}")
            if len(selected_items) > 5:
                print(f"🔧 [FULL_ANONYMIZER] ... и еще {len(selected_items) - 5} элементов")
            
            # Загружаем документ
            doc = Document(input_path)
            
            # Извлекаем блоки для получения элементов документа
            blocks = self.block_builder.build_blocks(doc)
            
            # Создаем карту блоков для быстрого поиска
            blocks_map = {block['block_id']: block for block in blocks}
            print(f"🗂️  [FULL_ANONYMIZER] Создана карта блоков: {list(blocks_map.keys())}")
            
            # Подготавливаем замены на основе выбранных элементов
            replacements_for_formatting = []
            skipped_items = []
            seen_replacements = set()  # Для дедупликации
            
            for item in selected_items:
                block_id = item.get('block_id')
                original_value = item.get('original_value', '')
                position = item.get('position', {})
                uuid_val = item.get('uuid', '')

                # Диагностика некорректных uuid
                if not uuid_val or str(uuid_val).strip().lower() == 'placeholder':
                    print(f"🚨 [BUG] Некорректный uuid для значения '{original_value}' (block_id={block_id}): '{uuid_val}'")

                # Создаем уникальный ключ для дедупликации
                dedup_key = (block_id, original_value, position.get('start'), position.get('end'))

                if dedup_key in seen_replacements:
                    print(f"🔄 [FULL_ANONYMIZER] Пропускаем дубликат: '{original_value}' в {block_id}")
                    continue

                seen_replacements.add(dedup_key)

                if block_id in blocks_map:
                    block = blocks_map[block_id]
                    replacement = {
                        'block_id': block_id,
                        'original_value': original_value,
                        'uuid': uuid_val,
                        'position': position,
                        'element': block.get('element'),
                        'category': item['category']
                    }
                    replacements_for_formatting.append(replacement)
                else:
                    skipped_items.append(item)
                    print(f"⚠️  [FULL_ANONYMIZER] Пропущен элемент - блок '{block_id}' не найден: '{original_value}'")
            
            print(f"🔧 [FULL_ANONYMIZER] Подготовлено замен для FormatterApplier: {len(replacements_for_formatting)}")
            print(f"⚠️  [FULL_ANONYMIZER] Пропущено элементов: {len(skipped_items)}")
            if skipped_items:
                print(f"⚠️  [FULL_ANONYMIZER] Доступные block_id: {list(blocks_map.keys())}")

            # Применяем замены
            replacement_stats = self.formatter.apply_replacements_to_document(doc, replacements_for_formatting)
            doc.save(output_path)

            # --- СКВОЗНАЯ АНОНИМИЗАЦИЯ ДЛЯ HEADER ---
            # Для каждого выбранного блока типа header делаем замену и в метаданных
            header_items = [item for item in selected_items if 'header' in (item.get('block_id') or '').lower()]
            if header_items:
                print(f"🔧 [FULL_ANONYMIZER] Найдено header-элементов для сквозной анонимизации: {len(header_items)}")
                # Готовим список для метаданных: для каждого header original_value и uuid (если нет - генерируем)
                from uuid_mapper import UUIDMapper
                uuid_mapper = self.formatter.uuid_mapper if hasattr(self.formatter, 'uuid_mapper') else UUIDMapper()
                metadata_items = []
                for h in header_items:
                    uuid_val = h.get('uuid')
                    if not uuid_val or str(uuid_val).strip().lower() == 'placeholder':
                        uuid_val = uuid_mapper.get_uuid_for_text(h['original_value'], h['category'])
                    for section in ['core', 'app', 'custom']:
                        metadata_items.append({
                            'original_value': h['original_value'],
                            'uuid': uuid_val,
                            'category': h['category'],
                            'metadata_section': section,
                        })
                from docx_metadata_handler import DocxMetadataHandler
                metadata_handler = DocxMetadataHandler(output_path)
                metadata_handler.anonymize_metadata_in_docx(output_path, output_path, metadata_items)

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

    def _generate_excel_report(self, processed_blocks: List[Dict], matches: List[Dict], excel_path: str) -> bool:
        """
        Генерация Excel отчета с детерминистичными UUID
        
        Args:
            processed_blocks: Обработанные блоки документа
            matches: Список найденных совпадений
            excel_path: Путь для сохранения Excel файла
            
        Returns:
            True если успешно, False при ошибке
        """
        try:
            report_data = []
            
            print(f"📝 [EXCEL_REPORT] Генерация отчета для {len(matches)} замен")
            print(f"📝 [EXCEL_REPORT] Первые 3 замены:")
            for i, match in enumerate(matches[:3], 1):
                print(f"  {i}. original_value: '{match.get('original_value', 'N/A')[:50]}'")
                print(f"     uuid: '{match.get('uuid', 'N/A')}'")
                print(f"     category: '{match.get('category', 'N/A')}'")
            
            for i, match in enumerate(matches, 1):
                original_value = match.get('original_value', '')
                category = match.get('category', 'unknown')
                
                # Используем UUID который уже был сгенерирован в formatter_applier
                # Если UUID нет в match, генерируем новый (резервный вариант)
                uuid_for_replacement = match.get('uuid')
                if not uuid_for_replacement:
                    print(f"⚠️ [EXCEL_REPORT] UUID отсутствует для '{original_value[:50]}', генерируем новый")
                    uuid_for_replacement = self.formatter.uuid_mapper.get_uuid_for_text(original_value, category)
                
                # Определяем расположение замены
                # Если source начинается с metadata_ — это метаданные
                source = match.get('source', '')
                location = 'Метаданные' if source.startswith('metadata_') else 'Документ'
                
                report_data.append({
                    '№': i,
                    'Исходные данные': original_value,
                    'Замена (идентификатор)': uuid_for_replacement,
                    'Расположение': location
                })
            
            # Создаем DataFrame с правильными колонками
            df = pd.DataFrame(report_data)
            
            # Сохраняем в Excel
            with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Замены', index=False)
                
                # Настраиваем форматирование колонок
                worksheet = writer.sheets['Замены']
                worksheet.column_dimensions['A'].width = 5
                worksheet.column_dimensions['B'].width = 40
                worksheet.column_dimensions['C'].width = 45
                worksheet.column_dimensions['D'].width = 15  # Колонка "Расположение"
            
            print(f"✅ Excel отчет сохранен: {excel_path} ({len(report_data)} записей)")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка генерации Excel отчета: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

    def _generate_json_ledger(self, matches: List[Dict], stats: Dict) -> Dict:
        """Генерация JSON журнала замен с детерминистичными UUID"""
        replacements_list = []
        
        for match in matches:
            original_value = match.get('original_value', '')
            category = match.get('category', 'unknown')
            
            # Используем UUID который уже был сгенерирован в formatter_applier
            # Если UUID нет в match, генерируем новый (резервный вариант)
            uuid_for_replacement = match.get('uuid')
            if not uuid_for_replacement:
                uuid_for_replacement = self.formatter.uuid_mapper.get_uuid_for_text(original_value, category)
            
            replacements_list.append({
                'uuid': uuid_for_replacement,
                'category': category,
                'original_value': original_value,
                'block_id': match.get('block_id', ''),
                'position': match.get('position', {}),
                'confidence': match.get('confidence', 1.0)
            })
        
        return {
            'timestamp': pd.Timestamp.now().isoformat(),
            'total_matches': len(matches),
            'replacement_statistics': stats,
            'replacements': replacements_list
        }
    
    def _positions_overlap(self, pos1: Dict, pos2: Dict, threshold: float = 0.5) -> bool:
        """
        Проверяет, перекрываются ли две позиции
        
        Args:
            pos1, pos2: Позиции с ключами 'start' и 'end'
            threshold: Порог перекрытия для считания дубликатом
            
        Returns:
            True если позиции перекрываются
        """
        start1 = pos1.get('start', 0)
        end1 = pos1.get('end', 0)
        start2 = pos2.get('start', 0)  
        end2 = pos2.get('end', 0)
        
        overlap_start = max(start1, start2)
        overlap_end = min(end1, end2)
        
        if overlap_start >= overlap_end:
            return False
        
        overlap_length = overlap_end - overlap_start
        min_length = min(end1 - start1, end2 - start2)
        
        return (overlap_length / min_length) >= threshold if min_length > 0 else False