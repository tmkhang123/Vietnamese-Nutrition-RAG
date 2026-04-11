from __future__ import annotations

import os
from typing import Dict, List, Optional

import torch
from transformers import AutoModelForTokenClassification, AutoTokenizer


class NERModel:
    """
    PhoBERT NER model cho tiếng Việt.
    Labels: B-FOOD, B-DISEASE, B-NUTRIENT, B-SYMPTOM, O

    Input: text đã qua underthesea (compound words nối _)
           ví dụ: "người bị tiểu_đường nên ăn ức_gà"
    Output: {"DISEASE": ["tiểu_đường"], "FOOD": ["ức_gà"]}
    """

    def __init__(self, model_dir: str):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # use_fast=False vì PhobertTokenizer là slow tokenizer (BPE)
        self.tokenizer = AutoTokenizer.from_pretrained(model_dir, use_fast=False)
        self.model = AutoModelForTokenClassification.from_pretrained(model_dir)
        self.model.to(self.device)
        self.model.eval()

        self.id2label: Dict[int, str] = self.model.config.id2label

    def predict(self, text: str) -> Dict[str, List[str]]:
        """
        Trả về dict entity theo loại, bỏ trùng.

        >>> model.predict("người bị tiểu_đường nên ăn ức_gà")
        {"DISEASE": ["tiểu_đường"], "FOOD": ["ức_gà"]}
        """
        words = text.split()
        if not words:
            return {}

        # Tokenize từng word riêng để biết chính xác số subtoken của mỗi word.
        # Không dùng word_ids() vì PhobertTokenizer là slow tokenizer.
        word_subtokens: List[List[str]] = []
        for w in words:
            subtoks = self.tokenizer.tokenize(w)
            word_subtokens.append(subtoks if subtoks else [self.tokenizer.unk_token])

        # Ghép lại, cắt nếu vượt max_length (258 - 2 special tokens)
        max_body = self.tokenizer.model_max_length - 2
        all_subtokens: List[str] = []
        word_cutoff = 0  # bao nhiêu word được giữ lại
        for wt in word_subtokens:
            if len(all_subtokens) + len(wt) > max_body:
                break
            all_subtokens.extend(wt)
            word_cutoff += 1

        # Build input_ids thủ công: [CLS] + subtokens + [SEP]
        token_ids = self.tokenizer.convert_tokens_to_ids(
            [self.tokenizer.cls_token] + all_subtokens + [self.tokenizer.sep_token]
        )
        input_ids = torch.tensor([token_ids], device=self.device)
        attention_mask = torch.ones_like(input_ids)

        with torch.no_grad():
            logits = self.model(input_ids=input_ids, attention_mask=attention_mask).logits

        # Bỏ [CLS] và [SEP]
        predictions = logits.argmax(dim=-1)[0].tolist()[1:-1]

        # Map subtoken predictions → word (lấy nhãn subtoken đầu tiên)
        entities: Dict[str, List[str]] = {}
        tok_idx = 0
        for word, subtoks in zip(words[:word_cutoff], word_subtokens[:word_cutoff]):
            if tok_idx >= len(predictions):
                break
            label = self.id2label[predictions[tok_idx]]
            tok_idx += len(subtoks)

            if label == "O":
                continue

            # Bỏ prefix B- / I-
            entity_type = label.split("-", 1)[-1]
            if word not in entities.get(entity_type, []):
                entities.setdefault(entity_type, []).append(word)

        return entities


def load_ner_model(config: dict, root_dir: str) -> Optional[NERModel]:
    """
    Load NERModel từ config.yaml.
    Tự tìm subfolder chứa config.json bên trong ner_model_path.
    Trả về None nếu chưa có model hoặc thiếu thư viện.
    """
    ner_base = os.path.join(root_dir, config.get("ner_model_path", "models/ner_phobert"))

    # Trường hợp 1: model nằm thẳng trong ner_base
    if os.path.isfile(os.path.join(ner_base, "config.json")):
        model_dir = ner_base
    else:
        # Trường hợp 2: tìm subfolder đầu tiên có config.json (vd: phobert-ner-final/)
        model_dir = None
        if os.path.isdir(ner_base):
            for entry in sorted(os.scandir(ner_base), key=lambda e: e.name):
                if entry.is_dir() and os.path.isfile(os.path.join(entry.path, "config.json")):
                    model_dir = entry.path
                    break

    if model_dir is None:
        print(f"[NER] not found: {ner_base}")
        return None

    try:
        model = NERModel(model_dir)
        print(f"[NER] loaded {model_dir} ({model.device})")
        return model
    except Exception as exc:
        print(f"[NER] load error: {exc}")
        return None


if __name__ == "__main__":
    import yaml

    ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    with open(os.path.join(ROOT, "configs", "config.yaml"), encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    ner = load_ner_model(cfg, ROOT)
    if ner is None:
        print("Không load được model.")
    else:
        tests = [
            "người bị tiểu_đường nên ăn ức_gà không",
            "bị gout và huyết_áp cao kiêng gì",
            "100g cá_hồi có bao nhiêu protein và omega_3",
            "mệt_mỏi đau_đầu có nên ăn rau_muống không",
        ]
        for t in tests:
            result = ner.predict(t)
            print(f"Input : {t}")
            print(f"Entities: {result}\n")
