# -*- coding: utf-8 -*-

"""抽取与 AI / 数字化相关的段落。"""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import List

import pandas as pd


def split_paragraphs(text: str) -> List[str]:
    parts = re.split(r"\n\s*\n+", text)
    parts = [p.strip().replace("\n", " ") for p in parts if p.strip()]
    if len(parts) <= 1:
        parts = [p.strip() for p in re.split(r"(?<=。)", text) if p.strip()]
    return parts


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--text-index", required=True)
    parser.add_argument("--lexicon", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    text_index = pd.read_csv(args.text_index)
    lexicon = pd.read_csv(args.lexicon)
    keywords = lexicon["term"].dropna().astype(str).tolist()

    rows = []
    for _, row in text_index.iterrows():
        txt_path = Path(row["txt_path"])
        if not txt_path.exists():
            continue
        text = txt_path.read_text(encoding="utf-8", errors="ignore")
        paragraphs = split_paragraphs(text)
        for idx, para in enumerate(paragraphs):
            matched = [kw for kw in keywords if kw in para]
            if not matched:
                continue
            rows.append(
                {
                    "firm_id": row["firm_id"],
                    "company": row["company"],
                    "doc_type": row["doc_type"],
                    "paragraph_id": f"{row['firm_id']}_{row['doc_type']}_{idx:04d}",
                    "paragraph_text": para,
                    "matched_terms": "|".join(matched),
                    "n_matches": len(matched),
                    "txt_path": str(txt_path),
                }
            )

    out = pd.DataFrame(rows)
    out.to_csv(args.output, index=False, encoding="utf-8-sig")
    print(f"[OK] wrote {args.output} with {len(out)} paragraph rows")


if __name__ == "__main__":
    main()
