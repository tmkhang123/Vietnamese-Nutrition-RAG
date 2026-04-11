"""
Data augmentation cho NER data — entity swap.
Chạy: python data/ner_labels/augment.py
Output: data/ner_labels/ner_data_augmented.csv (300 gốc + ~400 mới)
"""

import csv
import random

random.seed(42)

# -----------------------------------------------------------------------
# Danh sách entity để swap — thêm vào đây nếu muốn đa dạng hơn
# -----------------------------------------------------------------------

SWAP_POOL = {
    "FOOD": [
        "ức_gà", "cá_hồi", "thịt_bò", "trứng_gà", "đậu_phụ",
        "rau_muống", "khoai_lang", "gạo_lứt", "yến_mạch", "chuối",
        "táo", "bưởi", "cà_chua", "cà_rốt", "bắp_cải",
        "tôm", "cá_thu", "óc_chó", "hạt_điều", "đậu_xanh",
        "sữa_chua", "sữa", "bơ", "dưa_hấu", "thịt_heo",
        "cá_ba_sa", "bông_cải_xanh", "hạt_hạnh_nhân",
        "rau_chân_vịt", "đậu_lăng", "hạt_chia",
    ],
    "DISEASE": [
        "tiểu_đường", "gout", "huyết_áp_cao", "cholesterol_cao",
        "béo_phì", "gan_nhiễm_mỡ", "loãng_xương", "thiếu_máu",
        "dạ_dày", "ung_thư", "tim_mạch",
    ],
    "NUTRIENT": [
        "protein", "canxi", "sắt", "kali", "vitamin_C",
        "vitamin_D", "omega-3", "chất_xơ", "magiê", "kẽm",
        "tinh_bột", "chất_béo", "folate", "vitamin_B12", "natri",
    ],
    "SYMPTOM": [
        "đau_đầu", "mệt_mỏi", "buồn_nôn", "đau_khớp", "mất_ngủ",
        "chóng_mặt", "đau_bụng", "khó_tiêu", "tiêu_chảy",
        "sưng_khớp", "chuột_rút", "táo_bón", "đau_cơ", "ợ_nóng",
    ],
}


def token_to_text(token: str) -> str:
    """ức_gà → ức gà"""
    return token.replace("_", " ")


def find_entities(tokens: list[str], labels: list[str]) -> list[tuple[int, str, str]]:
    """Trả về [(index, token, entity_type), ...] cho mỗi B- label."""
    entities = []
    for i, (tok, lab) in enumerate(zip(tokens, labels)):
        if lab.startswith("B-"):
            entity_type = lab[2:]  # B-FOOD → FOOD
            entities.append((i, tok, entity_type))
    return entities


def augment_row(tokens: list[str], labels: list[str], n_swaps: int = 2) -> list[tuple]:
    """
    Với mỗi entity trong câu, tạo n_swaps biến thể bằng cách swap entity đó.
    Trả về list các (tokens_mới, labels_mới).
    """
    entities = find_entities(tokens, labels)
    if not entities:
        return []

    results = []
    seen = set()

    for idx, original_token, entity_type in entities:
        pool = [e for e in SWAP_POOL.get(entity_type, []) if e != original_token]
        if not pool:
            continue

        candidates = random.sample(pool, min(n_swaps, len(pool)))
        for new_token in candidates:
            new_tokens = tokens[:]
            new_tokens[idx] = new_token
            key = " ".join(new_tokens)
            if key not in seen:
                seen.add(key)
                results.append((new_tokens, labels))  # labels không đổi

    return results


def tokens_to_sentence(tokens: list[str]) -> str:
    """Dựng lại sentence từ tokens (bỏ dấu câu dính vào từ trước)."""
    words = []
    for tok in tokens:
        text = token_to_text(tok)
        if text in ("?", ".", ",", "!"):
            if words:
                words[-1] = words[-1] + text
        else:
            words.append(text)
    # Capitalize chữ đầu
    sentence = " ".join(words)
    return sentence[0].upper() + sentence[1:] if sentence else sentence


# -----------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------

INPUT  = "data/ner_labels/ner_data.csv"
OUTPUT = "data/ner_labels/ner_data_augmented.csv"

rows = []
with open(INPUT, encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        rows.append(row)

augmented = []
new_id = len(rows) + 1

for row in rows:
    tokens = row["tokens"].split()
    labels = row["labels"].split()

    for new_tokens, new_labels in augment_row(tokens, labels, n_swaps=2):
        augmented.append({
            "id":       new_id,
            "sentence": tokens_to_sentence(new_tokens),
            "tokens":   " ".join(new_tokens),
            "labels":   " ".join(new_labels),
        })
        new_id += 1

print(f"Gốc   : {len(rows)} câu")
print(f"Thêm  : {len(augmented)} câu")
print(f"Tổng  : {len(rows) + len(augmented)} câu")

with open(OUTPUT, "w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["id", "sentence", "tokens", "labels"])
    writer.writeheader()
    writer.writerows(rows)      # giữ nguyên 300 câu gốc
    writer.writerows(augmented) # thêm câu mới vào sau

print(f"Saved → {OUTPUT}")
