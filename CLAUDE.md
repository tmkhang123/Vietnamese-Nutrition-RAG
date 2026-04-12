# CLAUDE.md — Hệ thống RAG Dinh dưỡng Tiếng Việt

> File hướng dẫn dành cho AI assistant. Đọc kỹ trước khi làm bất cứ việc gì.

---

## ✅ TRẠNG THÁI HIỆN TẠI — Cập nhật 2026-04-11

**Pipeline core:** Eval lần 7 PASS toàn bộ 7 nhóm với `llama3.1:8b`.  
**Eval notebook:** Đã có đủ 4 metrics (intent accuracy, source relevance, keyword presence, latency) trong `notebooks/eval_7_groups.ipynb`.  
**GitHub:** Đã push lên `tmkhang123/Vietnamese-Nutrition-RAG` (commit `8c71cf7`).  
**Giai đoạn tiếp theo:** Build web UI và hoàn thiện hệ thống.

**Việc tiếp theo:** Xem section "Bước tiếp theo" ở dưới.

---

## Tổng quan dự án

**Tên:** Hybrid RAG Nutrition Q&A — Hệ thống tư vấn dinh dưỡng và sức khỏe tiếng Việt  
**Người làm:** TV1 — làm toàn bộ backend, pipeline, NLP, dữ liệu, AI  
**Nhóm:** 3 thành viên — TV2 làm crawler + dữ liệu, TV3 làm Spring Boot UI  
**Mục tiêu:** Hoàn thiện hệ thống RAG, chuẩn bị báo cáo giữa kỳ Deep Learning.

---

## Kiến trúc pipeline (hiện tại)

```
Câu hỏi (tiếng Việt)
        │
        ▼
[preprocessor.py ✅]    normalize Unicode + underthesea word tokenize
        │
        ▼
[ner_model.py ✅]       PhoBERT fine-tuned — extract FOOD, DISEASE, NUTRIENT, SYMPTOM
        │                (load từ models/ner_phobert/phobert-ner-final/)
        ▼
[classifier.py ✅]      keyword-based + override logic → NUTRITION_LOOKUP / HEALTH_ADVICE / BOTH
        │                normalize underscore trước khi match; "ăn gì" trong NUTRITION_KEYWORDS
        ├─── NUTRITION ──→ [sqlite_manager.py ✅]   USDA lookup → nutrition_data
        │
        └─── HEALTH ─────→ [vector_store.py ✅]    ChromaDB semantic search
                           [retriever.py ✅]        BM25 (underthesea) + RRF + score_threshold=0.5
                                      │              strip underscore CHỈ cho semantic search
                                      ▼
                               health_chunks (score >= 0.5)
        │
        ▼
[generator.py ✅]       → Ollama llama3.1:8b (local)
        │                /api/chat với system message; không fallback /api/generate
        ▼
[main/rag_cli.py ✅]    JSON bridge cho Spring Boot
        │
        ▼
[chatbot ✅]            Spring Boot port 8081
```

---

## Trạng thái các file — CẬP NHẬT 2025-04-11

| File | Trạng thái | Ghi chú |
|---|---|---|
| `src/nlp/preprocessor.py` | ✅ Ổn | — |
| `src/nlp/classifier.py` | ✅ Đã fix | normalize `_`→space + "ăn gì" trong NUTRITION_KEYWORDS |
| `src/nlp/ner_model.py` | ✅ Ổn | — |
| `src/nlp/retriever.py` | ✅ Đã fix | strip underscore cho semantic, BM25 giữ nguyên |
| `src/database/sqlite_manager.py` | ✅ Ổn | — |
| `src/database/vector_store.py` | ✅ Ổn | — |
| `src/generation/generator.py` | ✅ Đã fix | llama3.1:8b, system message, không fallback generate |
| `src/pipeline.py` | ✅ Đã fix | score_threshold từ config, query gốc cho retriever |
| `main/rag_cli.py` | ✅ Ổn | — |
| `configs/config.yaml` | ✅ Đã fix | `llm_model: "llama3.1:8b"`, `similarity_threshold: 0.5` |
| `eval_7_groups.py` | ❌ Đã xóa | Thay bằng `notebooks/eval_7_groups.ipynb` |
| `notebooks/eval_7_groups.ipynb` | ✅ Đầy đủ | intent accuracy, source relevance, keyword presence, latency |
| `data/raw/articles/` | ✅ 184 bài | +1 bài synthetic: `syn_trieu_chung_bo_sung_dinh_duong.json` |

---

## Lịch sử eval

| Lần | Model | Kết quả | Vấn đề chính |
|---|---|---|---|
| 1-2 | qwen3:4b | ❌ | Thinking leak nặng |
| 3 | qwen3:4b | ❌ | Thinking + intent sai nhóm 3,7 |
| 4 | qwen2.5:7b | ❌ | Chinese output + chat template contamination |
| 5 | llama3.1:8b | ❌ | Model từ chối trả lời câu y tế |
| 6 | llama3.1:8b | ❌ | Nhóm 3 lấy bài sai (thiếu corpus) |
| **7** | **llama3.1:8b** | **✅ ALL PASS** | — |

### Eval lần 7 — kết quả chi tiết

