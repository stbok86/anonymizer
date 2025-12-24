from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from fastapi.responses import FileResponse
import requests
import tempfile
import os
from typing import List, Optional
from dotenv import load_dotenv
import logging

# Загружаем переменные окружения из .env
load_dotenv()

app = FastAPI(title="Document Anonymizer Gateway", version="1.0.0")

# Настройка логирования
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# URL сервисов
UNIFIED_SERVICE_URL = "http://localhost:8009"
NLP_SERVICE_URL = "http://localhost:8006"
RULE_ENGINE_URL = "http://localhost:8003"  # ИСПРАВЛЕНО: было 8009, должно быть 8003
ORCHESTRATOR_URL = "http://localhost:8004"

# Feature flags из .env
USE_ORCHESTRATOR = os.getenv("USE_ORCHESTRATOR", "false").lower() == "true"
AB_TESTING = os.getenv("AB_TESTING", "false").lower() == "true"
ORCHESTRATOR_CANARY = int(os.getenv("ORCHESTRATOR_CANARY", "0"))

logger.info(f"Gateway started with USE_ORCHESTRATOR={USE_ORCHESTRATOR}, AB_TESTING={AB_TESTING}, CANARY={ORCHESTRATOR_CANARY}%")

@app.get("/")
async def root():
    return {
        "message": "Document Anonymizer Gateway", 
        "version": "1.0.0",
        "services": {
            "unified": UNIFIED_SERVICE_URL,
            "nlp": NLP_SERVICE_URL,
            "rule_engine": RULE_ENGINE_URL,
            "orchestrator": ORCHESTRATOR_URL
        },
        "feature_flags": {
            "use_orchestrator": USE_ORCHESTRATOR,
            "ab_testing": AB_TESTING,
            "orchestrator_canary": f"{ORCHESTRATOR_CANARY}%"
        }
    }

@app.get("/health")
async def health_check():
    """Проверка здоровья Gateway и всех сервисов"""
    services_status = {
        "gateway": "healthy"
    }
    
    # Проверяем каждый сервис
    services = {
        "unified": f"{UNIFIED_SERVICE_URL}/health",
        "nlp": f"{NLP_SERVICE_URL}/healthz",
        "rule_engine": f"{RULE_ENGINE_URL}/healthz",
        "orchestrator": f"{ORCHESTRATOR_URL}/healthz"
    }
    
    for service_name, url in services.items():
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                services_status[service_name] = "healthy"
            else:
                services_status[service_name] = f"error: {response.status_code}"
        except requests.exceptions.RequestException as e:
            services_status[service_name] = f"unavailable: {str(e)}"
    
    return {"status": "ok", "services": services_status}

@app.post("/process_text")
async def process_text(request_data: dict):
    """
    Обработка текста через Rule Engine
    Проксирование запросов к rule_engine
    """
    try:
        # Пересылаем запрос к rule_engine
        response = requests.post(
            f"{RULE_ENGINE_URL}/process_text",
            json=request_data,
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Rule Engine error: {response.text}"
            )
            
    except requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="Service timeout")
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Service unavailable: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/analyze_document")
async def analyze_document(
    file: UploadFile = File(...), 
    patterns_file: str = Form(default="patterns/sensitive_patterns.xlsx")
):
    """
    Проксирование запроса анализа с поддержкой feature flags
    
    Поддерживаемые режимы:
    - USE_ORCHESTRATOR=false: текущая система (Unified Service)
    - USE_ORCHESTRATOR=true: новая система (Orchestrator)
    - AB_TESTING=true: запускает оба пути для сравнения
    - ORCHESTRATOR_CANARY=X: X% трафика на Orchestrator
    """
    try:
        # Подготавливаем файлы для пересылки
        # Читаем файл в память один раз для возможного повторного использования
        file_content = await file.read()
        file.file.seek(0)  # Возвращаем указатель в начало
        
        files = {
            'file': (file.filename, file_content, file.content_type)
        }
        
        data = {
            'patterns_file': patterns_file
        }
        
        # Определяем куда направить запрос
        if USE_ORCHESTRATOR:
            # Режим: Полностью на Orchestrator
            logger.info("[ORCHESTRATOR] Routing to Orchestrator (USE_ORCHESTRATOR=true)")
            target_url = f"{ORCHESTRATOR_URL}/analyze_document"
            route_name = "Orchestrator"
        else:
            # Режим: Текущая система (Unified Service)
            logger.info("[UNIFIED] Routing to Unified Service (USE_ORCHESTRATOR=false)")
            target_url = f"{UNIFIED_SERVICE_URL}/analyze_document"
            route_name = "Unified Service"
        
        # Пересылаем запрос
        response = requests.post(
            target_url,
            files=files,
            data=data,
            timeout=120
        )
        
        logger.info(f"[{route_name}] Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            logger.debug(f"✅ [{route_name}] Success: {len(result.get('found_items', []))} items found")
            return result
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Ошибка {route_name}: {response.text}"
            )
            
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Service unavailable: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail=f"Service недоступен: {str(e)}"
        )

@app.post("/anonymize_document")
async def anonymize_document(
    file: UploadFile = File(...), 
    patterns_file: str = Form(default="patterns/sensitive_patterns.xlsx")
):
    """
    Проксирование запроса анонимизации к unified_document_service
    """
    try:
        # Подготавливаем файлы для пересылки
        files = {
            'file': (file.filename, file.file, file.content_type)
        }
        
        data = {
            'patterns_file': patterns_file
        }
        
        # Пересылаем запрос к unified_document_service
        response = requests.post(
            f"{UNIFIED_SERVICE_URL}/anonymize_document",
            files=files,
            data=data,
            timeout=120
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Ошибка unified_document_service: {response.text}"
            )
            
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=503,
            detail=f"Unified Document Service недоступен: {str(e)}"
        )

