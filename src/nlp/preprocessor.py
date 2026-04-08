from __future__ import annotations

import re
import unicodedata

try:
    import underthesea
    UNDERTHESEA_AVAILABLE = True
except ImportError:
    UNDERTHESEA_AVAILABLE = False


class VietnamesePreprocessor:
    """
    Tiền xử lý text tiếng Việt.
    - Nếu có underthesea: tách từ ghép (ức_gà, tiểu_đường)
    - Nếu không có: vẫn chạy được với normalize cơ bản
    """

    def normalize_unicode(self, text: str) -> str:
        """Chuẩn hóa Unicode NFC, lowercase, bỏ khoảng trắng thừa."""
        text = unicodedata.normalize("NFC", text)
        text = text.strip().lower()
        text = re.sub(r"\s+", " ", text)
        return text

    def word_segment(self, text: str) -> str:
        """
        Tách từ ghép tiếng Việt.
        'ức gà nước mắm' → 'ức_gà nước_mắm'
        Nếu chưa cài underthesea thì trả về nguyên bản.
        """
        if UNDERTHESEA_AVAILABLE:
            return underthesea.word_tokenize(text, format="text")
        return text

    def preprocess(self, text: str) -> str:
        """
        Pipeline đầy đủ: normalize → word segment.

        >>> p = VietnamesePreprocessor()
        >>> p.preprocess("Người bị Tiểu Đường ăn PHỞ được ko?")
        'người bị tiểu_đường ăn phở được ko?'  # nếu có underthesea
        """
        text = self.normalize_unicode(text)
        text = self.word_segment(text)
        return text


if __name__ == "__main__":
    p = VietnamesePreprocessor()

    tests = [
        "Người bị Tiểu Đường ăn PHỞ được không?",
        "100g ức gà chứa bao nhiêu PROTEIN?",
        "Bị gout nên kiêng gì?",
        "rau muống cung cấp bao nhiêu calo",
    ]

    print(f"underthesea: {'có' if UNDERTHESEA_AVAILABLE else 'chưa cài'}\n")
    for t in tests:
        print(f"  Input : {t}")
        print(f"  Output: {p.preprocess(t)}")
        print()
