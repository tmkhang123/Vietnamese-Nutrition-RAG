import sys
sys.path.insert(0, "main")

from pipeline import extract_entities, classify_intent, load_vi_food_names, VI_FOOD_MAPPING_PATH

known_foods = load_vi_food_names(VI_FOOD_MAPPING_PATH)
print(f"Da load {len(known_foods)} ten mon an\n")

queries = [
    "100g uc ga co bao nhieu protein?",
    "nguoi bi tieu duong co nen an pho khong?",
    "rau muong chua bao nhieu calo?",
    "bi gout nen kieng gi?",
]

for q in queries:
    entities = extract_entities(q, known_foods)
    intent = classify_intent(q, entities)
    print(f"Cau hoi : {q}")
    print(f"  Foods   : {entities.foods}")
    print(f"  Benh    : {entities.diseases}")
    print(f"  Duong CL: {entities.nutrients}")
    print(f"  Intent  : {intent}")
    print()
