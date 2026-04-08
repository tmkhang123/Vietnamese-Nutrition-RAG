from __future__ import annotations

import requests


class Generator:
    """
    Sinh cau tra loi bang Ollama LLM (chay local).
    Tach ra tu OllamaGenerator trong main/pipeline.py,
    them prompt template ro rang hon theo technical_spec.
    """

    def __init__(self, model: str = "qwen2.5:3b", host: str = "http://localhost:11434"):
        self.model = model
        self.host = host.rstrip("/")

    # ------------------------------------------------------------------
    # Prompt builder
    # ------------------------------------------------------------------

    def build_prompt(self, query: str, nutrition_data: dict | None, health_chunks: list) -> str:
        """
        Ghep prompt tu ket qua retrieval.

        nutrition_data: dict tu SqliteManager.lookup() hoac None
        health_chunks : list of RetrievedChunk (co .text va .source)
        """
        if nutrition_data:
            nutrition_text = (
                f"Mon an  : {nutrition_data['food_description']}\n"
                f"Chi so  : {nutrition_data['nutrient_name']}\n"
                f"Gia tri : {nutrition_data['amount_per_100g']} {nutrition_data['unit']} tren 100g\n"
                f"Nguon   : USDA FoodData Central (id={nutrition_data['fdc_id']})"
            )
        else:
            nutrition_text = "Khong co so lieu USDA phu hop."

        if health_chunks:
            context_text = "\n\n".join(
                f"[{c.source}]\n{c.text}" for c in health_chunks
            )
        else:
            context_text = "Khong co tai lieu y khoa lien quan."

        return f"""Ban la tro ly dinh duong. Tra loi bang tieng Viet, ro rang va ngan gon.
Chi su dung thong tin duoc cung cap. Neu khong du thong tin, noi ro gioi han.

[Thong tin dinh duong]
{nutrition_text}

[Tai lieu tham khao]
{context_text}

Cau hoi: {query}

Tra loi (kem nguon tham khao o cuoi):"""

    # ------------------------------------------------------------------
    # Generate
    # ------------------------------------------------------------------

    def generate(self, query: str, nutrition_data: dict | None, health_chunks: list) -> dict:
        """
        Goi Ollama va tra ve ket qua.

        Returns:
            {
                "answer": "...",
                "sources": [...],
                "used_llm": True/False
            }
        """
        prompt = self.build_prompt(query, nutrition_data, health_chunks)
        answer = self._call_ollama(prompt)

        sources = [c.source for c in health_chunks]
        if nutrition_data:
            sources.append(f"USDA FoodData Central (fdc_id={nutrition_data['fdc_id']})")

        if answer is None:
            answer = self._fallback_answer(query, nutrition_data, health_chunks)
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
                f"{self.host}/api/generate",
                json={"model": self.model, "prompt": prompt, "stream": False},
                timeout=120,
            )
            resp.raise_for_status()
            return resp.json().get("response", "").strip() or None
        except Exception:
            return None

    @staticmethod
    def _fallback_answer(query: str, nutrition_data: dict | None, health_chunks: list) -> str:
        parts = [f"Cau hoi: {query}\n"]

        if nutrition_data:
            parts.append(
                f"So lieu USDA: {nutrition_data['nutrient_name']} cua "
                f"'{nutrition_data['food_description']}' la "
                f"{nutrition_data['amount_per_100g']} {nutrition_data['unit']} tren 100g."
            )
        else:
            parts.append("Hien chua tim thay so lieu USDA phu hop.")

        if health_chunks:
            parts.append("\nKhuyen nghi tu tai lieu y khoa:")
            for c in health_chunks:
                parts.append(f"  - {c.text}  (Nguon: {c.source})")
        else:
            parts.append("Chua co tai lieu y khoa phu hop.")

        return "\n".join(parts)


if __name__ == "__main__":
    g = Generator()
    print("Kiem tra ket noi Ollama...")
    result = g._call_ollama("Xin chao, ban co hoat dong khong?")
    if result:
        print("Ollama OK:", result[:100])
    else:
        print("Ollama chua chay hoac chua cai. Fallback mode se duoc dung.")
