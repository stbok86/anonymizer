from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse, FileResponse
import requests
import tempfile
import shutil
import os

app = FastAPI(title="Document Anonymizer Gateway", version="1.0.0")

# Конфигурация сервисов
UNIFIED_SERVICE_URL = "http://localhost:8001"
ORCHESTRATOR_URL = "http://localhost:8002"
NLP_SERVICE_URL = "http://localhost:8006"  # Обновлен порт для NLP Service
RULE_ENGINE_URL = "http://localhost:8004"

@app.get("/health")
def health():
    return {"status": "ok", "service": "gateway"}

@app.get("/healthz")
def healthz():
    return {"status": "ok"}

@app.get("/readyz")
def readyz():
    return {"status": "ready"}

@app.get("/services/status")
async def services_status():
    """Проверка статуса всех сервисов"""
    services = {
        "unified_document_service": UNIFIED_SERVICE_URL,
        "orchestrator": ORCHESTRATOR_URL,
        "nlp_service": NLP_SERVICE_URL,
        "rule_engine": RULE_ENGINE_URL
    }
    
    status = {}
    for service_name, url in services.items():
        try:
            response = requests.get(f"{url}/health", timeout=5)
            status[service_name] = {
                "status": "ok" if response.status_code == 200 else "error",
                "url": url,
                "response_code": response.status_code
            }
        except requests.exceptions.RequestException:
            status[service_name] = {
                "status": "unavailable",
                "url": url,
                "response_code": None
            }
    
    return status

@app.post("/analyze_document")
async def analyze_document(
    file: UploadFile = File(...), 
    patterns_file: str = Form(default="patterns/sensitive_patterns.xlsx")
):
    """
    Анализ документа без анонимизации - только поиск чувствительных данных
    """
    try:
        # Подготавливаем файлы для пересылки
        files = {
            'file': (file.filename, file.file, file.content_type)
        }
        
        data = {
            'patterns_file': patterns_file
        }
        
        # Пересылаем запрос к unified_document_service для анализа
        response = requests.post(
            f"{UNIFIED_SERVICE_URL}/analyze_document",
            files=files,
            data=data,
            timeout=120
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(
                status_code=response.status_code, 
                detail=f"Unified service error: {response.text}"
            )
            
    except requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="Service timeout")
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Service unavailable: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/anonymize_document")
async def anonymize_document(
    file: UploadFile = File(...), 
    patterns_file: str = Form(default="patterns/sensitive_patterns.xlsx")
):
    """
    Полная анонимизация документа с заменой всех найденных чувствительных данных
    """
    try:
        # Создаем временный файл для загруженного документа
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file.filename.split('.')[-1]}") as tmp_file:
            shutil.copyfileobj(file.file, tmp_file)
            temp_path = tmp_file.name
        
        try:
            # Подготавливаем файлы для пересылки
            files = {
                'file': (file.filename, open(temp_path, 'rb'), file.content_type)
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
            
            files['file'][1].close()  # Закрываем файл
            
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(
                    status_code=response.status_code, 
                    detail=f"Unified service error: {response.text}"
                )
                
        finally:
            # Удаляем временный файл
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            
    except requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="Service timeout")
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Service unavailable: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/anonymize_full")
async def anonymize_full(
    file: UploadFile = File(...),
    patterns_file: str = Form(default="patterns/sensitive_patterns.xlsx"),
    output_format: str = Form(default="docx"),
    highlight_replacements: str = Form(default="false"),
    generate_json_ledger: str = Form(default="false")
):
    """
    Полная анонимизация с дополнительными опциями
    """
    try:
        # Создаем временный файл для загруженного документа
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file.filename.split('.')[-1]}") as tmp_file:
            shutil.copyfileobj(file.file, tmp_file)
            temp_path = tmp_file.name
        
        try:
            # Подготавливаем файлы для пересылки
            files = {
                'file': (file.filename, open(temp_path, 'rb'), file.content_type)
            }
            
            data = {
                'patterns_file': patterns_file,
                'output_format': output_format,
                'highlight_replacements': highlight_replacements,
                'generate_json_ledger': generate_json_ledger
            }
            
            # Пересылаем запрос к unified_document_service
            response = requests.post(
                f"{UNIFIED_SERVICE_URL}/anonymize_full",
                files=files,
                data=data,
                timeout=120
            )
            
            files['file'][1].close()  # Закрываем файл
            
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Ошибка unified_document_service: {response.text}"
                )
                
        finally:
            # Удаляем временный файл
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            
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