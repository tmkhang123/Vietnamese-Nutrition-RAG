"""
Tải và filter dataset từ HuggingFace:
  - urnus11/Vietnamese-Healthcare  → articles Vinmec → ChromaDB
  - hungnm/vietnamese-medical-qa   → test set evaluation

Cài trước: pip install datasets

Chạy:
    python -m src.data_pipeline.load_hf_dataset
"""

from __future__ import annotations

import json
import os

# -------------------------------------------------------
# Từ khóa filter bài liên quan đến dinh dưỡng / bệnh mãn tính
# -------------------------------------------------------
# Ưu tiên bài tư vấn dinh dưỡng thực tế — người dùng hay hỏi
HIGH_PRIORITY = [
    "dinh dưỡng", "thực phẩm", "ăn uống", "lợi ích",
    "tốt cho sức khỏe", "giàu protein", "giàu vitamin", "giàu canxi", "giàu sắt",
    "nên ăn gì", "ăn gì tốt", "thực đơn",
    "vitamin", "khoáng chất", "chất xơ", "omega", "protein",
    "calo", "năng lượng", "dinh dưỡng cho",
    "bà bầu", "trẻ em", "người già", "tập thể dục", "giảm cân", "tăng cân",
    "ăn chay", "thực dưỡng", "chế độ ăn lành mạnh",
]

# Dùng để filter phụ — chỉ lấy nếu kết hợp với HIGH_PRIORITY
LOW_PRIORITY = [
    "tiểu đường", "huyết áp", "gout", "cholesterol",
    "thiếu máu", "loãng xương", "dạ dày",
]

ALL_KEYWORDS = HIGH_PRIORITY + LOW_PRIORITY

MAX_ARTICLES = 150  # giới hạn số bài lưu xuống


def relevance_score(text: str) -> int:
    """Đếm số keyword HIGH_PRIORITY khớp — bài càng liên quan dinh dưỡng càng cao điểm."""
    t = text.lower()
    return sum(1 for kw in HIGH_PRIORITY if kw in t)

def is_relevant(text: str) -> bool:
    t = text.lower()
    return any(kw in t for kw in ALL_KEYWORDS)


def load_vinmec_articles(out_dir: str) -> int:
    """
    Tải urnus11/Vietnamese-Healthcare, lấy vinmec_article_main,
    filter bài liên quan dinh dưỡng/bệnh → lưu JSON vào out_dir.
    """
    from datasets import load_dataset

    print("Loading urnus11/Vietnamese-Healthcare ...")
    ds = load_dataset("urnus11/Vietnamese-Healthcare", trust_remote_code=True)
    print(f"Splits có sẵn: {list(ds.keys())}")

    # Thử lấy split phù hợp
    split_name = None
    for candidate in ["vinmec_article_main", "train", "vinmec"]:
        if candidate in ds:
            split_name = candidate
            break
    if split_name is None:
        split_name = list(ds.keys())[0]

    data = ds[split_name]
    print(f"Split '{split_name}': {len(data)} bản ghi")
    print(f"Columns: {data.column_names}")

    os.makedirs(out_dir, exist_ok=True)

    # Thu thập + chấm điểm trước, lấy top MAX_ARTICLES
    candidates = []
    for i, row in enumerate(data):
        text = (
            row.get("content") or row.get("text") or
            row.get("body") or row.get("article") or ""
        )
        title = row.get("title") or row.get("name") or f"vinmec_{i}"
        source = row.get("source", "Vinmec")

        if not text or len(text) < 200:
            continue

        combined = f"{title} {text}"
        if not is_relevant(combined):
            continue

        score = relevance_score(combined)
        candidates.append((score, i, title, text, source))

    # Sắp xếp theo điểm cao nhất, lấy top MAX_ARTICLES
    candidates.sort(key=lambda x: x[0], reverse=True)
    top = candidates[:MAX_ARTICLES]

    print(f"Found {len(candidates)} relevant articles, saving top {len(top)}")

    for score, i, title, text, source in top:
        filename = f"vinmec_{i:05d}.json"
        with open(os.path.join(out_dir, filename), "w", encoding="utf-8") as f:
            json.dump(
                {"text": f"{title}\n\n{text}".strip(), "source": source or "Vinmec"},
                f, ensure_ascii=False, indent=2
            )

    print(f"Đã lưu {len(top)} bài vào {out_dir}")
    return len(top)


def export_test_questions(out_path: str, n: int = 30) -> int:
    """
    Tải hungnm/vietnamese-medical-qa, lấy n câu hỏi liên quan dinh dưỡng
    → lưu JSONL để dùng làm test set evaluation.
    """
    from datasets import load_dataset

    print("\nLoading hungnm/vietnamese-medical-qa ...")
    ds = load_dataset("hungnm/vietnamese-medical-qa", trust_remote_code=True)

    split_name = list(ds.keys())[0]
    data = ds[split_name]
    print(f"Split '{split_name}': {len(data)} cặp hỏi-đáp")
    print(f"Columns: {data.column_names}")

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    saved = 0

    with open(out_path, "w", encoding="utf-8") as f:
        for row in data:
            if saved >= n:
                break
            question = row.get("question") or row.get("input") or row.get("q") or ""
            answer   = row.get("answer") or row.get("output") or row.get("a") or ""
            if not question:
                continue
            if not is_relevant(question):
                continue
            f.write(json.dumps(
                {"question": question, "reference_answer": answer},
                ensure_ascii=False
            ) + "\n")
            saved += 1

    print(f"Đã lưu {saved} câu hỏi test vào {out_path}")
    return saved


def main():
    ROOT     = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    OUT_DIR  = os.path.join(ROOT, "data", "raw", "articles")
    TEST_OUT = os.path.join(ROOT, "data", "test_questions.jsonl")

    print("--- Vinmec articles → data/raw/articles/ ---")
    try:
        load_vinmec_articles(OUT_DIR)
    except Exception as e:
        print(f"[!] Vinmec error: {e}")

    print("\n--- Medical Q&A → data/test_questions.jsonl ---")
    try:
        export_test_questions(TEST_OUT, n=30)
    except Exception as e:
        print(f"[!] QA dataset error: {e}")

    print("\nXong. Chạy tiếp:")
    print("  python -m src.data_pipeline.embed_articles")


if __name__ == "__main__":
    main()
