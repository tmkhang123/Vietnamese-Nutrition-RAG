from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import time
from pathlib import Path
from urllib.parse import urlparse

import requests

try:
    from bs4 import BeautifulSoup

    BS4_AVAILABLE = True
except Exception:
    BS4_AVAILABLE = False


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "data" / "raw" / "vinmec_nutrition_articles"
DEFAULT_MANIFEST_PATH = PROJECT_ROOT / "data" / "raw" / "vinmec_nutrition_manifest.jsonl"
DEFAULT_OUTPUT_JSONL = PROJECT_ROOT / "data" / "raw" / "vinmec_nutrition_rag.jsonl"

BASE_SEARCH_URL = "https://www.vinmec.com/vie/ket-qua-tim-kiem/"
BASE_SEARCH_API_URL = "https://www.vinmec.com/api/v3/search"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)
DEFAULT_SEARCH_TERMS = [
    "dinh dưỡng",
    "chế độ ăn",
    "thực phẩm",
    "tiểu đường ăn uống",
    "huyết áp ăn uống",
    "giảm cân",
]

# Tu khoa de giu lai bai viet lien quan dinh duong.
NUTRITION_KEYWORDS = {
    "dinh duong",
    "dinh dưỡng",
    "an uong",
    "ăn uống",
    "thuc don",
    "thực đơn",
    "che do an",
    "chế độ ăn",
    "khau phan",
    "khẩu phần",
    "thap duong",
    "tiểu đường",
    "dai thao duong",
    "đái tháo đường",
    "giam can",
    "giảm cân",
    "beo phi",
    "béo phì",
    "vitamin",
    "khoang chat",
    "khoáng chất",
    "protein",
    "carb",
    "chat beo",
    "chất béo",
    "chat xo",
    "chất xơ",
    "duong huyet",
    "đường huyết",
    "huyet ap",
    "huyết áp",
    "an kieng",
    "ăn kiêng",
    "dai trang",
    "muoi",
    "natri",
    "calo",
    "nang luong",
    "năng lượng",
    "bo sung chat",
    "bổ sung chất",
}


def normalize_space(text: str) -> str:
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def clean_article_text(text: str) -> str:
    text = html.unescape(text)
    text = text.replace("&#9776;", " ")
    text = text.replace("☰", " ")
    text = normalize_space(text)

    cut_markers = [
        "Để đặt lịch khám tại viện",
        "Nếu có nhu cầu tư vấn và thăm khám",
        "Bài viết có hữu ích hay không?",
        "ĐỂ LẠI THÔNG TIN TƯ VẤN",
    ]
    lowered = text.lower()
    cut_positions = []
    for marker in cut_markers:
        pos = lowered.find(marker.lower())
        if pos != -1:
            cut_positions.append(pos)
    if cut_positions:
        text = text[: min(cut_positions)]

    text = re.sub(r"\bMục lục\b", " ", text, flags=re.IGNORECASE)
    return normalize_space(text)


def strip_accents(text: str) -> str:
    table = str.maketrans(
        "àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễ"
        "ìíịỉĩòóọỏõôồốộổỗơờớợởỡ"
        "ùúụủũưừứựửữỳýỵỷỹđ",
        "aaaaaaaaaaaaaaaaa"
        "eeeeeeeeeee"
        "iiiii"
        "ooooooooooooooooo"
        "uuuuuuuuuuu"
        "yyyyyd",
    )
    return text.lower().translate(table)


