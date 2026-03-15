# -*- coding: utf-8 -*-

"""批量抽取 PDF 文本。

输入：标准化 manifest，其中包含 prospectus_pdf 和 / 或 reply_pdf 路径。
输出：
1. 每个文档对应 txt 文本；
2. document_index.csv 记录 firm_id、doc_type、pdf_path、txt_path、页数、字符数。
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import List

import fitz
import pandas as pd


DOC_SPECS = [
    ("prospectus_pdf", "prospectus"),
    ("reply_pdf", "reply"),
]


def extract_pdf_text(pdf_path: Path) -> tuple[str, int]:
    doc = fitz.open(pdf_path)
    texts = []
    for page in doc:
        texts.append(page.get_text("text"))
    text = "\n".join(texts)
    return text, len(doc)


def safe_name(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in str(value))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    manifest = pd.read_csv(args.manifest)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    records: List[dict] = []

    for _, row in manifest.iterrows():
        firm_id = str(row["firm_id"])
        company = str(row["company"])
        company_safe = safe_name(company)
        for col, doc_type in DOC_SPECS:
            if col not in row or pd.isna(row[col]):
                continue
            pdf_path = Path(str(row[col]))
            if not pdf_path.exists():
                print(f"[WARN] missing file: {pdf_path}")
                continue
            try:
                text, n_pages = extract_pdf_text(pdf_path)
            except Exception as exc:
                print(f"[WARN] failed to parse {pdf_path}: {exc}")
                continue

            txt_dir = out_dir / doc_type
            txt_dir.mkdir(parents=True, exist_ok=True)
            txt_path = txt_dir / f"{firm_id}_{company_safe}_{doc_type}.txt"
            txt_path.write_text(text, encoding="utf-8")
            records.append(
                {
                    "firm_id": firm_id,
                    "company": company,
                    "doc_type": doc_type,
                    "pdf_path": str(pdf_path),
                    "txt_path": str(txt_path),
                    "pages": n_pages,
                    "n_chars": len(text),
                }
            )

    index_df = pd.DataFrame(records)
    index_path = out_dir / "document_index.csv"
    index_df.to_csv(index_path, index=False, encoding="utf-8-sig")
    print(f"[OK] wrote {index_path} with {len(index_df)} documents")


if __name__ == "__main__":
    main()
