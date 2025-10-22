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
NLP_SERVICE_URL = "http://localhost:8003"
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

@app.post("/anonymize_full")
async def anonymize_full(
    file: UploadFile = File(...), 
    patterns_file: str = Form(default="patterns/sensitive_patterns.xlsx"),
    generate_excel_report: bool = Form(default=True),
    generate_json_ledger: bool = Form(default=False)
):
    """
    Проксирование запроса полной анонимизации к unified_document_service
    """
    try:
        # Подготавливаем файлы для пересылки
        files = {
            'file': (file.filename, file.file, file.content_type)
        }
        
        data = {
            'patterns_file': patterns_file,
            'generate_excel_report': generate_excel_report,
            'generate_json_ledger': generate_json_ledger
        }
        
        # Пересылаем запрос к unified_document_service
        response = requests.post(
            f"{UNIFIED_SERVICE_URL}/anonymize_full",
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
