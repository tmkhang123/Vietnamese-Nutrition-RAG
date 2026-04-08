from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT_DIR = PROJECT_ROOT / "data" / "raw" / "vinmec_nutrition_articles"
DEFAULT_OUTPUT_JSONL = PROJECT_ROOT / "data" / "processed" / "vinmec_priority_corpus.jsonl"
DEFAULT_MANIFEST = PROJECT_ROOT / "data" / "processed" / "vinmec_priority_manifest.json"


TOPIC_KEYWORDS = {
    "diabetes": [
        "tiểu đường",
        "đái tháo đường",
        "đường huyết",
        "insulin",
        "hạ đường huyết",
    ],
    "hypertension": [
        "tăng huyết áp",
        "huyết áp",
        "natri",
        "muối",
        "tim mạch",
    ],
    "gout": [
        "gout",
        "gút",
        "axit uric",
        "purin",
    ],
    "weight_loss": [
        "giảm cân",
        "béo phì",
        "thừa cân",
        "calo",
        "năng lượng",
    ],
    "lipids": [
        "cholesterol",
        "triglycerid",
        "mỡ máu",
        "lipid",
    ],
}

RECOMMENDATION_PATTERNS = [
    r"\bnên\b",
    r"\bkhông nên\b",
    r"\bhạn chế\b",
    r"\btránh\b",
    r"\bưu tiên\b",
    r"\bkhuyến nghị\b",
    r"\bnên ăn\b",
    r"\bkiêng\b",
]

QUANT_PATTERNS = [
    r"\b\d+(\.\d+)?\s?(g|mg|kg|ml|l|kcal|calo|%)\b",
    r"\b\d+\s?(lần/ngày|lần/tuần|phút|giờ|tuần)\b",
]

RISK_PATTERNS = [
    r"\bnguy cơ\b",
    r"\bbiến chứng\b",
    r"\btác dụng phụ\b",
    r"\bchống chỉ định\b",
]

NOISE_PATTERNS = [
    r"theo dõi website",
    r"để nắm thêm thông tin",
    r"đặt lịch",
    r"liên hệ",
    r"copyright",
]


def normalize_space(text: str) -> str:
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def split_sentences(text: str) -> list[str]:
    pieces = re.split(r"(?<=[\.\!\?])\s+", text)
    return [normalize_space(piece) for piece in pieces if normalize_space(piece)]


def build_chunks(sentences: list[str], chunk_size: int, overlap: int) -> list[str]:
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for sentence in sentences:
        sentence_len = len(sentence)
        if not current:
            current = [sentence]
            current_len = sentence_len
            continue

        if current_len + 1 + sentence_len <= chunk_size:
            current.append(sentence)
            current_len += 1 + sentence_len
            continue

        chunks.append(" ".join(current))

        if overlap <= 0:
            current = [sentence]
            current_len = sentence_len
            continue

        carry: list[str] = []
        carry_len = 0
        for old in reversed(current):
            add_len = len(old) if not carry else len(old) + 1
            if carry_len + add_len > overlap:
                break
            carry.append(old)
            carry_len += add_len
        carry.reverse()
        current = carry + [sentence]
        current_len = len(" ".join(current))

    if current:
        chunks.append(" ".join(current))
    return chunks


def infer_topic(text: str, file_name: str) -> str:
    lowered = f"{file_name} {text}".lower()
    topic_scores: dict[str, int] = {}
    for topic, keywords in TOPIC_KEYWORDS.items():
        topic_scores[topic] = sum(1 for kw in keywords if kw in lowered)
    best_topic, best_score = max(topic_scores.items(), key=lambda x: x[1])
    return best_topic if best_score > 0 else "nutrition_general"


