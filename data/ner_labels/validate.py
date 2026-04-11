"""
Kiểm tra ner_data_augmented.csv trước khi đưa vào fine-tune.
Chạy: python data/ner_labels/validate.py
"""

import csv

VALID_LABELS = {"O", "B-FOOD", "B-DISEASE", "B-NUTRIENT", "B-SYMPTOM"}
FILE = "data/ner_labels/ner_data_augmented.csv"

errors = []

with open(FILE, encoding="utf-8") as f:
    for row in csv.DictReader(f):
        row_id = row["id"]
        tokens = row["tokens"].split()
        labels = row["labels"].split()

        # token count != label count
        if len(tokens) != len(labels):
            errors.append(f"[{row_id}] token={len(tokens)} label={len(labels)} LỆCH")
            continue

        # label không hợp lệ
        bad = [l for l in labels if l not in VALID_LABELS]
        if bad:
            errors.append(f"[{row_id}] label lạ: {bad}")

        # dòng rỗng
        if not tokens:
            errors.append(f"[{row_id}] tokens rỗng")

if errors:
    print(f"Tìm thấy {len(errors)} lỗi:\n")
    for e in errors:
        print(" ", e)
else:
    print(f"OK — không có lỗi trong {FILE}")
