from __future__ import annotations

import json
import os
import time

import requests

# -------------------------------------------------------
# Danh sách bài Wikipedia tiếng Việt cần crawl
# Chủ đề: định nghĩa bệnh + triệu chứng + nguyên nhân
# (phần chế độ ăn → bổ sung thủ công từ Vinmec)
# -------------------------------------------------------
WIKIPEDIA_TOPICS = [
    "Đái tháo đường",
    "Đái tháo đường type 2",
    "Đái tháo đường thai kỳ",
    "Gút",
    "Tăng huyết áp",
    "Rối loạn lipid máu",
    "Béo phì",
    "Thiếu máu",
    "Loãng xương",
    "Sỏi thận",
    "Gan nhiễm mỡ",
    "Viêm gan",
    "Ung thư dạ dày",
    "Viêm loét dạ dày",
    "Táo bón",
    "Tiêu chảy",
    "Hội chứng ruột kích thích",
    "Suy dinh dưỡng",
    "Thiếu vitamin D",
    "Bệnh tim mạch",
]

WIKIPEDIA_API = "https://vi.wikipedia.org/w/api.php"


def fetch_wikipedia(title: str) -> str | None:
    """Lấy nội dung plain text của bài Wikipedia tiếng Việt."""
    params = {
        "action":      "query",
        "prop":        "extracts",
        "explaintext": 1,       # trả về plain text, bỏ HTML/wikimarkup
        "titles":      title,
        "format":      "json",
        "redirects":   1,
    }
    headers = {
        "User-Agent": "NutritionRAG-Bot/1.0 (academic project; contact: student@university.edu)"
    }
    try:
        resp = requests.get(WIKIPEDIA_API, params=params, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        pages = data["query"]["pages"]
        page  = next(iter(pages.values()))

        if "missing" in page:
            print(f"  [!] Không tìm thấy bài: {title}")
            return None

        return page.get("extract", "").strip()

    except Exception as exc:
        print(f"  [!] Lỗi khi crawl '{title}': {exc}")
        return None


def crawl_wikipedia(out_dir: str, topics: list[str] = WIKIPEDIA_TOPICS) -> int:
    """
    Crawl các bài Wikipedia và lưu vào out_dir dạng JSON.
    Format mỗi file: {"text": "...", "source": "Wikipedia — <title>"}
    """
    os.makedirs(out_dir, exist_ok=True)
    saved = 0

    for title in topics:
        print(f"Crawling: {title} ...", end=" ")
        text = fetch_wikipedia(title)

        if not text or len(text) < 200:
            print("bỏ qua (quá ngắn hoặc không có)")
            continue

        # Tên file: slug từ title
        slug     = title.lower().replace(" ", "_").replace("/", "-")
        filename = f"wiki_{slug}.json"
        filepath = os.path.join(out_dir, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump({"text": text, "source": f"Wikipedia — {title}"}, f, ensure_ascii=False, indent=2)

        print(f"OK ({len(text):,} ký tự)")
        saved += 1
        time.sleep(0.5)  # rate limit

    return saved


if __name__ == "__main__":
    ROOT    = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    OUT_DIR = os.path.join(ROOT, "data", "raw", "articles")

    print(f"=== Wikipedia Crawler ===")
    print(f"Lưu vào: {OUT_DIR}\n")

    n = crawl_wikipedia(OUT_DIR)
    print(f"\nHoàn tất: {n}/{len(WIKIPEDIA_TOPICS)} bài đã lưu.")
    print(f"\n--- Hướng dẫn tiếp theo ---")
    print(f"1. Copy tay 10-15 bài Vinmec vào {OUT_DIR}/")
    print(f"   Format JSON: {{\"text\": \"...\", \"source\": \"Vinmec\"}}")
    print(f"2. Chạy: python -m src.data_pipeline.embed_articles")
