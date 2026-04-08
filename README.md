# He thong hoi dap dinh duong (Hybrid RAG)

Ban toi gian hien tai: de chay nhanh, de demo, de nop.

## File quan trong

Tat ca file code da duoc dua vao thu muc `main/`.

- `main/Run_Project.ipynb`: notebook chay project tu A-Z (khuyen dung).
- `main/app.py`: giao dien chat Streamlit.
- `main/pipeline.py`: pipeline chinh (NLP + USDA lookup + semantic retrieval + generation).
- `main/build_usda_db.py`: tao `usda_food.db` tu USDA CSV.
- `vi_food_mapping.csv`: mapping ten mon Viet -> tu khoa Anh.
- `medical_knowledge.jsonl`: tap van ban y khoa mau.
- `main/requirements.txt`: thu vien can cai.
- `FoodData_Central_csv_2025-12-18/...`: du lieu USDA goc.

## Cach chay khuyen nghi (Notebook)

### 1) Cai thu vien

```bash
pip install -r main/requirements.txt
```

### 2) Mo notebook

Mo `main/Run_Project.ipynb`, sau do chay lan luot tung cell.

Notebook da co san cac buoc:
- set working directory,
- build `usda_food.db` neu chua co,
- khoi tao he thong,
- test cau hoi mau.

## Cach chay bang command line

### 1) Tao database

```bash
python main/build_usda_db.py
```

### 2) Chay Streamlit app

```bash
streamlit run main/app.py
```

## Tuy chon Ollama (LLM local)

- Neu muon sinh cau tra loi bang LLM local:
  - `ollama pull qwen2.5:3b`
- Neu chua co Ollama, he thong van chay voi fallback answer.

## Mo rong du lieu

- Bo sung mapping trong `vi_food_mapping.csv` de tra USDA dung hon.
- Them tai lieu vao `medical_knowledge.jsonl` de tang chat luong tư van.
