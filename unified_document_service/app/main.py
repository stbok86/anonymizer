
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from docx import Document
from .block_builder import BlockBuilder
import tempfile
import shutil
import os

app = FastAPI()

@app.get("/healthz")
def healthz():
    return {"status": "ok"}

@app.get("/readyz")
def readyz():
    return {"status": "ready"}

@app.post("/parse_docx_blocks")
async def parse_docx_blocks(file: UploadFile = File(...)):
    # Сохраняем загруженный файл во временный файл
    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name
    try:
        doc = Document(tmp_path)
        builder = BlockBuilder()
        blocks = builder.build_blocks(doc)
        # Возвращаем только метаинформацию (без element)
        blocks_out = [
            {k: v for k, v in b.items() if k != "element"}
            for b in blocks
        ]
        return JSONResponse(content={"blocks": blocks_out})
    finally:
        os.remove(tmp_path)
