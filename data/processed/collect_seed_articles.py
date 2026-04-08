from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from urllib.parse import urlparse

import requests

try:
    from bs4 import BeautifulSoup

    BS4_AVAILABLE = True
except Exception:
    BS4_AVAILABLE = False


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SEED_CSV = PROJECT_ROOT / "data" / "raw" / "seed_urls.csv"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "data" / "raw" / "articles_seed"
DEFAULT_MANIFEST = PROJECT_ROOT / "data" / "raw" / "seed_download_manifest.jsonl"


def normalize_space(text: str) -> str:
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def html_to_text(html: str) -> str:
    if BS4_AVAILABLE:
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.extract()
        return normalize_space(soup.get_text(separator=" "))

    # Fallback extractor without external parser
    html = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", html)
    html = re.sub(r"(?is)<[^>]+>", " ", html)
    return normalize_space(html)


def safe_name(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9_-]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text[:120] if text else "article"


def parse_priority(priority: str) -> int:
    # P0 is highest priority.
    m = re.match(r"^P(\d+)$", (priority or "").strip().upper())
    return int(m.group(1)) if m else 99


def collect(
    seed_csv: Path,
    output_dir: Path,
    manifest_path: Path,
    max_priority: int,
    timeout: int,
) -> tuple[int, int]:
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    downloaded = 0
    failed = 0

    with seed_csv.open("r", encoding="utf-8") as f, manifest_path.open(
        "w", encoding="utf-8"
    ) as mf:
        reader = csv.DictReader(f)
        for row_idx, row in enumerate(reader, start=1):
            priority = parse_priority(row.get("priority", ""))
            if priority > max_priority:
                continue

            url = (row.get("url") or "").strip()
            if not url:
                continue

            topic = (row.get("topic") or "unknown").strip()
            authority = (row.get("authority") or "unknown").strip()
            lang = (row.get("lang") or "unknown").strip()

            domain = urlparse(url).netloc.replace("www.", "")
            path_hint = urlparse(url).path.strip("/").replace("/", "_")
            file_stem = safe_name(f"{row_idx}_{topic}_{authority}_{domain}_{path_hint}")
            output_file = output_dir / f"{file_stem}.txt"

            result = {
                "url": url,
                "topic": topic,
                "authority": authority,
                "lang": lang,
                "priority": row.get("priority"),
                "output_file": str(output_file),
                "status": "failed",
                "reason": "",
            }

            try:
                response = requests.get(
                    url,
                    timeout=timeout,
                    headers={"User-Agent": "Mozilla/5.0 (data-collector)"},
                )
                response.raise_for_status()
                text = html_to_text(response.text)

                if len(text) < 300:
                    result["reason"] = "content_too_short_or_blocked"
                    failed += 1
                else:
                    output_file.write_text(text, encoding="utf-8")
                    result["status"] = "ok"
                    downloaded += 1
            except Exception as exc:
                result["reason"] = str(exc)
                failed += 1

            mf.write(json.dumps(result, ensure_ascii=False) + "\n")

    return downloaded, failed


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download and extract text from seed URLs for RAG data collection."
    )
    parser.add_argument("--seed-csv", type=Path, default=DEFAULT_SEED_CSV)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--max-priority", type=int, default=1)
    parser.add_argument("--timeout", type=int, default=25)
    args = parser.parse_args()

    if not args.seed_csv.exists():
        raise FileNotFoundError(f"Seed CSV not found: {args.seed_csv}")

    downloaded, failed = collect(
        seed_csv=args.seed_csv,
        output_dir=args.output_dir,
        manifest_path=args.manifest,
        max_priority=args.max_priority,
        timeout=args.timeout,
    )
    print(f"Done. downloaded={downloaded}, failed={failed}, seed_csv={args.seed_csv}")


if __name__ == "__main__":
    main()
