from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any

app = FastAPI()

class AnalyzeTextRequest(BaseModel):
    text: str
    options: Dict[str, Any] = {}

@app.get("/healthz")
def healthz():
    return {"status": "ok"}

@app.get("/readyz")  
def readyz():
    return {"status": "ready"}

@app.post("/analyze_text")
async def analyze_text(request: AnalyzeTextRequest):
    """
    Заглушка для совместимости с прямыми вызовами
    Возвращаем пустой результат, так как анализ должен идти через Unified Service
    """
    return {
        "success": True,
        "detections": [],
        "message": "Direct calls to Rule Engine are deprecated. Use Unified Service instead."
    }