def safe_name(text: str) -> str:
    text = strip_accents(text)
    text = re.sub(r"[^a-z0-9_-]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text[:120] if text else "article"


def extract_links(html: str, base_url: str) -> set[str]:
    links: set[str] = set()
    if BS4_AVAILABLE:
        soup = BeautifulSoup(html, "html.parser")
        for a in soup.select("a[href]"):
            href = (a.get("href") or "").strip()
            if not href:
                continue
            links.add(urljoin(base_url, href))
        return links

    for href in re.findall(r'href=["\']([^"\']+)["\']', html, flags=re.IGNORECASE):
        href = href.strip()
        if not href:
            continue
        links.add(urljoin(base_url, href))
    return links


def is_search_page(url: str) -> bool:
    path = urlparse(url).path.lower().rstrip("/")
    return path.endswith("/ket-qua-tim-kiem")


def is_article_url(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.netloc and "vinmec.com" not in parsed.netloc:
        return False
    path = parsed.path.lower()
    return "/vie/bai-viet/" in path


def html_to_text(html: str) -> str:
    if BS4_AVAILABLE:
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.extract()

        # Uu tien phan than bai viet neu tim thay.
        selectors = [
            "#main-article",
            "article",
            "main",
            ".article-content",
            ".news-detail-content",
            ".post-content",
            ".content-detail",
        ]
        for selector in selectors:
            node = soup.select_one(selector)
            if node:
                for remove_selector in [".table-of-contents", "#toc-container"]:
                    for bad_node in node.select(remove_selector):
                        bad_node.decompose()
                return clean_article_text(node.get_text(separator=" "))

        return clean_article_text(soup.get_text(separator=" "))

    # Fallback extractor without bs4: try to keep only the main article block.
    article_html = html
    m = re.search(
        r'(?is)<div[^>]+id=["\']main-article["\'][^>]*>(.*?)<div[^>]+class=["\'][^"\']*meta-bottom',
        html,
    )
    if m:
        article_html = m.group(1)

    article_html = re.sub(r"(?is)<(script|style|noscript).*?>.*?</\1>", " ", article_html)
    article_html = re.sub(r"(?is)<[^>]+>", " ", article_html)
    return clean_article_text(article_html)


def extract_title(html: str, article_url: str) -> str:
    if BS4_AVAILABLE:
        soup = BeautifulSoup(html, "html.parser")
        h1 = soup.find("h1")
        if h1:
            title = normalize_space(h1.get_text(separator=" "))
            if title:
                return title
        if soup.title:
            title = normalize_space(soup.title.get_text(separator=" "))
            if title:
                return title

    m_h1 = re.search(r"(?is)<h1[^>]*>(.*?)</h1>", html)
    if m_h1:
        title = re.sub(r"(?is)<[^>]+>", " ", m_h1.group(1))
        title = normalize_space(title)
        if title:
            return title

    slug = urlparse(article_url).path.rstrip("/").split("/")[-1]
    return normalize_space(slug.replace("-", " "))


def is_nutrition_related(url: str, text: str) -> bool:
    bag = f"{url} {text}"
    bag_norm = strip_accents(bag)
    for keyword in NUTRITION_KEYWORDS:
        if strip_accents(keyword) in bag_norm:
            return True
    return False


def canonicalize_for_dedup(text: str) -> str:
    lowered = strip_accents(text.lower())
    lowered = re.sub(r"[^a-z0-9\s]", " ", lowered)
    lowered = normalize_space(lowered)
    return lowered


def build_shingles(text: str, shingle_size: int) -> set[str]:
    words = text.split()
    if len(words) < shingle_size:
        return set(words)
    return {" ".join(words[i : i + shingle_size]) for i in range(len(words) - shingle_size + 1)}


def jaccard_similarity(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0


def discover_article_links_from_search_api(
    session: requests.Session,
    terms: list[str],
    max_pages_per_term: int,
    page_size: int,
    delay_seconds: float,
    timeout: int,
) -> list[dict]:
    by_url: dict[str, dict] = {}
    for term in terms:
        clean_term = normalize_space(term)
        if not clean_term:
            continue
        for page in range(1, max_pages_per_term + 1):
            response = session.get(
                BASE_SEARCH_API_URL,
                params={
                    "term": clean_term,
                    "type": "post",
                    "page": page,
                    "limit": page_size,
                    "locale": "vi",
                },
                timeout=timeout,
            )
            response.raise_for_status()
            data = response.json()

            value = data.get("value") or {}
            if not isinstance(value, dict) or not value:
                break
            rows = list(value.values())[0]
            if not rows:
                break

            for row in rows:
                slug = normalize_space(str(row.get("post_slug") or ""))
                if not slug:
                    continue
                url = f"https://www.vinmec.com/vie/bai-viet/{slug}"
                if url in by_url:
                    continue
                by_url[url] = {
                    "url": url,
                    "search_term": clean_term,
                    "search_title": normalize_space(str(row.get("post_title") or "")),
                }

            if len(rows) < page_size:
                break
            if delay_seconds > 0:
                time.sleep(delay_seconds)

    return sorted(by_url.values(), key=lambda x: x["url"])


def crawl_vinmec_nutrition(
    output_dir: Path,
    manifest_path: Path,
    output_jsonl_path: Path,
    target_count: int,
    max_pages: int,
    search_terms: list[str],
    page_size: int,
    near_dup_threshold: float,
    shingle_size: int,
    delay_seconds: float,
    timeout: int,
    search_url: str,
) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    output_jsonl_path.parent.mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT, "Accept-Language": "vi,en;q=0.8"})

    article_candidates = discover_article_links_from_search_api(
        session=session,
        terms=search_terms,
        max_pages_per_term=max_pages,
        page_size=page_size,
        delay_seconds=delay_seconds,
        timeout=timeout,
    )

    saved = 0
    failed = 0
    scanned = 0
    dedup_exact = 0
    dedup_near = 0
    items: list[dict] = []
    rag_rows: list[dict] = []
    seen_exact: dict[str, str] = {}
    seen_shingles: list[tuple[str, set[str]]] = []

    for idx, candidate in enumerate(article_candidates, start=1):
        if saved >= target_count:
            break

        scanned += 1
        article_url = candidate["url"]
        result = {
            "index": idx,
            "url": article_url,
            "status": "failed",
            "reason": "",
            "output_file": "",
            "search_term": candidate.get("search_term", ""),
            "title": candidate.get("search_title", ""),
        }
        try:
            response = session.get(article_url, timeout=timeout)
            response.raise_for_status()
            html = response.text
            text = html_to_text(html)
            title = extract_title(html, article_url) or candidate.get("search_title", "")

            if len(text) < 500:
                result["reason"] = "content_too_short"
                failed += 1
            elif not is_nutrition_related(article_url, text[:2500]):
                result["status"] = "skipped"
                result["reason"] = "not_nutrition_related"
            else:
                canonical_text = canonicalize_for_dedup(text)
                exact_hash = hashlib.md5(canonical_text.encode("utf-8")).hexdigest()
                duplicate_of = seen_exact.get(exact_hash)
                if duplicate_of:
                    result["status"] = "skipped"
                    result["reason"] = "exact_duplicate"
                    result["duplicate_of"] = duplicate_of
                    dedup_exact += 1
                else:
                    shingles = build_shingles(canonical_text, shingle_size=shingle_size)
                    best_similarity = 0.0
                    near_duplicate_of = ""
                    for kept_url, kept_shingles in seen_shingles:
                        similarity = jaccard_similarity(shingles, kept_shingles)
                        if similarity > best_similarity:
                            best_similarity = similarity
                            near_duplicate_of = kept_url

                    if best_similarity >= near_dup_threshold:
                        result["status"] = "skipped"
                        result["reason"] = "near_duplicate"
                        result["duplicate_of"] = near_duplicate_of
                        result["similarity"] = round(best_similarity, 4)
                        dedup_near += 1
                    else:
                        slug = urlparse(article_url).path.rstrip("/").split("/")[-1]
                        stem = safe_name(f"{idx}_{slug}")
                        output_file = output_dir / f"{stem}.txt"
                        output_file.write_text(text, encoding="utf-8")
                        result["status"] = "ok"
                        result["output_file"] = str(output_file)
                        result["title"] = title
                        saved += 1
                        rag_rows.append({"url": article_url, "title": title, "text": text})
                        seen_exact[exact_hash] = article_url
                        seen_shingles.append((article_url, shingles))
        except Exception as exc:
            result["reason"] = str(exc)
            failed += 1

        items.append(result)
        if delay_seconds > 0:
            time.sleep(delay_seconds)

    with manifest_path.open("w", encoding="utf-8") as mf:
        for item in items:
            mf.write(json.dumps(item, ensure_ascii=False) + "\n")

    with output_jsonl_path.open("w", encoding="utf-8") as jf:
        for row in rag_rows:
            jf.write(json.dumps(row, ensure_ascii=False) + "\n")

    return {
        "search_url": search_url,
        "search_api_url": BASE_SEARCH_API_URL,
        "search_terms": search_terms,
        "target_count": target_count,
        "max_pages": max_pages,
        "page_size": page_size,
        "near_dup_threshold": near_dup_threshold,
        "shingle_size": shingle_size,
        "scanned_articles": scanned,
        "found_article_links": len(article_candidates),
        "saved": saved,
        "failed": failed,
        "dedup_exact": dedup_exact,
        "dedup_near": dedup_near,
        "output_dir": str(output_dir),
        "manifest_path": str(manifest_path),
        "output_jsonl_path": str(output_jsonl_path),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Crawl Vinmec nutrition articles and save plain text only."
    )
    parser.add_argument("--search-url", type=str, default=BASE_SEARCH_URL)
    parser.add_argument("--target-count", type=int, default=500)
    parser.add_argument("--max-pages", type=int, default=40)
    parser.add_argument(
        "--search-term",
        action="append",
        default=[],
        help="Search term for Vinmec API. Repeat this flag to add more terms.",
    )
    parser.add_argument("--page-size", type=int, default=20)
    parser.add_argument("--near-dup-threshold", type=float, default=0.88)
    parser.add_argument("--shingle-size", type=int, default=5)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST_PATH)
    parser.add_argument("--output-jsonl", type=Path, default=DEFAULT_OUTPUT_JSONL)
    parser.add_argument("--delay-seconds", type=float, default=0.5)
    parser.add_argument("--timeout", type=int, default=25)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    search_terms = args.search_term if args.search_term else DEFAULT_SEARCH_TERMS
    stats = crawl_vinmec_nutrition(
        output_dir=args.output_dir,
        manifest_path=args.manifest,
        output_jsonl_path=args.output_jsonl,
        target_count=args.target_count,
        max_pages=args.max_pages,
        search_terms=search_terms,
        page_size=args.page_size,
        near_dup_threshold=args.near_dup_threshold,
        shingle_size=args.shingle_size,
        delay_seconds=args.delay_seconds,
        timeout=args.timeout,
        search_url=args.search_url,
    )
    # Use ASCII-safe output to avoid Windows console encoding errors.
    print(json.dumps(stats, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
