# Vietnamese Nutrition RAG

Hệ thống hỏi đáp dinh dưỡng và sức khỏe bằng tiếng Việt, sử dụng kiến trúc Hybrid RAG.

## Tổng quan

Người dùng đặt câu hỏi tiếng Việt (ví dụ: *"bị tiểu đường nên ăn gì?"*), hệ thống truy xuất thông tin từ 2 nguồn rồi dùng LLM tổng hợp câu trả lời:

- **Nhánh A — SQLite (USDA)**: tra cứu thành phần dinh dưỡng chính xác (13,661 món)
- **Nhánh B — ChromaDB**: tìm kiếm ngữ nghĩa trong tài liệu y tế tiếng Việt (BM25 + cosine + Reciprocal Rank Fusion)

## Cấu trúc thư mục

```
├── main/               # Bản thô ban đầu (không sửa)
├── src/
│   ├── nlp/            # preprocessor, retriever (BM25+ChromaDB), NER, classifier
│   ├── database/       # sqlite_manager, vector_store (ChromaDB)
│   ├── generation/     # generator (Ollama LLM)
│   └── data_pipeline/  # chunker, embedder
├── data/
│   ├── usda_food.db    # SQLite USDA — 13,661 món ăn
│   ├── vi_food_mapping.csv  # Ánh xạ tên Việt → từ khóa Anh
│   └── raw/articles/   # Bài viết y tế tiếng Việt (vinmec, hellobacsi)
├── Interface/chatbot/  # Spring Boot UI (JWT auth, gọi Python qua CLI)
└── configs/config.yaml # Cấu hình tập trung
```

## Yêu cầu

**Python:**
```bash
conda create -n nutrition-rag python=3.10
conda activate nutrition-rag
pip install -r main/requirements.txt
```

**Java:** JDK 21 trở lên

**Ollama:**
```bash
ollama pull qwen2.5:3b
```

## Chạy bản thô (nhanh nhất)

```bash
conda activate nutrition-rag
streamlit run main/app.py
```

Hoặc dùng notebook:
```bash
jupyter notebook main/Run_Project.ipynb
```

## Chạy với Spring Boot UI

**Bước 1 — Khởi động Python backend** (terminal 1):
```bash
conda activate nutrition-rag
```

**Bước 2 — Chạy Spring Boot** (terminal 2):
```bash
cd Interface/chatbot
$env:JAVA_HOME = "C:\Program Files\Java\jdk-23"
./mvnw spring-boot:run
```

Mở trình duyệt: [http://localhost:8081](http://localhost:8081)

## Cấu hình

Sửa `configs/config.yaml` để thay đổi model hoặc đường dẫn:

```yaml
llm_model: "qwen2.5:3b"   # đổi thành "vistral" khi sẵn sàng
llm_backend: "ollama"
top_k: 5
chunk_size: 500
```

## Phân công nhóm

| Thành viên | Phụ trách |
|---|---|
| TV1 | Hybrid retrieval (BM25 + ChromaDB + RRF), fine-tune PhoBERT NER, tích hợp LLM |
| TV2 | Thu thập dữ liệu dinh dưỡng & y tế, gán nhãn NER 300 câu |
| TV3 | Spring Boot UI, tích hợp hệ thống, RAGAS evaluation, demo |
