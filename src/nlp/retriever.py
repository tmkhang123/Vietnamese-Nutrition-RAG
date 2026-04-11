from __future__ import annotations

from rank_bm25 import BM25Okapi

from src.database.vector_store import VectorStore, RetrievedChunk


def _tokenize_vi(text: str) -> list[str]:
    """Tách từ tiếng Việt bằng underthesea.
    Fallback sang .split() nếu underthesea chưa cài.
    Dùng cho BM25 — 'tiểu đường' thành 1 token 'tiểu_đường' thay vì 2 token rời.
    """
    try:
        from underthesea import word_tokenize
        return word_tokenize(text, format="text").split()
    except ImportError:
        return text.split()


class HybridRetriever:
    # BM25 bắt tên riêng/thuật ngữ tốt hơn semantic,
    # semantic bắt câu cùng nghĩa khác từ tốt hơn BM25.
    # Kết hợp qua RRF để tận dụng cả hai.

    def __init__(
        self,
        vector_store: VectorStore,
        top_k: int = 5,
        rrf_k: int = 60,
        score_threshold: float = 0.3,
    ):
        self.vs              = vector_store
        self.top_k           = top_k
        self.rrf_k           = rrf_k       # k=60 là giá trị mặc định trong paper gốc RRF
        self.score_threshold = score_threshold  # loại chunk kém liên quan trước khi vào prompt

        self._bm25:        BM25Okapi | None = None
        self._bm25_chunks: list[dict]       = []

    def build_bm25_index(self, chunks: list[dict]) -> None:
        self._bm25_chunks = chunks
        # Dùng underthesea để "tiểu đường" → token "tiểu_đường", khớp đúng hơn với .split()
        self._bm25 = BM25Okapi([_tokenize_vi(c["text"]) for c in chunks])

    def sync_bm25_from_store(self) -> None:
        chunks = self.vs.get_all_chunks()
        if chunks:
            self.build_bm25_index(chunks)

    def _bm25_search(self, query: str, top_k: int) -> list[RetrievedChunk]:
        if self._bm25 is None:
            return []

        # Tokenize query cùng cách với lúc index để khớp "tiểu_đường" → "tiểu_đường"
        scores = self._bm25.get_scores(_tokenize_vi(query))
        ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)

        return [
            RetrievedChunk(
                text=self._bm25_chunks[idx]["text"],
                source=self._bm25_chunks[idx]["source"],
                score=float(score),
            )
            for idx, score in ranked[:top_k]
        ]

    def _rrf(
        self,
        bm25_list:     list[RetrievedChunk],
        semantic_list: list[RetrievedChunk],
    ) -> list[RetrievedChunk]:
        # Chunk xuất hiện ở cả hai list được cộng điểm từ cả hai → nổi lên top
        rrf_scores: dict[str, float]          = {}
        chunk_map:  dict[str, RetrievedChunk] = {}

        for lst in (bm25_list, semantic_list):
            for rank, chunk in enumerate(lst):
                key = chunk.text
                rrf_scores[key] = rrf_scores.get(key, 0.0) + 1.0 / (self.rrf_k + rank)
                chunk_map[key]  = chunk

        merged = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
        return [
            RetrievedChunk(text=k, source=chunk_map[k].source, score=s)
            for k, s in merged[: self.top_k]
        ]

    def retrieve(self, query: str) -> list[RetrievedChunk]:
        query_for_semantic = query.replace("_", " ")  # corpus embed raw text, không có underscore
        semantic = self.vs.query(query_for_semantic, top_k=self.top_k)
        bm25     = self._bm25_search(query, top_k=self.top_k)

        if not semantic and not bm25:
            return []

        merged = self._rrf(bm25, semantic)

        # Lọc chunk kém liên quan — tránh đưa bài không liên quan vào prompt LLM
        filtered = [c for c in merged if c.score >= self.score_threshold]
        return filtered if filtered else merged[:1]  # giữ ít nhất 1 nếu tất cả dưới threshold


if __name__ == "__main__":
    vs = VectorStore()
    retriever = HybridRetriever(vs, top_k=3)
    retriever.sync_bm25_from_store()

    q = "bị tiểu đường nên ăn gì?"
    for r in retriever.retrieve(q):
        print(f"[{r.score:.4f}] {r.text[:70]}...")
