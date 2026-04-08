from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT_DIR = PROJECT_ROOT / "data" / "processed" / "articles_cleaned"
DEFAULT_OUTPUT_JSONL = PROJECT_ROOT / "data" / "processed" / "rag_corpus.jsonl"
DEFAULT_OUTPUT_MANIFEST = PROJECT_ROOT / "data" / "processed" / "rag_corpus_manifest.json"


NOISE_PATTERNS = [
    r"table of contents",
    r"suggested citation",
    r"program discrimination complaint",
    r"equal opportunity provider",
    r"all rights reserved",
    r"http[s]?://\S+",
]


def detect_lang(text: str) -> str:
    vi_chars = "ăâđêôơưáàảãạấầẩẫậắằẳẵặéèẻẽẹếềểễệíìỉĩịóòỏõọốồổỗộớờởỡợúùủũụứừửữựýỳỷỹỵ"
    lowered = text.lower()
    return "vi" if any(ch in lowered for ch in vi_chars) else "en"


def normalize_space(text: str) -> str:
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def remove_noise(text: str) -> str:
    cleaned = text
    for pattern in NOISE_PATTERNS:
        cleaned = re.sub(pattern, " ", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\b\d{1,4}\b", lambda m: m.group(0), cleaned)
    return normalize_space(cleaned)


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

        next_len = current_len + 1 + sentence_len
        if next_len <= chunk_size:
            current.append(sentence)
            current_len = next_len
            continue

        chunks.append(" ".join(current))

        if overlap > 0:
            tail: list[str] = []
            tail_len = 0
            for old_sentence in reversed(current):
                extra = len(old_sentence) if not tail else len(old_sentence) + 1
                if tail_len + extra > overlap:
                    break
                tail.append(old_sentence)
                tail_len += extra
            tail.reverse()
            current = tail + [sentence]
            current_len = len(" ".join(current))
        else:
            current = [sentence]
            current_len = sentence_len

    if current:
        chunks.append(" ".join(current))

    return chunks


def build_corpus(
    input_dir: Path,
    output_jsonl: Path,
    output_manifest: Path,
    chunk_size: int,
    overlap: int,
    min_chunk_len: int,
) -> dict:
    txt_files = sorted(input_dir.glob("*.txt"))
    if not txt_files:
        raise FileNotFoundError(f"No .txt files in {input_dir}")

    output_jsonl.parent.mkdir(parents=True, exist_ok=True)
    output_manifest.parent.mkdir(parents=True, exist_ok=True)

    written = 0
    per_source = Counter()
    seen = set()

    with output_jsonl.open("w", encoding="utf-8") as out:
        for txt_path in txt_files:
            raw = txt_path.read_text(encoding="utf-8", errors="ignore")
            raw = normalize_space(raw)
            if not raw:
                continue

            denoised = remove_noise(raw)
            sentences = split_sentences(denoised)
            chunks = build_chunks(sentences, chunk_size=chunk_size, overlap=overlap)

            for idx, chunk in enumerate(chunks, start=1):
                chunk = normalize_space(chunk)
                if len(chunk) < min_chunk_len:
                    continue
                if chunk in seen:
                    continue
                seen.add(chunk)

                source = txt_path.stem
                lang = detect_lang(chunk)
                item = {
                    "id": f"{source}_{idx}",
                    "source": source,
                    "lang": lang,
                    "topic": "nutrition_general",
                    "text": chunk,
                }
                out.write(json.dumps(item, ensure_ascii=False) + "\n")
                written += 1
                per_source[source] += 1

    manifest = {
        "input_dir": str(input_dir),
        "output_jsonl": str(output_jsonl),
        "total_chunks": written,
        "sources": dict(per_source),
        "schema": {
            "id": "unique chunk id",
            "source": "document source",
            "lang": "language code",
            "topic": "topic tag",
            "text": "retrieval text content",
        },
        "chunking": {
            "chunk_size_chars": chunk_size,
            "overlap_chars": overlap,
            "min_chunk_len_chars": min_chunk_len,
        },
    }

    output_manifest.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build RAG handoff corpus from cleaned article txt files."
    )
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT_DIR)
    parser.add_argument("--output-jsonl", type=Path, default=DEFAULT_OUTPUT_JSONL)
    parser.add_argument("--output-manifest", type=Path, default=DEFAULT_OUTPUT_MANIFEST)
    parser.add_argument("--chunk-size", type=int, default=850)
    parser.add_argument("--overlap", type=int, default=120)
    parser.add_argument("--min-chunk-len", type=int, default=120)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    manifest = build_corpus(
        input_dir=args.input_dir,
        output_jsonl=args.output_jsonl,
        output_manifest=args.output_manifest,
        chunk_size=args.chunk_size,
        overlap=args.overlap,
        min_chunk_len=args.min_chunk_len,
    )
    print(
        f"Done. Wrote {manifest['total_chunks']} chunks to {manifest['output_jsonl']} "
        f"from {len(manifest['sources'])} source files."
    )


if __name__ == "__main__":
    main()
