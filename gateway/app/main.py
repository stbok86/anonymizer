from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from fastapi.responses import FileResponse
import requests
import tempfile
import os
from typing import List, Optional

app = FastAPI(title="Document Anonymizer Gateway", version="1.0.0")

# URL сервисов
UNIFIED_SERVICE_URL = "http://localhost:8009"
NLP_SERVICE_URL = "http://localhost:8006"
RULE_ENGINE_URL = "http://localhost:8003"
ORCHESTRATOR_URL = "http://localhost:8004"

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
    Проксирование запроса анализа к unified_document_service
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
            f"{UNIFIED_SERVICE_URL}/analyze_document",
            files=files,
            data=data,
            timeout=120
        )
        
        print(f"🔍 [DEBUG] Gateway получил ответ от Unified Service: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"🔍 [DEBUG] Результат от Unified Service: {type(result)}")
            print(f"🔍 [DEBUG] Ключи в результате: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
            return result
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

@app.post("/anonymize_selected")
async def anonymize_selected(
    file: UploadFile = File(...), 
    selected_items: str = Form(...),
    patterns_file: str = Form(default="patterns/sensitive_patterns.xlsx")
):
    """
    Проксирование запроса селективной анонимизации к unified_document_service
    """
    try:
        print(f"🚀 [GATEWAY] Получен запрос анонимизации: файл={file.filename}")
        print(f"🚀 [GATEWAY] selected_items длина: {len(selected_items) if selected_items else 'None'}")
        print(f"🚀 [GATEWAY] patterns_file: {patterns_file}")
        
        # Подготавливаем файлы для пересылки
        files = {
            'file': (file.filename, file.file, file.content_type)
        }
        
        data = {
            'patterns_file': patterns_file,
            'selected_items': selected_items
        }
        
        print(f"🚀 [GATEWAY] Отправляем к unified_document_service...")
        
        # Пересылаем запрос к unified_document_service
        response = requests.post(
            f"{UNIFIED_SERVICE_URL}/anonymize_selected",
            files=files,
            data=data,
            timeout=120
        )
        
        print(f"🚀 [GATEWAY] Ответ от unified_document_service: {response.status_code}")
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ [GATEWAY] Ошибка от unified_document_service: {response.status_code}")
            print(f"❌ [GATEWAY] Текст ошибки: {response.text}")
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Ошибка unified_document_service: {response.text}"
            )
            
    except requests.exceptions.RequestException as e:
        print(f"❌ [GATEWAY] Ошибка сети при обращении к unified_document_service: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail=f"Unified Document Service недоступен: {str(e)}"
        )
    except Exception as e:
        print(f"❌ [GATEWAY] Неожиданная ошибка при анонимизации: {str(e)}")
        import traceback
        print(f"❌ [GATEWAY] Трассировка: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Неожиданная ошибка при анонимизации: {str(e)}"
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)