# Vietnamese Nutrition RAG

Hệ thống hỏi đáp dinh dưỡng và sức khỏe tiếng Việt, kiến trúc Hybrid RAG.

Người dùng đặt câu hỏi → hệ thống tra cứu từ 2 nguồn → LLM tổng hợp câu trả lời:

- **USDA SQLite** — dữ liệu dinh dưỡng chính xác (13,661 món)
- **ChromaDB** — tìm kiếm ngữ nghĩa trong tài liệu y tế tiếng Việt (BM25 + cosine + RRF)

---

## Kiến trúc

```
Câu hỏi (tiếng Việt)
    │
    ▼
Preprocessor (underthesea)
    │
    ▼
NER — PhoBERT fine-tuned (FOOD / DISEASE / NUTRIENT / SYMPTOM)
    │
    ▼
Classifier → NUTRITION_LOOKUP / HEALTH_ADVICE / BOTH
    │
    ├─── NUTRITION ──→ SQLite (USDA)
    └─── HEALTH ─────→ ChromaDB + BM25 + RRF
    │
    ▼
Ollama llama3.1:8b → câu trả lời
```

---

## Cấu trúc thư mục

```
├── src/
│   ├── nlp/            # preprocessor, classifier, NER, retriever (BM25+ChromaDB+RRF)
│   ├── database/       # sqlite_manager, vector_store
│   ├── generation/     # generator (Ollama)
│   └── data_pipeline/  # embedder, chunker, crawler
├── main/
│   ├── rag_server.py   # FastAPI server (port 8000) — load model 1 lần, serve nhiều request
│   └── rag_cli.py      # CLI bridge (legacy)
├── notebooks/
│   ├── eval_7_groups.ipynb          # đánh giá 7 nhóm câu hỏi (chạy local)
│   └── phobert_ner_finetune.ipynb   # fine-tune PhoBERT NER (chạy trên Colab)
├── chatbot/            # Spring Boot UI (port 8081)
├── data/
│   ├── usda_food.db         # USDA SQLite
│   ├── vi_food_mapping.csv  # mapping tên Việt → USDA
│   └── raw/articles/        # bài viết y tế tiếng Việt (~184 bài)
├── configs/config.yaml
└── requirements.txt
```

> **Không có trong repo** (phải tự tạo):
> - `data/chroma_db/` — tự sinh khi chạy pipeline lần đầu
> - `models/ner_phobert/` — fine-tune bằng notebook Colab rồi giải nén vào đây

---

## Cài đặt

**1. Python environment**

```bash
conda create -n nutrition-rag python=3.10
conda activate nutrition-rag
pip install -r requirements.txt
```

**2. Ollama + model**

Cài [Ollama](https://ollama.com), sau đó:

```bash
ollama pull llama3.1:8b
```

**3. NER model**

Fine-tune bằng `notebooks/phobert_ner_finetune.ipynb` trên Colab, download file zip về, giải nén vào:

```
models/ner_phobert/phobert-ner-final/
```

---

## Chạy notebook đánh giá (eval_7_groups)

Notebook này kiểm tra pipeline với 7 nhóm câu hỏi đại diện, in intent, entities, sources, câu trả lời và tóm tắt accuracy/latency.

**Chạy local:**

```bash
conda activate nutrition-rag
jupyter notebook notebooks/eval_7_groups.ipynb
```

Chạy lần lượt từng cell. Lần đầu sẽ tự động embed ~184 bài vào ChromaDB (mất vài phút).

---

## Fine-tune PhoBERT NER (phobert_ner_finetune)

Notebook này fine-tune `vinai/phobert-base` để nhận diện thực thể FOOD / DISEASE / NUTRIENT / SYMPTOM từ câu hỏi tiếng Việt.

**Chạy trên Google Colab** (cần GPU T4):

1. Upload `notebooks/phobert_ner_finetune.ipynb` lên Colab
2. Upload file `data/ner_labels/ner_data_augmented.csv` khi được hỏi
3. Chạy toàn bộ — huấn luyện 10 epoch, tự động download `phobert-ner-final.zip`
4. Giải nén zip vào `models/ner_phobert/`

---

## Chạy web (Spring Boot + FastAPI)

**Yêu cầu:** JDK 21+, Maven, Python environment đã cài

**Bước 1** — đảm bảo Ollama đang chạy:

```bash
ollama serve
```

**Bước 2** — khởi động FastAPI server (load model 1 lần):

```bash
conda activate nutrition-rag
python main/rag_server.py
```

**Bước 3** — chạy Spring Boot:

```bash
cd chatbot
./mvnw spring-boot:run
```

Trên Windows nếu cần set JAVA_HOME:

```powershell
$env:JAVA_HOME = "C:\Program Files\Java\jdk-23"
./mvnw spring-boot:run
```

Mở trình duyệt: [http://localhost:8081](http://localhost:8081)

> FastAPI chạy ở port 8000, Spring Boot gọi qua `http://localhost:8000/ask`. Model chỉ load 1 lần khi khởi động FastAPI.

---

## Cấu hình

Sửa `configs/config.yaml`:

```yaml
llm_model: "llama3.1:8b"   # model Ollama
top_k: 5                    # số chunk retrieval
similarity_threshold: 0.5   # ngưỡng lọc ChromaDB
```

---

## Phân công nhóm

| Thành viên | Phụ trách |
|---|---|
| TV1 | Pipeline, Hybrid retrieval (BM25 + ChromaDB + RRF), fine-tune PhoBERT NER, tích hợp LLM |
| TV2 | Thu thập dữ liệu dinh dưỡng & y tế, gán nhãn NER |
| TV3 | Spring Boot UI, tích hợp hệ thống |
