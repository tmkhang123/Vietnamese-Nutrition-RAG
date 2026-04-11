from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class QueryType(str, Enum):
    NUTRITION_LOOKUP = "NUTRITION_LOOKUP"  # tra cứu số liệu cụ thể (protein, calo...)
    HEALTH_ADVICE    = "HEALTH_ADVICE"     # lời khuyên y tế (nên ăn gì khi bị bệnh X)
    BOTH             = "BOTH"              # cả hai


@dataclass
class ClassificationResult:
    query_type:       QueryType
    confidence:       float
    nutrition_score:  int
    health_score:     int


class QueryClassifier:
    """
    Phân loại câu hỏi theo rule-based keyword matching.

    NUTRITION_LOOKUP: "100g ức gà có bao nhiêu protein?"
    HEALTH_ADVICE   : "bị tiểu đường nên ăn gì?"
    BOTH            : "người gout ăn cá hồi được không?"
    """

    NUTRITION_KEYWORDS = [
        "bao nhiêu", "bao nhieu",
        "hàm lượng", "ham luong",
        "calo", "calorie", "kcal",
        "protein", "đạm",
        "chất béo", "chat beo", "lipid",
        "carb", "carbohydrate", "tinh bột", "tinh bot",
        "vitamin", "khoáng", "khoang chat",
        "chất xơ", "chat xo", "fiber",
        "natri", "kali", "canxi", "sắt", "kẽm",
        "thành phần", "thanh phan",
        "dinh dưỡng", "dinh duong",
        "100g", "100 gram",
        "khẩu phần", "khau phan",
        "chỉ số dinh dưỡng", "chi so",
        "gram", " mg ", " mcg ",
        "ăn gì", "an gi",          # nhóm 7: "tiểu đường nên ăn gì?" → n_score > 0 → BOTH
        "ăn được gì", "an duoc gi",
    ]

    HEALTH_KEYWORDS = [
        # Lời khuyên chung
        "nên ăn", "nen an",
        "không nên ăn", "khong nen an",
        "kiêng", "kieng",
        "tốt cho", "tot cho",
        "có hại", "co hai",
        "tránh", "tranh",
        "hạn chế", "han che",
        "lời khuyên", "loi khuyen",
        "chữa", "điều trị", "dieu tri",
        "phòng ngừa", "phong ngua",
        "sức khỏe", "suc khoe",

        # Nhóm 2 — Bệnh lý
        "bệnh", "benh",
        "bị tiểu đường", "bi tieu duong", "tiểu đường", "tieu duong",
        "đái tháo đường", "dai thao duong",
        "gout", "gút",
        "huyết áp", "huyet ap",
        "cholesterol", "mỡ máu", "mo mau",
        "béo phì", "beo phi", "thừa cân", "thua can",
        "tim mạch", "tim mach",
        "bệnh gan", "benh gan",
        "thận", "dạ dày", "da day",
        "táo bón", "tao bon", "tiêu chảy", "tieu chay",
        "ung thư", "ung thu", "xương khớp", "xuong khop",
        "thiếu máu", "thieu mau", "loãng xương", "loang xuong",
        "sỏi thận", "soi than", "viêm loét", "viem loet",

        # Nhóm 3 — Triệu chứng
        "triệu chứng", "trieu chung",
        "đau đầu", "dau dau",
        "mệt mỏi", "met moi",
        "chóng mặt", "chong mat",
        "buồn nôn", "buon non",
        "khó tiêu", "kho tieu",
        "đầy bụng", "day bung",
        "mất ngủ", "mat ngu",

        # Nhóm 4 — Mục tiêu cơ thể
        "giảm cân", "giam can",
        "tăng cân", "tang can",
        "giảm mỡ", "giam mo",
        "tăng cơ", "tang co",
        "gym", "thể thao", "the thao",
        "tập luyện", "tap luyen",
        "chạy bộ", "chay bo",
        "trước khi tập", "sau khi tập",
        "trước tập", "sau tập",
        "tăng sức bền", "tang suc ben",
        "phục hồi cơ", "phuc hoi co",

        # Nhóm 5 — Theo đối tượng
        "bà bầu", "ba bau",
        "mang thai", "mang thai",
        "thai kỳ", "thai ky",
        "cho con bú", "cho con bu",
        "trẻ em", "tre em",
        "trẻ nhỏ", "tre nho",
        "trẻ sơ sinh", "tre so sinh",
        "người cao tuổi", "nguoi cao tuoi",
        "người già", "nguoi gia",
        "người lớn tuổi",
        "người bệnh", "nguoi benh",

        # Nhóm 6 — Ăn chay / ăn kiêng
        "ăn chay", "an chay",
        "chay trường", "chay truong",
        "thuần chay", "thuan chay",
        "keto", "low carb",
        "dị ứng", "di ung",
        "không ăn được", "khong an duoc",
        "không dung nạp", "khong dung nap",
        "ăn kiêng", "an kieng",
        "nhịn ăn", "nhin an",
        "intermittent fasting",
    ]

    # Các keyword khi xuất hiện → câu hỏi là HEALTH_ADVICE dù có NUTRIENT keyword
    # Ví dụ: "ăn chay có đủ protein không" → HEALTH_ADVICE, không phải NUTRITION_LOOKUP
    # Lưu ý: preprocessor (underthesea) nối compound words bằng "_"
    # nên cần cả 2 dạng: "ăn chay" và "ăn_chay"
    HEALTH_OVERRIDE_KEYWORDS = [
        # Ăn chay / ăn kiêng (cả dạng gốc và dạng underthesea nối _)
        "ăn chay", "an chay", "ăn_chay",
        "chay trường", "chay_trường",
        "thuần chay", "thuần_chay",
        "keto", "low carb", "low_carb",
        "ăn kiêng", "an kieng", "ăn_kiêng",
        "dị ứng", "di ung", "dị_ứng",
        "không dung nạp", "không_dung_nạp",
        "nhịn ăn", "nhịn_ăn", "intermittent fasting",
        # Mục tiêu cơ thể
        "giảm cân", "giam can", "giảm_cân",
        "tăng cân", "tang can", "tăng_cân",
        "tăng cơ", "tang co", "tăng_cơ",
        "giảm mỡ", "giảm_mỡ",
        # Đối tượng
        "bà bầu", "ba bau", "bà_bầu",
        "mang thai", "mang_thai",
        "thai kỳ", "thai_kỳ",
        "trẻ em", "tre em", "trẻ_em",
        "người cao tuổi", "người_cao_tuổi",
        "người già", "người_già",
        # Gym / thể thao
        "gym", "tập luyện", "tập_luyện",
        "thể thao", "thể_thao",
    ]

    def classify(self, query: str) -> ClassificationResult:
        q = query.lower().replace("_", " ")  # normalize sau underthesea tokenize

        n_score = sum(1 for kw in self.NUTRITION_KEYWORDS if kw in q)
        h_score = sum(1 for kw in self.HEALTH_KEYWORDS if kw in q)

        # Override: nếu câu hỏi có health override keyword
        # thì ưu tiên HEALTH_ADVICE dù n_score > 0
        # Tránh "ăn chay có đủ protein không" → NUTRITION_LOOKUP
        has_health_override = any(kw in q for kw in self.HEALTH_OVERRIDE_KEYWORDS)

        if has_health_override and h_score > 0:
            # Câu hỏi về lối sống/chế độ ăn có đề cập nutrient → BOTH
            if n_score > 0:
                query_type = QueryType.BOTH
                confidence = 0.85
            else:
                query_type = QueryType.HEALTH_ADVICE
                confidence = min(0.6 + h_score * 0.1, 1.0)
        elif has_health_override:
            # Có override keyword nhưng h_score = 0 (chưa match) → vẫn HEALTH_ADVICE
            query_type = QueryType.HEALTH_ADVICE
            confidence = 0.7
        elif n_score > 0 and h_score > 0:
            query_type = QueryType.BOTH
            confidence = 0.85
        elif n_score > 0:
            query_type = QueryType.NUTRITION_LOOKUP
            confidence = min(0.6 + n_score * 0.1, 1.0)
        elif h_score > 0:
            query_type = QueryType.HEALTH_ADVICE
            confidence = min(0.6 + h_score * 0.1, 1.0)
        else:
            # Không rõ → dùng cả 2 nhánh cho an toàn
            query_type = QueryType.BOTH
            confidence = 0.4

        return ClassificationResult(
            query_type=query_type,
            confidence=confidence,
            nutrition_score=n_score,
            health_score=h_score,
        )


if __name__ == "__main__":
    clf = QueryClassifier()

    tests = [
        "100g ức gà có bao nhiêu protein?",
        "bị tiểu đường nên ăn gì?",
        "người gout ăn cá hồi được không?",
        "nước mía có nhiều calo không, người huyết áp cao uống được không?",
        "cho tôi biết về rau muống",
    ]

    for q in tests:
        r = clf.classify(q)
        print(f"Q: {q}")
        print(f"   → {r.query_type.value}  (n={r.nutrition_score}, h={r.health_score}, conf={r.confidence:.2f})")
        print()
