import re
import os
import unicodedata

UNICODE_REPLACEMENTS = {
    "\u2013": "-",   # en dash
    "\u2014": "-",   # em dash
    "\u2018": "'",   # left single quote
    "\u2019": "'",   # right single quote
    "\u201c": '"',   # left double quote
    "\u201d": '"',   # right double quote
    "\u2026": "...", # ellipsis
    "\u00a0": " ",   # non-breaking space
    "\u00ad": "",    # soft hyphen
    "\u200b": "",    # zero-width space
}

def normalize_unicode(text):
    for char, replacement in UNICODE_REPLACEMENTS.items():
        text = text.replace(char, replacement)
    # Chuyen cac ky tu co dau (e.g. accented letters) ve dang ASCII gan nhat
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    return text

def clean_text(text):
    text = normalize_unicode(text)

    # Xoa cac dai dau cham muc luc (Vi du: . . . . . . 15)
    text = re.sub(r'\.\s?\.\s?[\.\s]+', ' ', text)

    # Loai bo cac dong chi co so (so trang)
    text = re.sub(r'\n\s*\d+\s*\n', '\n', text)

    # Gop cac dong bi ngat quang (noi cau)
    text = re.sub(r'(?<![.!?])\n', ' ', text)

    # Don dep khoang trang thua
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

input_dir = os.path.join(PROJECT_ROOT, "data", "raw", "articles")
output_dir = os.path.join(PROJECT_ROOT, "data", "processed", "articles_cleaned")
os.makedirs(output_dir, exist_ok=True)

txt_files = [f for f in os.listdir(input_dir) if f.endswith(".txt")]

if not txt_files:
    print(f"Khong tim thay file .txt nao trong: {input_dir}")
else:
    for filename in txt_files:
        input_path = os.path.join(input_dir, filename)
        output_path = os.path.join(output_dir, filename)

        with open(input_path, "r", encoding="utf-8") as f:
            raw_content = f.read()

        cleaned_text = clean_text(raw_content)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(cleaned_text)

        print(f"  [OK] {filename}")

    print(f"\nXong! Da xu ly {len(txt_files)} file. Ket qua luu tai: {output_dir}")