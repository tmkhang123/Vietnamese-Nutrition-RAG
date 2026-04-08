from __future__ import annotations

import json
import sys

from pipeline import (
    DEFAULT_TOP_K,
    NutritionRAGSystem,
    UsdaLookupError,
    classify_intent,
    extract_entities,
)

# Ensure Python writes JSON as UTF-8 on Windows consoles (avoids UnicodeEncodeError).
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


def main() -> None:
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Missing query"}))
        return

    query = sys.argv[1]
    bot = NutritionRAGSystem()

    # Reuse the same pipeline logic, but return extra fields for the Java UI
    entities = extract_entities(query, bot.known_foods)
    intent = classify_intent(query, entities)

    nutrition_data = None
    try:
        if entities.foods and entities.nutrients:
            nutrition_data = bot.usda_repo.lookup_food_nutrient(entities.foods[0], entities.nutrients[0])
    except UsdaLookupError:
        nutrition_data = None

    contexts = bot.retriever.retrieve(query, top_k=DEFAULT_TOP_K)
    prompt = bot._build_prompt(query, nutrition_data, contexts)
    generated = bot.generator.generate(prompt)
    final_answer = generated or bot._fallback_answer(query, nutrition_data, contexts)

    sources = [c.source for c in contexts]
    if nutrition_data:
        sources.append(f"USDA FoodData Central (fdc_id={nutrition_data['fdc_id']})")

    energy = None
    # `entities.nutrients` stores canonical nutrient keys (e.g. "Energy")
    if nutrition_data and entities.nutrients and entities.nutrients[0] == "Energy":
        energy = {
            "amountPer100g": nutrition_data.get("amount_per_100g"),
            "unitName": nutrition_data.get("unit_name"),
        }

    output = {
        "answer": final_answer,
        "intent": intent,
        "entities": {
            "foods": entities.foods,
            "diseases": entities.diseases,
            "nutrients": entities.nutrients,
        },
        "sources": sorted(set(sources)),
        "energy": energy,
    }
    print(json.dumps(output, ensure_ascii=False))


if __name__ == "__main__":
    main()

