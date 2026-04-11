"""
Nạp các bài JSON trong data/raw/articles/ vào ChromaDB.
Dùng manifest để tránh embed trùng lặp.

    python -m src.data_pipeline.embed_articles          # chỉ embed file mới
    python -m src.data_pipeline.embed_articles --reset  # xóa sạch và embed lại toàn bộ
"""

from __future__ import annotations

import json
import os
import sys
import yaml

from src.database.vector_store import VectorStore
from src.data_pipeline.embedder import Embedder


MANIFEST_FILE = "data/.embedded_manifest.json"


def load_manifest(root: str) -> set[str]:
    path = os.path.join(root, MANIFEST_FILE)
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return set(json.load(f))
    return set()


def save_manifest(root: str, embedded: set[str]) -> None:
    path = os.path.join(root, MANIFEST_FILE)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(sorted(embedded), f, ensure_ascii=False, indent=2)


def main():
    reset = "--reset" in sys.argv

    ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    with open(os.path.join(ROOT, "configs", "config.yaml"), encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    articles_dir = os.path.join(ROOT, "data", "raw", "articles")
    if not os.path.isdir(articles_dir) or not os.listdir(articles_dir):
        print(f"[!] Chưa có bài nào trong {articles_dir}")
        return

    vs = VectorStore(
        persist_dir=os.path.join(ROOT, cfg["chroma_persist_dir"]),
        collection_name=cfg["chroma_collection"],
        embedding_model=cfg["embedding_model"],
    )

    if reset:
        print("--reset: xóa toàn bộ ChromaDB và embed lại...")
        vs.clear()
        # Re-embed medical_knowledge.jsonl trước
        from src.data_pipeline.embedder import Embedder as _E
        med_path = os.path.join(ROOT, cfg["medical_docs_path"])
        if os.path.exists(med_path):
            n = _E(vs).embed_jsonl(med_path)
            print(f"  Re-embed medical_knowledge: {n} chunks")
        embedded = set()
    else:
        embedded = load_manifest(ROOT)

    all_files = sorted(
        f for f in os.listdir(articles_dir)
        if f.endswith((".json", ".txt"))
    )
    new_files = [f for f in all_files if f not in embedded]

    if not new_files:
        print(f"Không có file mới. ChromaDB hiện có {vs.count()} chunks.")
        print("Dùng --reset để embed lại toàn bộ.")
        return

    print(f"File mới cần embed: {len(new_files)}/{len(all_files)}")

    # Tạo thư mục tạm chỉ chứa file mới để chunk
    import tempfile, shutil
    with tempfile.TemporaryDirectory() as tmp:
        for fname in new_files:
            shutil.copy(os.path.join(articles_dir, fname), os.path.join(tmp, fname))

        before = vs.count()
        embedder = Embedder(vs, chunk_size=cfg["chunk_size"], chunk_overlap=cfg["chunk_overlap"])
        n = embedder.embed_directory(tmp)

    print(f"Đã nạp {n} chunks mới")
    print(f"ChromaDB: {before} → {vs.count()} chunks")

    embedded.update(new_files)
    save_manifest(ROOT, embedded)


if __name__ == "__main__":
    main()
