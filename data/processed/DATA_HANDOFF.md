# Data Handoff for RAG Training

Tai lieu nay dung de ban giao data cho nguoi lam model/retrieval.

## 1) Input ban can chuan bi

- Thu muc nguon bai viet da clean: `data/processed/articles_cleaned/*.txt`
- File mapping mon an: `data/vi_food_mapping.csv`

## 2) Build corpus jsonl ban giao

Chay lenh:

```bash
python data/processed/build_handoff_corpus.py
```

Sau khi chay xong se co:

- `data/processed/rag_corpus.jsonl`: corpus dung de index/vectorize
- `data/processed/rag_corpus_manifest.json`: thong ke va schema de doi ban verify

## 2.1) Thu thap them bai viet tu seed URL (neu can)

Seed file da co san:

- `data/raw/seed_urls.csv`

Download cac nguon uu tien cao (P0, P1):

```bash
python data/processed/collect_seed_articles.py --max-priority 1
```

Ket qua:

- `data/raw/articles_seed/*.txt`: noi dung da trich xuat
- `data/raw/seed_download_manifest.jsonl`: log url thanh cong/that bai

## 2.2) Chon chunk quan trong (priority corpus) tu Vinmec

Khi co nhieu bai viet Vinmec, nen tao bo chunk co diem uu tien de doi model index/training dung truoc:

```bash
python data/processed/build_priority_corpus.py
```

File output:

- `data/processed/vinmec_priority_corpus.jsonl`
- `data/processed/vinmec_priority_manifest.json`

Schema mo rong (ngoai cac field co ban):

- `importance_score`: diem uu tien chunk
- `importance_labels`: ly do chunk duoc uu tien (recommendation, quantitative, risk_warning, topic:...)

## 3) Schema file `rag_corpus.jsonl`

Moi dong la 1 JSON object:

```json
{
  "id": "NutritionFactWHO_12",
  "source": "NutritionFactWHO",
  "lang": "vi",
  "topic": "nutrition_general",
  "text": "..."
}
```

Y nghia:

- `id`: dinh danh duy nhat cho chunk
- `source`: tai lieu goc
- `lang`: `vi` hoac `en`
- `topic`: nhan chu de (tam thoi dang de `nutrition_general`)
- `text`: noi dung retrieval

## 4) Checklist ban giao cho doi model

- [ ] Da build lai corpus moi nhat
- [ ] Da gui kem `rag_corpus_manifest.json`
- [ ] Da thong nhat schema field voi nguoi index vector DB
- [ ] Da thong bao ro nguon nao la `vi`, nguon nao la `en`
- [ ] Da gui file `vi_food_mapping.csv` de doi model xu ly entity mon an

## 5) Ghi chu chat luong du lieu

- Neu them bai viet tieng Viet moi, can chay lai script build corpus.
- Neu co noise (muc luc, disclaimer, legal), uu tien loc truoc khi handoff.
- Khong dua du lieu khong ro nguon vao corpus train/retrieval.