@app.get("/download_anonymized/{filename}")
async def download_anonymized(filename: str):
    """
    Проксирование запроса скачивания анонимизированного документа
    """
    try:
        response = requests.get(
            f"{UNIFIED_SERVICE_URL}/download_anonymized/{filename}",
            timeout=30
        )
        
        if response.status_code == 200:
            # Сохраняем файл временно и возвращаем через FileResponse
            with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
                tmp.write(response.content)
                tmp_path = tmp.name
            
            return FileResponse(
                path=tmp_path,
                filename=filename,
                media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            )
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail="Файл не найден"
            )
            
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=503,
            detail=f"Unified Document Service недоступен: {str(e)}"
        )

@app.post("/anonymize_selected")
async def anonymize_selected(
    file: UploadFile = File(...), 
    patterns_file: str = Form(default="patterns/sensitive_patterns.xlsx"),
    generate_excel_report: bool = Form(default=True),
    generate_json_ledger: bool = Form(default=False),
    selected_items: str = Form(...)
):
    """
    Проксирование запроса анонимизации к unified_document_service
    Выполняет анонимизацию только выбранных пользователем элементов
    """
    try:
        print(f"[GATEWAY] Получен запрос анонимизации: файл={file.filename}")
        print(f"[GATEWAY] selected_items: {len(selected_items)} символов")
        
        # Подготавливаем файлы для пересылки
        files = {
            'file': (file.filename, file.file, file.content_type)
        }
        
        data = {
            'patterns_file': patterns_file,
            'generate_excel_report': generate_excel_report,
            'generate_json_ledger': generate_json_ledger,
            'selected_items': selected_items
        }
        
        # Пересылаем запрос к unified_document_service
        response = requests.post(
            f"{UNIFIED_SERVICE_URL}/anonymize_selected",
            files=files,
            data=data,
            timeout=120
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Ошибка unified_document_service: {response.text}"
            )
            
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=503,
            detail=f"Unified Document Service недоступен: {str(e)}"
        )


# === NLP Service Routes ===

@app.post("/nlp/analyze")
async def nlp_analyze(request_data: dict):
    """
    Анализ текстовых блоков через NLP Service
    Проксирование запросов от Orchestrator к NLP Service
    """
    try:
        # Пересылаем запрос к NLP Service
        response = requests.post(
            f"{NLP_SERVICE_URL}/analyze",
            json=request_data,
            timeout=60,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"NLP Service error: {response.text}"
            )
            
    except requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="NLP Service timeout")
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=502, detail=f"NLP Service unavailable: {str(e)}")

@app.get("/nlp/health")
async def nlp_health():
    """Проверка здоровья NLP Service"""
    try:
        response = requests.get(f"{NLP_SERVICE_URL}/healthz", timeout=5)
        return response.json()
    except requests.exceptions.RequestException:
        raise HTTPException(status_code=503, detail="NLP Service unavailable")

@app.get("/nlp/categories")
async def nlp_categories():
    """Получение списка категорий из NLP Service"""
    try:
        response = requests.get(f"{NLP_SERVICE_URL}/categories", timeout=10)
        return response.json()
    except requests.exceptions.RequestException:
        raise HTTPException(status_code=503, detail="NLP Service unavailable")

@app.post("/nlp/test")
async def nlp_test(text: str):
    """Тестовый анализ текста через NLP Service"""
    try:
        response = requests.post(
            f"{NLP_SERVICE_URL}/test",
            params={"text": text},
            timeout=30
        )
        return response.json()
    except requests.exceptions.RequestException:
        raise HTTPException(status_code=503, detail="NLP Service unavailable")


@app.post("/deanonymize")
async def deanonymize_document(
    document: UploadFile = File(..., description="Анонимизированный DOCX документ"),
    replacement_table: UploadFile = File(..., description="Таблица соответствий UUID ↔ оригинальные данные")
):
    """
    Деанонимизация документа - обратная замена UUID на оригинальные данные
    
    Args:
        document: Анонимизированный DOCX файл
        replacement_table: Excel или CSV файл с соответствиями
        
    Returns:
        JSON с деанонимизированным документом и статистикой
    """
    try:
        # Проверяем типы файлов
        if not document.filename.endswith('.docx'):
            raise HTTPException(status_code=400, detail="Документ должен быть в формате DOCX")
        
        if not (replacement_table.filename.endswith('.xlsx') or replacement_table.filename.endswith('.csv')):
            raise HTTPException(status_code=400, detail="Таблица замен должна быть в формате XLSX или CSV")
        
        # Создаем временные файлы
        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as doc_temp:
            content = await document.read()
            doc_temp.write(content)
            doc_temp_path = doc_temp.name
        
        with tempfile.NamedTemporaryFile(
            suffix='.xlsx' if replacement_table.filename.endswith('.xlsx') else '.csv',
            delete=False
        ) as table_temp:
            table_content = await replacement_table.read()
            table_temp.write(table_content)
            table_temp_path = table_temp.name
        
        # Отправляем запрос в Unified Document Service
        files = {
            'document': ('document.docx', open(doc_temp_path, 'rb')),
            'replacement_table': ('table.xlsx', open(table_temp_path, 'rb'))
        }
        
        response = requests.post(
            f"{UNIFIED_SERVICE_URL}/deanonymize",
            files=files,
            timeout=120
        )
        
        # Закрываем файлы
        for file_tuple in files.values():
            file_tuple[1].close()
        
        # Очищаем временные файлы
        try:
            os.unlink(doc_temp_path)
            os.unlink(table_temp_path)
        except:
            pass
        
        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Ошибка Unified Service: {response.text}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка Gateway: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)