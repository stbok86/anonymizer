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
        УСТАРЕЛО: Используйте _process_blocks_optimized для батчинга
        """
        try:
            payload = {
                "blocks": [
                    {
                        "content": text,
                        "block_id": "doc_block_1",
                        "block_type": "text"
                    }

            # ...existing code...
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
                print(f"[WARNING] NLP Service error: {response.status_code}")
                print(f"[WARNING] Response: {response.text}")
                return []
        except Exception as e:
            print(f"[WARNING] NLP Service unavailable: {str(e)}")
            return []
    
    def _deduplicate_blocks(self, blocks: List[Dict]) -> tuple:
        """
        ОПТИМИЗАЦИЯ 1: Группирует блоки по уникальному тексту для кэширования
        
        Args:
            blocks: Список блоков для обработки
            
        Returns:
            tuple: (unique_blocks, text_to_blocks_mapping)
        """
        text_to_blocks = {}
        
        for block in blocks:
            text = block.get('text', '').strip()
            if text:
                if text not in text_to_blocks:
                    text_to_blocks[text] = []
                text_to_blocks[text].append(block)
        
        # Создаём список уникальных блоков (берём первый из каждой группы)
        unique_blocks = [block_list[0] for block_list in text_to_blocks.values()]
        
        return unique_blocks, text_to_blocks
    
    def _process_blocks_batch(self, blocks: List[Dict], batch_size: int = 50) -> List[Dict]:
        """
        ОПТИМИЗАЦИЯ 2: Обрабатывает блоки батчами через NLP Service
        
        Args:
            blocks: Список блоков для обработки
            batch_size: Размер батча (по умолчанию 50)
            
        Returns:
            Список всех детекций с привязкой к блокам
        """
        all_matches = []
        
        # Разбиваем на батчи
        for i in range(0, len(blocks), batch_size):
            batch_blocks = blocks[i:i + batch_size]
            
            # Готовим payload для NLP Service
            nlp_payload = {
                "blocks": [
                    {
                        "content": block.get('text', ''),
                        "block_id": block['block_id'],
                        "block_type": block.get('type', 'text')
                    }
                    for block in batch_blocks
                    if block.get('text', '').strip()
                ],
                "options": {}
            }
            
            if not nlp_payload["blocks"]:
                continue
            
            try:
                # ОДИН HTTP запрос на весь батч
                response = requests.post(
                    f"{self.nlp_service_url}/analyze",
                    json=nlp_payload,
                    timeout=60
                )
                
                if response.status_code == 200:
                    result = response.json()
                    batch_detections = result.get('detections', [])
                    
                    # Создаём mapping block_id -> block для быстрого поиска
                    blocks_map = {b['block_id']: b for b in batch_blocks}
                    
                    # Привязываем детекции к блокам
                    for detection in batch_detections:
                        block_id = detection.get('block_id')
                        if block_id in blocks_map:
                            source_block = blocks_map[block_id]
                            all_matches.append({
                                'block_id': block_id,
                                'original_value': detection['original_value'],
                                'position': detection['position'],
                                'element': source_block.get('element'),
                                'category': detection['category'],
                                'confidence': detection['confidence'],
                                'source': 'nlp_service',
                                'method': detection['method']
                            })
                else:
                    print(f"[WARNING] NLP Service error for batch: {response.status_code}")
            except Exception as e:
                print(f"[WARNING] Error processing batch: {str(e)}")
                continue
        
        return all_matches
    
    def _process_blocks_optimized(self, blocks: List[Dict], batch_size: int = 50) -> List[Dict]:
        """
        ОПТИМИЗАЦИЯ КОМБО: Кэширование дубликатов + Батчинг HTTP запросов
        
        Args:
            blocks: Список всех блоков для обработки
            batch_size: Размер батча для HTTP запросов
            
        Returns:
            Список всех детекций для всех блоков (включая дубликаты)
        """
        import time
        start_time = time.time()
        
        # ШАГ 1: Дедупликация - находим уникальные тексты
        unique_blocks, text_to_blocks = self._deduplicate_blocks(blocks)
        
        blocks_with_text = [b for b in blocks if b.get('text', '').strip()]
        dedup_ratio = (1 - len(unique_blocks) / len(blocks_with_text)) * 100 if blocks_with_text else 0
        
        print(f"\n[OPTIMIZATION] Дедупликация:")
        print(f"   Всего блоков: {len(blocks)}")
        print(f"   С текстом: {len(blocks_with_text)}")
        print(f"   Уникальных: {len(unique_blocks)}")
        print(f"   Дубликатов: {len(blocks_with_text) - len(unique_blocks)} ({dedup_ratio:.1f}%)")
        
        # ШАГ 2: Батчинг - обрабатываем только уникальные блоки
        num_batches = (len(unique_blocks) + batch_size - 1) // batch_size
        print(f"\n[OPTIMIZATION] Батчинг:")
        print(f"   Batch size: {batch_size}")
        print(f"   Количество батчей: {num_batches}")
        print(f"   Было бы запросов БЕЗ оптимизации: {len(blocks_with_text)}")
        print(f"   Будет запросов С оптимизацией: {num_batches}")
        print(f"   Экономия HTTP запросов: {len(blocks_with_text) - num_batches} ({100*(1 - num_batches/len(blocks_with_text)):.1f}%)\n")
        
        unique_matches = self._process_blocks_batch(unique_blocks, batch_size)
        
        # ШАГ 3: Реплицирование - копируем детекции на дубликаты
        all_matches = []
        
        for match in unique_matches:
            # Находим исходный блок и его текст
            source_block_id = match['block_id']
            source_block = next((b for b in unique_blocks if b['block_id'] == source_block_id), None)
            
            if source_block:
                source_text = source_block.get('text', '').strip()
                
                # Реплицируем match для всех блоков с таким же текстом
                for duplicate_block in text_to_blocks.get(source_text, []):
                    match_copy = {
                        'block_id': duplicate_block['block_id'],      # УНИКАЛЬНЫЙ ID
                        'original_value': match['original_value'],
                        'position': match['position'],                # ОДИНАКОВАЯ позиция
                        'element': duplicate_block.get('element'),    # РАЗНАЯ ссылка на объект
                        'category': match['category'],
                        'confidence': match['confidence'],
                        'source': match['source'],
                        'method': match['method']
                    }
                    all_matches.append(match_copy)
        
        elapsed_time = time.time() - start_time
        print(f"[OPTIMIZATION] Обработка завершена за {elapsed_time:.2f}с")
        print(f"   Детекций найдено: {len(all_matches)}\n")
        
        return all_matches
        
    def anonymize_document(self, 
                          input_path: str, 
                          output_path: str,
                          excel_report_path: Optional[str] = None,
                          json_ledger_path: Optional[str] = None,
                          replacements_table: Optional[List[Dict]] = None,
                          selected_items: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Полный цикл анонимизации документа с генерацией отчетов
        
        Args:
            input_path: Путь к исходному документу
            output_path: Путь для сохранения анонимизированного документа
            excel_report_path: Путь для Excel отчета (опционально)
            json_ledger_path: Путь для JSON журнала (опционально)
            replacements_table: Предопределенная таблица замен (опционально)
            selected_items: Список выбранных пользователем элементов (обязателен в рабочем режиме)
            
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
                
                # 3.2: Поиск через NLP Service (ОПТИМИЗИРОВАННАЯ обработка)
                print(f"\n[NLP SERVICE] Анализ {len(blocks)} блоков с оптимизацией...")
                
                import time
                nlp_start = time.time()
                
                # ОПТИМИЗАЦИЯ: Используем кэширование дубликатов + батчинг
                nlp_matches = self._process_blocks_optimized(blocks, batch_size=50)
                
                nlp_elapsed = time.time() - nlp_start
                print(f"[NLP SERVICE] Завершено за {nlp_elapsed:.2f}с ({len(nlp_matches)} детекций)\n")
                
                
                # 3.3: Комбинируем результаты (приоритет NLP Service)
                # print(f"📊 Найдено совпадений: Rule Engine={len(rule_engine_matches)}, NLP Service={len(nlp_matches)}")
                
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
                
                # print(f"✅ Итого уникальных совпадений: {len(all_matches)}")
                
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
            
            # ЭТАП 3.5: Фильтрация по выбранным пользователем элементам
            if selected_items:
                # print(f"🎯 [USER_SELECTION] Применяем выбор пользователя: {len(selected_items)} элементов")
                
                # Создаем карту блоков для быстрого поиска
                blocks_map = {block['block_id']: block for block in blocks}
                
                # Подготавливаем отфильтрованный список замен
                filtered_matches = []
                skipped_items = []
                seen_replacements = set()  # Для дедупликации
                
                for item in selected_items:
                    block_id = item.get('block_id')
                    original_value = item.get('original_value', '')
                    position = item.get('position', {})
                    uuid_val = item.get('uuid', '')
                    
                    # Диагностика некорректных uuid
                    # if not uuid_val or str(uuid_val).strip().lower() == 'placeholder':
                    #     print(f"🚨 [BUG] Некорректный uuid для значения '{original_value}' (block_id={block_id}): '{uuid_val}'")
                    
                    # Создаем уникальный ключ для дедупликации
                    dedup_key = (block_id, original_value, position.get('start'), position.get('end'))
                    
                    if dedup_key in seen_replacements:
                        # print(f"🔄 [USER_SELECTION] Пропускаем дубликат: '{original_value}' в {block_id}")
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
                            'category': item.get('category', 'unknown')
                        }
                        filtered_matches.append(replacement)
                    else:
                        skipped_items.append(item)
                
                # print(f"🎯 [USER_SELECTION] Отобрано пользователем: {len(filtered_matches)} из {len(all_matches)} найденных")
                
                # Заменяем all_matches на отфильтрованный список
                all_matches = filtered_matches
            
            # ЭТАП 4: Применение замен с сохранением форматирования
            replacement_stats = self.formatter.apply_replacements_to_document(doc, all_matches)
            
            # 🎯 ВАЖНО: Получаем нормализованные замены с UUID для отчетов
            normalized_matches = replacement_stats.get('normalized_replacements', all_matches)
            
            # ЭТАП 5: Сохранение анонимизированного документа (текст)
            doc.save(output_path)
            
            # ЭТАП 5.5: Сквозная анонимизация для header элементов (выбранных пользователем)
            if selected_items:
                header_items = [item for item in selected_items if 'header' in (item.get('block_id') or '').lower()]
                if header_items:
                    
                    from uuid_mapper import UUIDMapper
                    uuid_mapper = self.formatter.uuid_mapper if hasattr(self.formatter, 'uuid_mapper') else UUIDMapper()
                    
                    metadata_items = []
                    for h in header_items:
                        uuid_val = h.get('uuid')
                        if not uuid_val or str(uuid_val).strip().lower() == 'placeholder':
                            uuid_val = uuid_mapper.get_uuid_for_text(h['original_value'], h.get('category', 'unknown'))
                        for section in ['core', 'app', 'custom']:
                            metadata_items.append({
                                'original_value': h['original_value'],
                                'uuid': uuid_val,
                                'category': h.get('category', 'unknown'),
                                'metadata_section': section,
                            })
                    
                    from docx_metadata_handler import DocxMetadataHandler
                    metadata_handler = DocxMetadataHandler(output_path)
                    metadata_handler.anonymize_metadata_in_docx(output_path, output_path, metadata_items)
            
            # ЭТАП 6: Анонимизация метаданных в docProps/core.xml
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
                    # Генерируем UUID для метаданных если их нет
                    for i, m in enumerate(sensitive_metadata):
                        existing_uuid = m.get('uuid')
                        if not existing_uuid:
                            m['uuid'] = uuid_mapper.get_uuid_for_text(m['original_value'], m.get('category', 'unknown'))
                        # else: pass
                    
                    # Анонимизируем метаданные в docx
                    metadata_handler.anonymize_metadata_in_docx(output_path, output_path, sensitive_metadata)
                    
                    # 🎯 ВАЖНО: Добавляем метаданные в список замен для отчета
                    # Фильтрация: не добавляем если все partial_matches уже есть в документе
                    
                    doc_values = set(m.get('original_value', '') for m in normalized_matches)
                    
                    for meta in sensitive_metadata:
                        partial_matches = meta.get('partial_matches', [])
                        
                        if partial_matches:
                            # Проверяем: есть ли хотя бы один partial_match, которого НЕТ в документе
                            has_new_value = any(pm.get('partial_match', '') not in doc_values for pm in partial_matches)
                            
                            if has_new_value:
                                # Есть новые значения — добавляем запись метаданных
                                normalized_matches.append(meta)
                            # else:
                                # Все partial_matches уже в документе — пропускаем
                        else:
                            # Для точных совпадений — добавляем только если нет в документе
                            if meta.get('original_value', '') not in doc_values:
                                normalized_matches.append(meta)
                            # else: pass
                # else: pass
                    
            except Exception as e:
                import traceback
                traceback.print_exc()
            
            # ЭТАП 7: Генерация отчетов
            results = {
                'status': 'success',
                'message': 'Документ успешно анонимизирован',
                'replacement_stats': replacement_stats,
                'statistics': replacement_stats,  # Для обратной совместимости
                'total_blocks': len(blocks),
                'matches_count': len(all_matches),
                'detections_found': normalized_matches,  # Для тестов и UI
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
            
            # print(f"📝 [EXCEL_REPORT] Генерация отчета для {len(matches)} замен")
            # print(f"📝 [EXCEL_REPORT] Первые 3 замены:")
            # for i, match in enumerate(matches[:3], 1):
            #     print(f"  {i}. original_value: '{match.get('original_value', 'N/A')[:50]}'")
            #     print(f"     uuid: '{match.get('uuid', 'N/A')}'")
            #     print(f"     category: '{match.get('category', 'N/A')}'")
            #     print(f"     source: '{match.get('source', 'N/A')}'")
            #     print(f"     block_id (top level): '{match.get('block_id', 'N/A')}'")
            #     position = match.get('position', {})
            #     block_id = position.get('block_id', 'N/A') if isinstance(position, dict) else 'N/A'
            #     print(f"     position.block_id: '{block_id}'")
            
            for i, match in enumerate(matches, 1):
                original_value = match.get('original_value', '')
                category = match.get('category', 'unknown')
                
                # Используем UUID который уже был сгенерирован в formatter_applier
                # Если UUID нет в match, генерируем новый (резервный вариант)
                uuid_for_replacement = match.get('uuid')
                if not uuid_for_replacement:
                    uuid_for_replacement = self.formatter.uuid_mapper.get_uuid_for_text(original_value, category)
                
                # Получаем block_id - сначала проверяем верхний уровень, потом position
                block_id = match.get('block_id', '')
                if not block_id:
                    position = match.get('position', {})
                    block_id = position.get('block_id', '') if isinstance(position, dict) else ''
                
                report_data.append({
                    '№': i,
                    'Исходные данные': original_value,
                    'Замена (идентификатор)': uuid_for_replacement,
                    'ID блока документа': block_id
                })
            
            # Создаем DataFrame с правильными колонками
            df = pd.DataFrame(report_data)

            # Удалена очистка строк и перекодировка: сохраняем строки в Unicode для корректного отображения кириллицы и других символов
            # df = df.applymap(clean_excel_string)

            # Сохраняем в Excel
            with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Замены', index=False)
                # Настраиваем форматирование колонок
                worksheet = writer.sheets['Замены']
                worksheet.column_dimensions['A'].width = 5      # №
                worksheet.column_dimensions['B'].width = 60     # Исходные данные (было 40, увеличено в 1.5 раза)
                worksheet.column_dimensions['C'].width = 45     # Замена (идентификатор)
                worksheet.column_dimensions['D'].width = 30     # ID блока документа (было 20, увеличено в 1.5 раза)
            # print(f"✅ Excel отчет сохранен: {excel_path} ({len(report_data)} записей)")
            return True
            
        except Exception as e:
            # print(f"❌ Ошибка генерации Excel отчета: {str(e)}")
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