| Nhóm | Intent | Used LLM | Source |
|---|---|---|---|
| 1 — Tra cứu protein ức gà | NUTRITION_LOOKUP | ✅ | USDA (14.59g) |
| 2 — Tiểu đường ăn gì | BOTH | ✅ | Vinmec |
| 3 — Đau đầu chóng mặt mệt mỏi | HEALTH_ADVICE | ✅ | Tổng hợp dinh dưỡng |
| 4 — Gym tăng cơ | BOTH | ✅ | Vinmec |
| 5 — Bà bầu 3 tháng đầu | HEALTH_ADVICE | ✅ | Vinmec |
| 6 — Ăn chay protein | BOTH | ✅ | Vinmec |
| 7 — Tiểu đường giảm cân ăn gì | BOTH | ✅ | Vinmec |

---

## Bước tiếp theo

**Roadmap đầy đủ tại:** `C:\Users\Khanng\.claude\plans\eventual-hatching-bentley.md`

**Đã hoàn thành:**
- ~~Hạng mục 1 — Eval metrics~~ ✅ (đã có trong notebook)

**Còn lại trước báo cáo:**
1. **vi_food_mapping** — mở rộng 81 → 180+ món (`data/vi_food_mapping.csv`)
2. **Bài synthetic** — tạo thêm 8 bài JSON trong `data/raw/articles/` rồi `python -m src.data_pipeline.embed_articles`
3. **Web UI** — build/hoàn thiện Spring Boot UI (xem plan Hạng mục 7)

**Sau báo cáo:**
4. Classifier robustness (`src/nlp/classifier.py`)
5. NER confidence scores (`src/nlp/ner_model.py` + `src/pipeline.py`)
6. H2 persist fix (`chatbot/src/main/resources/application.properties`)

**Chạy eval (dùng notebook, không còn .py):**
```bash
conda activate nutrition-rag
jupyter notebook notebooks/eval_7_groups.ipynb
```

---

## Quyết định quan trọng & lý do

| Quyết định | Lý do |
|---|---|
| Embed 184 raw articles thay vì 36 JSONL | 36 dòng không đủ nội dung cho 7 nhóm |
| Chuyển sang `llama3.1:8b` | qwen3:4b thinking không tắt được; qwen2.5:7b gen tiếng Trung khi fallback `/api/generate` |
| Bỏ fallback `/api/generate` | Fallback gây chat template contamination (`<\|im_start\|>`) + Chinese output |
| System message "Không từ chối trả lời" | llama3.1:8b có safety guardrails từ chối câu hỏi y tế khi không có context |
| Classifier normalize `_` → space | underthesea tạo "đau_đầu" nhưng keyword dạng "đau đầu" → h_score = 0 → intent sai |
| Thêm "ăn gì" vào NUTRITION_KEYWORDS | Group 7: "ăn gì?" cần n_score > 0 để trigger BOTH |
| Strip underscore CHỈ cho semantic search | BM25 tokenize nhất quán cả index lẫn query (underthesea) nên không cần |
| score_threshold = 0.5 (từ config) | Tránh đưa bài không liên quan vào LLM; giữ ít nhất 1 chunk |
| Bài synthetic nhóm 3 | Corpus gốc thiếu bài kết nối triệu chứng → chất dinh dưỡng cụ thể |
| Incremental embedding với manifest | Tránh re-embed toàn bộ khi thêm bài mới |

---

## Thông tin kỹ thuật cần nhớ

### LLM
- Model: **`llama3.1:8b`** (Ollama local)
- Timeout Java: `rag.timeoutMs=240000`
- `num_predict: 2000`, `temperature: 0.3`, `num_ctx: 4096`
- System message bắt buộc (không có → model từ chối câu hỏi y tế)

### ChromaDB
- Score: `score = 1 - distance / 2`
- Persist: `data/chroma_db/`
- Collection: `health_articles`
- Đã embed 184 bài → 3305+ chunks
- Incremental embed: `python -m src.data_pipeline.embed_articles`
- Re-embed toàn bộ: `rm -r -fo data\chroma_db` rồi restart pipeline

### NER
- Model: `models/ner_phobert/phobert-ner-final/`
- Vấn đề biết: "ức gà" → NER tách ["ức", "gà"] — pipeline.py đã có workaround concatenate
- Protein value đúng (14.59g) nhờ workaround; tên food hơi sai ("Chicken breast, roll")

### Spring Boot
- Port: 8081
- Python: `D:/anaconda/envs/nutrition-rag/python.exe`
- Script: `d:/FoodRecomendationSystem/main/rag_cli.py`
- JAVA_HOME: jdk-23
- Chạy: `conda activate nutrition-rag` → `python main/rag_server.py` → `cd chatbot` → `mvn spring-boot:run`

---

## Dữ liệu hiện có

| File/Folder | Nội dung | Trạng thái |
|---|---|---|
| `data/usda_food.db` | USDA FoodData Central SQLite | ✅ |
| `data/vi_food_mapping.csv` | Mapping tiếng Việt → USDA | ⚠️ Cần mở rộng |
| `data/medical_knowledge.jsonl` | 36 dòng — deprecated | Không dùng |
| `data/raw/articles/` | 184 file JSON (183 gốc + 1 synthetic) | ✅ Đã embed |
| `data/chroma_db/` | ChromaDB persist | ✅ Đang dùng |
| `models/ner_phobert/phobert-ner-final/` | PhoBERT NER đã fine-tune | ✅ |

---

## Không làm

- Không push lên GitHub nếu user chưa yêu cầu
- Không tự ý thêm tính năng ngoài plan
- Không xóa file nếu không chắc
- Không dùng tiếng Anh trong câu trả lời với user (user nói tiếng Việt)
- Không sửa code/logic khi chỉ được yêu cầu sửa comment
