from __future__ import annotations

import requests


class Generator:
    """Gọi Ollama local để sinh câu trả lời từ retrieved context."""

    def __init__(self, model: str = "qwen2.5:3b", host: str = "http://localhost:11434"):
        self.model = model
        self.host = host.rstrip("/")

    # ------------------------------------------------------------------
    # Prompt builder
    # ------------------------------------------------------------------

    def build_prompt(
        self,
        query: str,
        nutrition_data: dict | None,
        health_chunks: list,
        query_type: str | None = None,
    ) -> str:
        """
        Ghép prompt từ kết quả retrieval.

        nutrition_data: dict từ SqliteManager.lookup() hoặc None
        health_chunks : list of RetrievedChunk (có .text và .source)
        query_type    : "NUTRITION_LOOKUP" | "HEALTH_ADVICE" | "BOTH" | None
        """
        sections = []

        need_nutrition = query_type in (None, "NUTRITION_LOOKUP", "BOTH")
        need_health    = query_type in (None, "HEALTH_ADVICE",    "BOTH")

        if need_nutrition and nutrition_data:
            nutrition_text = (
                f"Món ăn  : {nutrition_data['food_description']}\n"
                f"Chỉ số  : {nutrition_data['nutrient_name']}\n"
                f"Giá trị : {nutrition_data['amount_per_100g']} {nutrition_data['unit']} / 100g\n"
                f"Nguồn   : USDA FoodData Central (id={nutrition_data['fdc_id']})"
            )
            sections.append(f"[Số liệu dinh dưỡng]\n{nutrition_text}")

        if need_health and health_chunks:
            context_text = "\n\n".join(
                f"[{c.source}]\n{c.text[:500]}" for c in health_chunks
            )
            sections.append(f"[Tài liệu tham khảo]\n{context_text}")

        body = "\n\n".join(sections) if sections else "Không có dữ liệu tham khảo."

        return (
            "Bạn là trợ lý dinh dưỡng chuyên nghiệp. Trả lời TRỰC TIẾP bằng tiếng Việt có dấu, đầy đủ và chi tiết.\n"
            "Chỉ viết câu trả lời cuối cùng, không giải thích quá trình suy nghĩ.\n"
            "Cấu trúc câu trả lời: (1) trả lời trực tiếp câu hỏi, (2) giải thích lý do hoặc cơ chế, "
            "(3) gợi ý thực phẩm hoặc lưu ý thực tế nếu phù hợp.\n"
            "Chỉ sử dụng thông tin được cung cấp. Nếu không đủ thông tin, nói rõ giới hạn.\n\n"
            f"{body}\n\n"
            f"Câu hỏi: {query}\n\n"
            "Trả lời (bằng tiếng Việt, kèm nguồn ở cuối):"
        )

    # ------------------------------------------------------------------
    # Generate
    # ------------------------------------------------------------------

    def generate(
        self,
        query: str,
        nutrition_data: dict | None,
        health_chunks: list,
        query_type: str | None = None,
    ) -> dict:
        """
        Gọi Ollama và trả về kết quả.

        Returns:
            {
                "answer": "...",
                "sources": [...],
                "used_llm": True/False
            }
        """
        prompt = self.build_prompt(query, nutrition_data, health_chunks, query_type)
        answer = self._call_ollama(prompt)

        sources = [c.source for c in health_chunks]
        if nutrition_data:
            sources.append(f"USDA FoodData Central (fdc_id={nutrition_data['fdc_id']})")

        if answer is None:
            answer = self._fallback_answer(query, nutrition_data, health_chunks, query_type)
            used_llm = False
        else:
            used_llm = True

        return {
            "answer": answer,
            "sources": sorted(set(sources)),
            "used_llm": used_llm,
        }

    def _call_ollama(self, prompt: str) -> str | None:
        try:
            resp = requests.post(
                f"{self.host}/api/chat",
                json={
                    "model":   self.model,
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                "Bạn là trợ lý tư vấn dinh dưỡng và sức khỏe chuyên nghiệp. "
                                "Nhiệm vụ của bạn là trả lời câu hỏi dựa trên tài liệu khoa học được cung cấp. "
                                "Luôn trả lời bằng tiếng Việt, trực tiếp và đầy đủ. "
                                "Không từ chối trả lời — luôn dựa vào tài liệu được cung cấp để đưa ra thông tin hữu ích."
                            ),
                        },
                        {"role": "user", "content": prompt},
                    ],
                    "stream":  False,
                    "options": {
                        "num_ctx":     4096,
                        "num_predict": 2000,
                        "temperature": 0.3,
                    },
                },
                timeout=180,
            )
            resp.raise_for_status()
            data = resp.json()
            answer = data.get("message", {}).get("content", "").strip()
            return self._strip_thinking(answer) or None
        except Exception:
            return None

    def _call_ollama_generate(self, prompt: str) -> str | None:
        """Fallback dùng /api/generate nếu /api/chat không khả dụng."""
        try:
            resp = requests.post(
                f"{self.host}/api/generate",
                json={
                    "model":   self.model,
                    "prompt":  prompt,
                    "stream":  False,
                    "options": {
                        "num_ctx":     4096,
                        "num_predict": 2000,
                        "temperature": 0.3,
                    },
                },
                timeout=180,
            )
            resp.raise_for_status()
            data = resp.json()
            answer = data.get("response", "").strip()
            if not answer:
                answer = data.get("thinking", "").strip()
            return self._strip_thinking(answer) or None
        except Exception:
            return None

    @staticmethod
    def _strip_thinking(text: str) -> str:
        """Safety net: strip <think> tags nếu có. qwen2.5 không có thinking mode."""
        import re
        if not text:
            return text
        return re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL | re.IGNORECASE).strip() or text

    @staticmethod
    def _fallback_answer(
        query: str,
        nutrition_data: dict | None,
        health_chunks: list,
        query_type: str | None = None,
    ) -> str:
        parts = [f"Câu hỏi: {query}\n"]

        need_nutrition = query_type in (None, "NUTRITION_LOOKUP", "BOTH")
        need_health    = query_type in (None, "HEALTH_ADVICE",    "BOTH")

        if need_nutrition:
            if nutrition_data:
                parts.append(
                    f"Số liệu USDA: {nutrition_data['nutrient_name']} của "
                    f"'{nutrition_data['food_description']}' là "
                    f"{nutrition_data['amount_per_100g']} {nutrition_data['unit']} / 100g."
                )
            else:
                parts.append("Hiện chưa tìm thấy số liệu USDA phù hợp.")

        if need_health:
            if health_chunks:
                parts.append("\nKhuyến nghị từ tài liệu y khoa:")
                for c in health_chunks:
                    parts.append(f"  - {c.text[:300]}  (Nguồn: {c.source})")
            else:
                parts.append("Chưa có tài liệu y khoa phù hợp.")

        return "\n".join(parts)


if __name__ == "__main__":
    g = Generator()
    print("Testing Ollama connection...")
    result = g._call_ollama("Xin chao, ban co hoat dong khong?")
    if result:
        print("OK:", result[:100])
    else:
        print("Ollama offline. Fallback active.")
