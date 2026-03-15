# -*- coding: utf-8 -*-

"""基于关键词对企业进行 AI / 数字化相关性筛选。"""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Dict

import pandas as pd


def count_terms(text: str, terms: list[str]) -> Dict[str, int]:
    counts = {}
    for term in terms:
        counts[term] = len(re.findall(re.escape(term), text, flags=re.IGNORECASE))
    return counts


def density(n_hits: float, n_chars: float) -> float:
    if not n_chars or n_chars <= 0:
        return 0.0
    return n_hits / n_chars * 10000


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--text-index", required=True)
    parser.add_argument("--lexicon", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    manifest = pd.read_csv(args.manifest)
    text_index = pd.read_csv(args.text_index)
    lexicon = pd.read_csv(args.lexicon)

    term_groups = {
        cat: lexicon.loc[lexicon["category"] == cat, "term"].dropna().astype(str).tolist()
        for cat in lexicon["category"].dropna().unique()
    }

    records = []
    for firm_id, group in text_index.groupby("firm_id"):
        summary = {"firm_id": firm_id}
        company = group["company"].iloc[0]
        summary["company"] = company
        for cat in term_groups:
            summary[f"{cat}_hits"] = 0
        total_chars = 0
        relevant_para_count = 0
        total_para_count = 0
        reply_has_ai = 0

        for _, row in group.iterrows():
            txt_path = Path(row["txt_path"])
            if not txt_path.exists():
                continue
            text = txt_path.read_text(encoding="utf-8", errors="ignore")
            total_chars += len(text)
            paragraphs = [p.strip() for p in re.split(r"\n\s*\n+", text) if p.strip()]
            total_para_count += len(paragraphs)

            doc_cat_hits = {}
            for cat, terms in term_groups.items():
                cat_hits = sum(count_terms(text, terms).values())
                doc_cat_hits[cat] = cat_hits
                summary[f"{cat}_hits"] += cat_hits

            keyword_terms = term_groups.get("core_concept", []) + term_groups.get("technical_term", []) + term_groups.get("scenario_term", [])
            for para in paragraphs:
                if any(term in para for term in keyword_terms):
                    relevant_para_count += 1

            if row["doc_type"] == "reply" and (doc_cat_hits.get("core_concept", 0) > 0 or doc_cat_hits.get("technical_term", 0) > 0):
                reply_has_ai = 1

        summary["n_chars_total"] = total_chars
        summary["relevant_paragraph_share"] = (relevant_para_count / total_para_count) if total_para_count else 0.0
        summary["reply_has_ai"] = reply_has_ai

        core_hits = summary.get("core_concept_hits", 0)
        tech_hits = summary.get("technical_term_hits", 0)
        scene_hits = summary.get("scenario_term_hits", 0)
        summary["core_density_per_10k"] = density(core_hits, total_chars)
        summary["tech_density_per_10k"] = density(tech_hits, total_chars)
        summary["scenario_density_per_10k"] = density(scene_hits, total_chars)

        summary["ai_related_firm"] = int((core_hits >= 1 and (tech_hits >= 1 or scene_hits >= 1)) or core_hits >= 2)
        summary["weak_related"] = int(core_hits >= 1 and summary["ai_related_firm"] == 0)
        records.append(summary)

    out = manifest[["firm_id", "company", "stock_code", "board", "ipo_year", "industry"]].merge(
        pd.DataFrame(records), on=["firm_id", "company"], how="left"
    )
    out = out.fillna(0)
    out.to_csv(args.output, index=False, encoding="utf-8-sig")
    print(f"[OK] wrote {args.output} with {len(out)} firms")


if __name__ == "__main__":
    main()
