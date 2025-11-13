#!/usr/bin/env python3
"""
NLP Service для обработки неструктурированных данных
Фокус на spaCy NER + кастомные матчеры + морфологический анализ
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging
import os
import sys

# Добавляем путь к модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from nlp_adapter import NLPAdapter

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="NLP Service", version="1.0.0")

# Глобальный экземпляр NLP адаптера
nlp_adapter = None

# Pydantic модели для API
class TextBlock(BaseModel):
    """Блок текста для анализа"""
    content: str
    block_id: str
    block_type: str = "text"

class AnalyzeRequest(BaseModel):
    """Запрос на анализ текстовых блоков"""
    blocks: List[TextBlock]
    options: Optional[Dict[str, Any]] = {}

class Detection(BaseModel):
    """Обнаруженные чувствительные данные"""
    category: str
    original_value: str
    confidence: float
    position: Dict[str, int]
    method: str
    uuid: str
    block_id: str

class AnalyzeResponse(BaseModel):
    """Ответ с результатами анализа"""
    success: bool
    detections: List[Detection]
    total_detections: int
    blocks_processed: int
    error: Optional[str] = None

@app.on_event("startup")
async def startup_event():
    """Инициализация сервиса при запуске"""
    global nlp_adapter
    
    try:
        logger.info("🚀 Инициализация NLP Service...")
        
        # Создаем NLP адаптер
        nlp_adapter = NLPAdapter()
        
        logger.info("✅ NLP Service успешно инициализирован")
        
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации NLP Service: {e}")
        raise e

@app.get("/healthz")
def healthz():
    """Проверка здоровья сервиса"""
    return {"status": "ok", "service": "nlp-service"}

@app.get("/readyz")
def readyz():
    """Проверка готовности сервиса"""
    global nlp_adapter
    
    if nlp_adapter is None:
        raise HTTPException(status_code=503, detail="NLP adapter not initialized")
    
    return {"status": "ready", "service": "nlp-service"}

@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_blocks(request: AnalyzeRequest):
    """
    Анализирует текстовые блоки на предмет чувствительных данных
    
    Args:
        request: Запрос с блоками для анализа
        
    Returns:
        Результаты анализа с обнаруженными данными
    """
    global nlp_adapter
    
    if nlp_adapter is None:
        raise HTTPException(
            status_code=503, 
            detail="NLP adapter not initialized"
        )
    
    try:
        logger.info(f"📝 Анализ {len(request.blocks)} блоков")
        
        all_detections = []
        blocks_processed = 0
        
        for block in request.blocks:
            try:
                # Анализируем содержимое блока
                block_detections = nlp_adapter.find_sensitive_data(block.content)
                
                # Добавляем block_id к каждому обнаружению
                for detection in block_detections:
                    detection['block_id'] = block.block_id
                    all_detections.append(Detection(**detection))
                
                blocks_processed += 1
                
                logger.debug(f"Блок {block.block_id}: найдено {len(block_detections)} обнаружений")
                
            except Exception as e:
                logger.error(f"Ошибка анализа блока {block.block_id}: {e}")
                continue
        
        logger.info(f"✅ Анализ завершен: {len(all_detections)} обнаружений в {blocks_processed} блоках")
        
        return AnalyzeResponse(
            success=True,
            detections=all_detections,
            total_detections=len(all_detections),
            blocks_processed=blocks_processed
        )
        
    except Exception as e:
        logger.error(f"❌ Ошибка анализа: {e}")
        return AnalyzeResponse(
            success=False,
            detections=[],
            total_detections=0,
            blocks_processed=0,
            error=str(e)
        )

@app.get("/patterns")
async def get_patterns():
    """Возвращает информацию о загруженных паттернах"""
    global nlp_adapter
    
    if nlp_adapter is None:
        raise HTTPException(
            status_code=503,
            detail="NLP adapter not initialized"  
        )
    
    patterns_info = {}
    
    for category, configs in nlp_adapter.pattern_configs.items():
        patterns_info[category] = {
            'count': len(configs),
            'types': list(set(config['pattern_type'] for config in configs)),
            'descriptions': [config['description'] for config in configs]
        }
    
    return {
        "total_categories": len(patterns_info),
        "patterns": patterns_info
    }

@app.get("/patterns/{category}")
async def get_category_patterns(category: str):
    """Возвращает конкретные паттерны для категории"""
    global nlp_adapter
    
    if nlp_adapter is None:
        raise HTTPException(
            status_code=503,
            detail="NLP adapter not initialized"
        )
    
    if category not in nlp_adapter.pattern_configs:
        raise HTTPException(
            status_code=404,
            detail=f"Category '{category}' not found"
        )
    
    configs = nlp_adapter.pattern_configs[category]
    return {
        "category": category,
        "patterns": [
            {
                "pattern": config['pattern'],
                "type": config['pattern_type'], 
                "confidence": config['confidence'],
                "context_required": config['context_required'],
                "description": config['description']
            }
            for config in configs
        ]
    }

@app.get("/categories") 
async def get_categories():
    """Возвращает список поддерживаемых категорий"""
    global nlp_adapter
    
    if nlp_adapter is None:
        raise HTTPException(
            status_code=503,
            detail="NLP adapter not initialized"
        )
    
    categories = list(nlp_adapter.patterns.keys())
    
    return {
        "categories": categories,
        "total": len(categories)
    }

@app.post("/test")
async def test_analysis(text: str):
    """Тестовый эндпоинт для быстрой проверки анализа текста"""
    global nlp_adapter
    
    if nlp_adapter is None:
        raise HTTPException(
            status_code=503,
            detail="NLP adapter not initialized"
        )
    
    try:
        detections = nlp_adapter.find_sensitive_data(text)
        
        return {
            "text": text,
            "detections": detections,
            "count": len(detections)
        }
        
    except Exception as e:
        logger.error(f"Ошибка тестового анализа: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8006)
