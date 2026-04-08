from __future__ import annotations

import csv
import json
import re
import sqlite3
import unicodedata
from dataclasses import dataclass
from pathlib import Path

import requests

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity

    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


CODE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = CODE_DIR.parent
DATA_DIR = PROJECT_DIR / "data"
USDA_CSV_DIR = (
    PROJECT_DIR
    / "FoodData_Central_csv_2025-12-18"
    / "FoodData_Central_csv_2025-12-18"
)
SQLITE_PATH = DATA_DIR / "usda_food.db"
VI_FOOD_MAPPING_PATH = DATA_DIR / "vi_food_mapping.csv"
MEDICAL_DOCS_PATH = DATA_DIR / "medical_knowledge.jsonl"

DEFAULT_TOP_K = 3
DEFAULT_OLLAMA_MODEL = "qwen2.5:3b"


@dataclass
class QueryEntities:
    foods: list[str]
    diseases: list[str]
    nutrients: list[str]


@dataclass
class RetrievedChunk:
    text: str
    source: str
    score: float


@dataclass
class RAGAnswer:
    answer: str
    intent: str
    entities: dict
    sources: list[str]


NUTRIENT_ALIASES: dict[str, list[str]] = {
    "Protein": ["protein", "dam", "chất đạm"],
    "Energy": ["calo", "năng lượng", "kcal", "bao nhiêu calo"],
    "Carbohydrate, by difference": ["carb", "carbohydrate", "tinh bột"],
    "Total lipid (fat)": ["fat", "chất béo", "lipid", "mỡ"],
    "Fiber, total dietary": ["chất xơ", "fiber", "xơ"],
    "Sugars, Total": ["đường", "sugar", "sugars"],
    "Sodium, Na": ["natri", "sodium", "muối"],
}

DISEASE_KEYWORDS = [
    "tiểu đường",
    "gout",
    "cao huyết áp",
    "tim mạch",
    "mỡ máu",
    "gan nhiễm mỡ",
]

LOOKUP_KEYWORDS = ["bao nhiêu", "hàm lượng", "chứa", "có bao nhiêu", "cung cấp"]
ADVICE_KEYWORDS = ["nên ăn", "kiêng", "có tốt không", "an toàn không", "có nên"]


def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFC", text)
    text = text.strip().lower()
    text = re.sub(r"\s+", " ", text)
    return text


def load_vi_food_names(mapping_path: Path) -> list[str]:
    foods: list[str] = []
    if not mapping_path.exists():
        return foods

    with mapping_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            vi_name = normalize_text(row.get("vi_name", ""))
            if vi_name:
                foods.append(vi_name)

    return sorted(set(foods))


def extract_entities(query: str, known_foods: list[str]) -> QueryEntities:
    normalized = normalize_text(query)

    found_foods = [f for f in known_foods if f in normalized]
    found_diseases = [d for d in DISEASE_KEYWORDS if d in normalized]

    found_nutrients: list[str] = []
    for canonical_name, aliases in NUTRIENT_ALIASES.items():
        if any(alias in normalized for alias in aliases):
            found_nutrients.append(canonical_name)

    return QueryEntities(
        foods=sorted(set(found_foods)),
        diseases=sorted(set(found_diseases)),
        nutrients=sorted(set(found_nutrients)),
    )


def classify_intent(query: str, entities: QueryEntities) -> str:
    normalized = normalize_text(query)

    has_lookup_words = any(word in normalized for word in LOOKUP_KEYWORDS)
    has_advice_words = any(word in normalized for word in ADVICE_KEYWORDS)

    if entities.foods and entities.nutrients and has_lookup_words:
        return "lookup"
    if entities.diseases or has_advice_words:
        return "advice"
    if entities.foods and entities.nutrients:
        return "lookup"
    return "advice"


class UsdaLookupError(Exception):
    pass


