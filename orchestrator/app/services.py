"""
Сервисы для параллельной обработки документов в Orchestrator

Этап 2: Параллелизация Rule Engine + NLP Service
"""
import asyncio
import httpx
import logging
from typing import List, Dict, Any, Optional
import time

logger = logging.getLogger(__name__)

class ParallelAnalyzer:
    """
    Параллельный анализатор документов
    
    Настоящая параллелизация:
    1. Парсинг документа → блоки
    2. ПАРАЛЛЕЛЬНО: Rule Engine + NLP Service (отдельные эндпоинты)
    3. Объединение результатов
    """
    
    def __init__(
        self,
        unified_service_url: str,
        nlp_service_url: str,
        rule_engine_url: str
    ):
        self.unified_service_url = unified_service_url
        self.nlp_service_url = nlp_service_url
        self.rule_engine_url = rule_engine_url
    
    async def analyze_document_parallel(
        self,
        file_content: bytes,
        filename: str,
        patterns_file: str = "patterns/sensitive_patterns.xlsx"
    ) -> Dict[str, Any]:
        """
        Параллельный анализ документа
        
        Шаги:
        1. Парсинг документа → блоки (Unified Service /parse_document)
        2. ПАРАЛЛЕЛЬНО: 
           - Rule Engine анализ (Unified Service /analyze_rule_engine)
           - NLP анализ (Unified Service /analyze_nlp)
        3. Объединение результатов
        
        Args:
            file_content: Содержимое DOCX файла
            filename: Имя файла
            patterns_file: Путь к файлу паттернов
        
        Returns:
            Dict с found_items и метриками производительности
        """
        start_time = time.time()
        
        # ЭТАП 1: Парсинг документа (последовательно)
        logger.info("[PARALLEL] Этап 1: Парсинг документа...")
        parse_start = time.time()
        
        blocks = await self._parse_document(file_content, filename)
        
        parse_time = time.time() - parse_start
        logger.info(f"[PARALLEL] Парсинг завершён: {len(blocks)} блоков за {parse_time:.2f}s")
        
        if not blocks:
            logger.warning("⚠️ [PARALLEL] Нет блоков для анализа")
            return {
                "success": True,
                "found_items": [],
                "total_items": 0,
                "performance_metrics": {
                    "total_time_seconds": round(time.time() - start_time, 2),
                    "parse_time_seconds": round(parse_time, 2),
                    "parallel_processing_time_seconds": 0,
                    "blocks_processed": 0,
                    "rule_engine_items": 0,
                    "nlp_items": 0
                }
            }
        
        # ЭТАП 2: ПАРАЛЛЕЛЬНАЯ обработка Rule Engine + NLP
        logger.info(f"[PARALLEL] Этап 2: Параллельная обработка {len(blocks)} блоков...")
        parallel_start = time.time()
        
        # Запускаем ОБА сервиса параллельно через новые эндпоинты
        rule_task = self._process_rule_engine(blocks, patterns_file)
        nlp_task = self._process_nlp_service(blocks)
        
        # Ждём завершения ОБОИХ задач
        results = await asyncio.gather(
            rule_task,
            nlp_task,
            return_exceptions=True  # Не падаем если одна задача упала
        )
        
        parallel_time = time.time() - parallel_start
        logger.info(f"[PARALLEL] Параллельная обработка завершена за {parallel_time:.2f}s")
        
        # Обрабатываем результаты
        rule_results = results[0] if not isinstance(results[0], Exception) else []
        nlp_results = results[1] if not isinstance(results[1], Exception) else []
        
        if isinstance(results[0], Exception):
            logger.error(f"❌ [PARALLEL] Rule Engine error: {results[0]}")
        if isinstance(results[1], Exception):
            logger.error(f"❌ [PARALLEL] NLP Service error: {results[1]}")
        
        # ЭТАП 3: Объединение результатов
        all_items = rule_results + nlp_results
        
        total_time = time.time() - start_time
        
        logger.info(f"[PARALLEL] Итого: Rule={len(rule_results)}, NLP={len(nlp_results)}, Total={len(all_items)}")
        logger.info(f"[PARALLEL] Общее время: {total_time:.2f}s (парсинг: {parse_time:.2f}s, параллельная обработка: {parallel_time:.2f}s)")
        
        return {
            "success": True,
            "found_items": all_items,
            "total_items": len(all_items),
            "performance_metrics": {
                "total_time_seconds": round(total_time, 2),
                "parse_time_seconds": round(parse_time, 2),
                "parallel_processing_time_seconds": round(parallel_time, 2),
                "blocks_processed": len(blocks),
                "rule_engine_items": len(rule_results),
                "nlp_items": len(nlp_results),
                "speedup_estimate": f"{round(parse_time / parallel_time, 1)}x faster than sequential" if parallel_time > 0 else "N/A"
            },
            "orchestrator_metadata": {
                "version": "2.0.0",
                "mode": "parallel_processing",
                "etap": 2
            }
        }
    
    async def _parse_document(
        self,
        file_content: bytes,
        filename: str
    ) -> List[Dict[str, Any]]:
        """
        Парсинг документа через Unified Service /parse_document
        
        Returns:
            List of blocks (без element)
        """
        try:
            files = {
                'file': (filename, file_content, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')
            }
            
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.unified_service_url}/parse_document",
                    files=files
                )
            
            if response.status_code == 200:
                result = response.json()
                blocks = result.get('blocks', [])
                logger.info(f"[PARSE] Получено {len(blocks)} блоков от Unified Service")
                return blocks
            else:
                logger.error(f"❌ [PARSE] Unified Service /parse_document error: {response.status_code} - {response.text}")
                return []
        
        except Exception as e:
            logger.error(f"💥 [PARSE] Exception: {e}")
            return []
    
    async def _process_rule_engine(
        self,
        blocks: List[Dict[str, Any]],
        patterns_file: str
    ) -> List[Dict[str, Any]]:
        """
        Обработка через Rule Engine через Unified Service /analyze_rule_engine
        
        Args:
            blocks: Список блоков для анализа
            patterns_file: Путь к файлу паттернов
        
        Returns:
            List of found_items from Rule Engine
        """
        try:
            logger.info(f"[RULE] Отправка {len(blocks)} блоков в Rule Engine...")
            
            payload = {
                "blocks": blocks,
                "patterns_file": patterns_file
            }
            
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.unified_service_url}/analyze_rule_engine",
                    json=payload
                )
            
            if response.status_code == 200:
                result = response.json()
                items = result.get('found_items', [])
                logger.info(f"[RULE] Rule Engine нашёл {len(items)} элементов")
                return items
            else:
                logger.error(f"❌ [RULE] Unified Service /analyze_rule_engine error: {response.status_code} - {response.text}")
                return []
        
        except Exception as e:
            logger.error(f"💥 [RULE] Exception: {e}")
            return []
    
    async def _process_nlp_service(
        self,
        blocks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Обработка через NLP Service через Unified Service /analyze_nlp
        
        Args:
            blocks: Список блоков для анализа
        
        Returns:
            List of found_items from NLP Service
        """
        try:
            logger.info(f"[NLP] Отправка {len(blocks)} блоков в NLP Service...")
            
            payload = {
                "blocks": blocks
            }
            
            async with httpx.AsyncClient(timeout=240.0) as client:  # Больше timeout для NLP
                response = await client.post(
                    f"{self.unified_service_url}/analyze_nlp",
                    json=payload
                )
            
            if response.status_code == 200:
                result = response.json()
                items = result.get('found_items', [])
                logger.info(f"[NLP] NLP Service нашёл {len(items)} элементов")
                return items
            else:
                logger.error(f"❌ [NLP] Unified Service /analyze_nlp error: {response.status_code} - {response.text}")
                return []
        
        except Exception as e:
            logger.error(f"💥 [NLP] Exception: {e}")
            return []
