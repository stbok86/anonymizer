from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from dotenv import load_dotenv
import httpx
import os
import logging
from typing import Dict, Any

from services import ParallelAnalyzer

# Загружаем переменные окружения
load_dotenv()

app = FastAPI(title="Document Anonymizer Orchestrator", version="2.0.0")

# Настройка логирования
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# URL сервисов
UNIFIED_SERVICE_URL = os.getenv("UNIFIED_SERVICE_URL", "http://localhost:8009")
NLP_SERVICE_URL = os.getenv("NLP_SERVICE_URL", "http://localhost:8006")
RULE_ENGINE_URL = os.getenv("RULE_ENGINE_URL", "http://localhost:8003")

# Режим работы: basic_proxy или parallel (из .env)
PARALLEL_MODE = os.getenv("PARALLEL_MODE", "true").lower() == "true"

# Создаём ParallelAnalyzer
parallel_analyzer = ParallelAnalyzer(
    unified_service_url=UNIFIED_SERVICE_URL,
    nlp_service_url=NLP_SERVICE_URL,
    rule_engine_url=RULE_ENGINE_URL
)

logger.info(f"Orchestrator started with PARALLEL_MODE={PARALLEL_MODE}")

@app.get("/")
async def root():
    """Root endpoint с информацией о Orchestrator"""
    mode = "parallel_processing" if PARALLEL_MODE else "basic_proxy"
    description = "Этап 2: Параллельная обработка Rule + NLP" if PARALLEL_MODE else "Этап 1: Базовое проксирование"
    
    return {
        "message": "Document Anonymizer Orchestrator",
        "version": "2.0.0",
        "mode": mode,
        "parallel_enabled": PARALLEL_MODE,
        "description": description,
        "services": {
            "unified": UNIFIED_SERVICE_URL,
            "nlp": NLP_SERVICE_URL,
            "rule_engine": RULE_ENGINE_URL
        }
    }

@app.get("/healthz")
def healthz():
    """Health check endpoint"""
    return {"status": "ok"}

@app.get("/readyz")
def readyz():
    """Readiness check endpoint"""
    return {"status": "ready"}

@app.post("/analyze_document")
async def analyze_document(
    file: UploadFile = File(...),
    patterns_file: str = Form(default="patterns/sensitive_patterns.xlsx")
) -> Dict[str, Any]:
    """
    Анализ документа с возможностью параллельной обработки
    
    Режимы работы (управляется через PARALLEL_MODE в .env):
    - PARALLEL_MODE=true: Параллельная обработка Rule + NLP (Этап 2) ⚡
    - PARALLEL_MODE=false: Простое проксирование (Этап 1)
    
    Args:
        file: DOCX файл для анализа
        patterns_file: Путь к файлу с паттернами
    
    Returns:
        Dict с найденными элементами и метриками производительности
    """
    logger.info(f"[ORCHESTRATOR] Received analyze_document request: {file.filename}")
    
    try:
        # Читаем файл в память
        file_content = await file.read()
        
        if PARALLEL_MODE:
            # ЭТАП 2: Параллельная обработка
            logger.info("[ORCHESTRATOR] Using PARALLEL mode (Этап 2)")
            
            result = await parallel_analyzer.analyze_document_parallel(
                file_content=file_content,
                filename=file.filename,
                patterns_file=patterns_file
            )
            
            return result
        
        else:
            # ЭТАП 1: Простое проксирование (старая логика)
            logger.info("[ORCHESTRATOR] Using BASIC PROXY mode (Этап 1)")
            
            files = {
                'file': (file.filename, file_content, file.content_type or 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')
            }
            
            data = {
                'patterns_file': patterns_file
            }
            
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{UNIFIED_SERVICE_URL}/analyze_document",
                    files=files,
                    data=data
                )
            
            if response.status_code == 200:
                result = response.json()
                found_count = len(result.get('found_items', []))
                logger.info(f"[ORCHESTRATOR] Basic proxy success: {found_count} items")
                
                result['orchestrator_metadata'] = {
                    'version': '2.0.0',
                    'mode': 'basic_proxy',
                    'etap': 1
                }
                
                return result
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Unified Service error: {response.text}"
                )
    
    except httpx.TimeoutException:
        logger.error("[ORCHESTRATOR] Request timeout")
        raise HTTPException(
            status_code=504,
            detail="Service timeout (>120s)"
        )
    except httpx.RequestError as e:
        logger.error(f"🔌 [ORCHESTRATOR] Connection error: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Cannot connect to services: {str(e)}"
        )
    except Exception as e:
        logger.error(f"💥 [ORCHESTRATOR] Unexpected error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