class UsdaRepository:
    def __init__(self, db_path: Path, vi_mapping_path: Path):
        self.db_path = db_path
        self.vi_mapping = self._load_mapping(vi_mapping_path)

    @staticmethod
    def _load_mapping(mapping_path: Path) -> dict[str, str]:
        if not mapping_path.exists():
            return {}
        mapping: dict[str, str] = {}
        with mapping_path.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                vi_name = row.get("vi_name", "").strip().lower()
                en_keyword = row.get("en_keyword", "").strip().lower()
                if vi_name and en_keyword:
                    mapping[vi_name] = en_keyword
        return mapping

    def _connect(self) -> sqlite3.Connection:
        if not self.db_path.exists():
            raise UsdaLookupError(
                f"Database not found at {self.db_path}. Please run build_usda_db.py first."
            )
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _resolve_food_keyword(self, vi_food_name: str) -> str:
        normalized = vi_food_name.strip().lower()
        return self.vi_mapping.get(normalized, normalized)

    def find_best_food(self, vi_food_name: str) -> sqlite3.Row | None:
        keyword = self._resolve_food_keyword(vi_food_name)
        query = """
            SELECT fdc_id, description, data_type
            FROM foods
            WHERE LOWER(description) LIKE ?
            ORDER BY
                CASE WHEN data_type = 'foundation_food' THEN 0 ELSE 1 END,
                LENGTH(description) ASC
            LIMIT 1
        """
        with self._connect() as conn:
            return conn.execute(query, (f"%{keyword}%",)).fetchone()

    def get_nutrient_amount(self, fdc_id: int, nutrient_name: str) -> dict | None:
        query = """
            SELECT n.name, n.unit_name, fn.amount
            FROM food_nutrients fn
            JOIN nutrients n ON fn.nutrient_id = n.id
            WHERE fn.fdc_id = ? AND LOWER(n.name) = LOWER(?)
            LIMIT 1
        """
        with self._connect() as conn:
            row = conn.execute(query, (fdc_id, nutrient_name)).fetchone()
            if not row:
                return None
            return {
                "nutrient_name": row["name"],
                "unit_name": row["unit_name"],
                "amount_per_100g": row["amount"],
            }

    def lookup_food_nutrient(self, vi_food_name: str, nutrient_name: str) -> dict | None:
        food = self.find_best_food(vi_food_name)
        if not food:
            return None

        nutrient = self.get_nutrient_amount(food["fdc_id"], nutrient_name)
        if not nutrient:
            return None

        return {
            "fdc_id": food["fdc_id"],
            "food_description": food["description"],
            "data_type": food["data_type"],
            **nutrient,
        }


class SemanticRetriever:
    def __init__(self, docs_path: Path):
        self.docs = self._load_docs(docs_path)
        self.vectorizer = None
        self.matrix = None

        if SKLEARN_AVAILABLE and self.docs:
            self.vectorizer = TfidfVectorizer(ngram_range=(1, 2))
            self.matrix = self.vectorizer.fit_transform([d["text"] for d in self.docs])

    @staticmethod
    def _load_docs(docs_path: Path) -> list[dict]:
        if not docs_path.exists():
            return []
        docs: list[dict] = []
        with docs_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                item = json.loads(line)
                if item.get("text") and item.get("source"):
                    docs.append(item)
        return docs

    def retrieve(self, query: str, top_k: int = 3) -> list[RetrievedChunk]:
        if not self.docs:
            return []
        if self.matrix is not None and self.vectorizer is not None:
            q_vec = self.vectorizer.transform([query])
            scores = cosine_similarity(q_vec, self.matrix)[0]
            ranked_indices = scores.argsort()[::-1][:top_k]
            return [
                RetrievedChunk(
                    text=self.docs[i]["text"],
                    source=self.docs[i]["source"],
                    score=float(scores[i]),
                )
                for i in ranked_indices
            ]

        query_tokens = set(query.lower().split())
        scored: list[tuple[int, float]] = []
        for idx, doc in enumerate(self.docs):
            doc_tokens = set(doc["text"].lower().split())
            overlap = len(query_tokens.intersection(doc_tokens))
            score = overlap / max(len(query_tokens), 1)
            scored.append((idx, score))
        scored.sort(key=lambda x: x[1], reverse=True)

        return [
            RetrievedChunk(
                text=self.docs[idx]["text"],
                source=self.docs[idx]["source"],
                score=score,
            )
            for idx, score in scored[:top_k]
        ]