def score_chunk(chunk: str) -> tuple[float, list[str]]:
    lowered = chunk.lower()
    score = 0.0
    labels: list[str] = []

    rec_hits = sum(1 for p in RECOMMENDATION_PATTERNS if re.search(p, lowered))
    if rec_hits:
        score += min(3.0, rec_hits * 1.2)
        labels.append("recommendation")

    quant_hits = sum(1 for p in QUANT_PATTERNS if re.search(p, lowered))
    if quant_hits:
        score += min(2.5, quant_hits * 1.0)
        labels.append("quantitative")

    risk_hits = sum(1 for p in RISK_PATTERNS if re.search(p, lowered))
    if risk_hits:
        score += min(2.0, risk_hits * 1.0)
        labels.append("risk_warning")

    # Reward chunks that clearly mention condition/context.
    topic = infer_topic(chunk, "")
    if topic != "nutrition_general":
        score += 1.0
        labels.append(f"topic:{topic}")

    noise_hits = sum(1 for p in NOISE_PATTERNS if re.search(p, lowered))
    if noise_hits:
        score -= min(2.5, noise_hits * 1.2)
        labels.append("contains_noise")

    # Prefer chunks that are not too short.
    if len(chunk) >= 180:
        score += 0.5
    else:
        score -= 0.5

    return round(score, 2), labels


def build_priority_corpus(
    input_dir: Path,
    output_jsonl: Path,
    output_manifest: Path,
    chunk_size: int,
    overlap: int,
    min_chars: int,
    min_score: float,
) -> dict:
    if not input_dir.exists():
        raise FileNotFoundError(f"Input folder not found: {input_dir}")

    txt_files = sorted(input_dir.glob("*.txt"))
    if not txt_files:
        raise FileNotFoundError(f"No .txt files found in: {input_dir}")

    output_jsonl.parent.mkdir(parents=True, exist_ok=True)
    output_manifest.parent.mkdir(parents=True, exist_ok=True)

    total_raw_chunks = 0
    total_kept_chunks = 0
    topic_counter = Counter()
    label_counter = Counter()
    per_file_kept = Counter()

    with output_jsonl.open("w", encoding="utf-8") as out:
        for path in txt_files:
            raw = path.read_text(encoding="utf-8", errors="ignore")
            raw = normalize_space(raw)
            if not raw:
                continue

            sentences = split_sentences(raw)
            chunks = build_chunks(sentences, chunk_size=chunk_size, overlap=overlap)
            total_raw_chunks += len(chunks)

            for idx, chunk in enumerate(chunks, start=1):
                chunk = normalize_space(chunk)
                if len(chunk) < min_chars:
                    continue

                topic = infer_topic(chunk, path.stem)
                score, labels = score_chunk(chunk)
                if score < min_score:
                    continue

                total_kept_chunks += 1
                topic_counter[topic] += 1
                per_file_kept[path.stem] += 1
                for lb in labels:
                    label_counter[lb] += 1

                record = {
                    "id": f"{path.stem}_{idx}",
                    "source": path.stem,
                    "lang": "vi",
                    "topic": topic,
                    "importance_score": score,
                    "importance_labels": labels,
                    "text": chunk,
                }
                out.write(json.dumps(record, ensure_ascii=False) + "\n")

    manifest = {
        "input_dir": str(input_dir),
        "output_jsonl": str(output_jsonl),
        "total_files": len(txt_files),
        "total_raw_chunks": total_raw_chunks,
        "total_kept_chunks": total_kept_chunks,
        "keep_ratio": round(
            (total_kept_chunks / total_raw_chunks) if total_raw_chunks else 0.0, 4
        ),
        "topic_distribution": dict(topic_counter),
        "top_labels": dict(label_counter.most_common(10)),
        "top_files_by_kept_chunks": dict(per_file_kept.most_common(20)),
        "config": {
            "chunk_size": chunk_size,
            "overlap": overlap,
            "min_chars": min_chars,
            "min_score": min_score,
        },
    }
    output_manifest.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a priority-scored corpus from vinmec nutrition articles."
    )
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT_DIR)
    parser.add_argument("--output-jsonl", type=Path, default=DEFAULT_OUTPUT_JSONL)
    parser.add_argument("--output-manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--chunk-size", type=int, default=900)
    parser.add_argument("--overlap", type=int, default=120)
    parser.add_argument("--min-chars", type=int, default=120)
    parser.add_argument("--min-score", type=float, default=1.5)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    manifest = build_priority_corpus(
        input_dir=args.input_dir,
        output_jsonl=args.output_jsonl,
        output_manifest=args.output_manifest,
        chunk_size=args.chunk_size,
        overlap=args.overlap,
        min_chars=args.min_chars,
        min_score=args.min_score,
    )
    print(
        f"Done. kept={manifest['total_kept_chunks']}/{manifest['total_raw_chunks']} "
        f"chunks from {manifest['total_files']} files."
    )


if __name__ == "__main__":
    main()
