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