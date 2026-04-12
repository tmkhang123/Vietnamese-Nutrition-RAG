from __future__ import annotations

import os
import sys
from contextlib import asynccontextmanager

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

os.environ["TQDM_DISABLE"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["TRANSFORMERS_NO_ADVISORY_WARNINGS"] = "1"

from fastapi import FastAPI, HTTPException
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel
import uvicorn

from src.pipeline import NutritionPipeline

_pipeline: NutritionPipeline | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _pipeline
    print("[RAG Server] Đang khởi động pipeline (NER + ChromaDB + Ollama)...")
    _pipeline = NutritionPipeline()
    print("[RAG Server] Pipeline sẵn sàng.")
    yield
    print("[RAG Server] Tắt server.")


app = FastAPI(title="RAG Dinh Dưỡng", lifespan=lifespan)


class AskRequest(BaseModel):
    message: str


@app.post("/ask")
async def ask(req: AskRequest):
    if _pipeline is None:
        raise HTTPException(status_code=503, detail="Pipeline chưa sẵn sàng.")

    # Chạy trong thread pool để không block event loop
    result = await run_in_threadpool(_pipeline.answer, req.message)

    ner_entities = result.get("entities", {})
    entities_out = {
        "foods":     ner_entities.get("FOOD",     []),
        "diseases":  ner_entities.get("DISEASE",  []),
        "nutrients": ner_entities.get("NUTRIENT", []),
        "symptoms":  ner_entities.get("SYMPTOM",  []),
    }

    energy = None
    nutrition_data = result.get("nutrition_data")
    if nutrition_data and isinstance(nutrition_data, dict):
        energy = {
            "amountPer100g": nutrition_data.get("amount_per_100g"),
            "unitName":      nutrition_data.get("unit"),
        }

    return {
        "answer":   result.get("answer", ""),
        "intent":   result.get("query_type", ""),
        "entities": entities_out,
        "sources":  sorted(set(result.get("sources", []))),
        "energy":   energy,
    }


@app.get("/health")
async def health():
    return {"status": "ok", "pipeline_ready": _pipeline is not None}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