class OllamaGenerator:
    def __init__(self, model: str, host: str = "http://localhost:11434"):
        self.model = model
        self.host = host.rstrip("/")

    def generate(self, prompt: str) -> str | None:
        url = f"{self.host}/api/generate"
        payload = {"model": self.model, "prompt": prompt, "stream": False}
        try:
            response = requests.post(url, json=payload, timeout=120)
            response.raise_for_status()
            data = response.json()
            return data.get("response", "").strip() or None
        except Exception:
            return None


class NutritionRAGSystem:
    def __init__(self, model_name: str = DEFAULT_OLLAMA_MODEL):
        self.known_foods = load_vi_food_names(VI_FOOD_MAPPING_PATH)
        self.retriever = SemanticRetriever(MEDICAL_DOCS_PATH)
        self.usda_repo = UsdaRepository(SQLITE_PATH, VI_FOOD_MAPPING_PATH)
        self.generator = OllamaGenerator(model_name)

    def _build_prompt(self, user_query: str, nutrition_data: dict | None, contexts: list) -> str:
        nutrition_text = "Khong co so lieu USDA phu hop."
        if nutrition_data:
            nutrition_text = (
                f"Mon: {nutrition_data['food_description']}\n"
                f"Chi so: {nutrition_data['nutrient_name']}\n"
                f"Gia tri: {nutrition_data['amount_per_100g']} {nutrition_data['unit_name']} tren 100g\n"
                f"Nguon du lieu: USDA ({nutrition_data['fdc_id']})"
            )

        context_text = "\n\n".join([f"- ({c.source}) {c.text}" for c in contexts])
        if not context_text:
            context_text = "Khong co ngu canh y khoa."

        return f"""
Ban la tro ly dinh duong. Tra loi bang tieng Viet, ro rang va ngan gon.
Neu du lieu khong du, noi ro gioi han.

Cau hoi nguoi dung:
{user_query}

So lieu dinh duong co cau truc:
{nutrition_text}

Ngu canh y khoa:
{context_text}

Yeu cau:
1) Tra loi truc tiep vao cau hoi.
2) Neu co so lieu USDA thi ghi ro don vi va theo 100g.
3) Dua muc 'Nguon tham khao' o cuoi cau tra loi.
"""

    @staticmethod
    def _fallback_answer(query: str, nutrition_data: dict | None, contexts: list) -> str:
        parts = [f"Cau hoi: {query}"]

        if nutrition_data:
            parts.append(
                "So lieu USDA: "
                f"{nutrition_data['nutrient_name']} cua '{nutrition_data['food_description']}' "
                f"la {nutrition_data['amount_per_100g']} {nutrition_data['unit_name']} tren 100g."
            )
        else:
            parts.append("Hien chua tim thay so lieu USDA phu hop cho mon hoac chi so ban hoi.")

        if contexts:
            parts.append("Khuyen nghi tong quat tu tai lieu y khoa:")
            for chunk in contexts:
                parts.append(f"- {chunk.text} (Nguon: {chunk.source})")
        else:
            parts.append("Chua co tai lieu y khoa phu hop de tu van sau hon.")

        return "\n".join(parts)

    def answer(self, query: str) -> RAGAnswer:
        entities = extract_entities(query, self.known_foods)
        intent = classify_intent(query, entities)

        nutrition_data = None
        if entities.foods and entities.nutrients:
            try:
                nutrition_data = self.usda_repo.lookup_food_nutrient(
                    entities.foods[0], entities.nutrients[0]
                )
            except UsdaLookupError:
                nutrition_data = None

        contexts = self.retriever.retrieve(query, top_k=DEFAULT_TOP_K)
        prompt = self._build_prompt(query, nutrition_data, contexts)
        generated = self.generator.generate(prompt)

        final_answer = generated or self._fallback_answer(query, nutrition_data, contexts)
        sources = [c.source for c in contexts]
        if nutrition_data:
            sources.append(f"USDA FoodData Central (fdc_id={nutrition_data['fdc_id']})")

        return RAGAnswer(
            answer=final_answer,
            intent=intent,
            entities={
                "foods": entities.foods,
                "diseases": entities.diseases,
                "nutrients": entities.nutrients,
            },
            sources=sorted(set(sources)),
        )
