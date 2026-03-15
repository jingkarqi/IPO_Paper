# -*- coding: utf-8 -*-

"""把相关段落整理成可供 LLM / 人工标注的任务包。"""

from __future__ import annotations

import argparse

import pandas as pd


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--paragraphs", required=True)
    parser.add_argument("--screening", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--max-firms", type=int, default=120)
    parser.add_argument("--top-n-per-doc", type=int, default=5)
    args = parser.parse_args()

    paragraphs = pd.read_csv(args.paragraphs)
    screening = pd.read_csv(args.screening)
    screening = screening[screening["ai_related_firm"] == 1].copy()

    sort_cols = [c for c in ["core_density_per_10k", "relevant_paragraph_share"] if c in screening.columns]
    if sort_cols:
        screening = screening.sort_values(sort_cols, ascending=False)
    screening = screening.head(args.max_firms)

    keep_ids = set(screening["firm_id"].astype(str))
    paragraphs = paragraphs[paragraphs["firm_id"].astype(str).isin(keep_ids)].copy()
    paragraphs = paragraphs.sort_values(["firm_id", "doc_type", "n_matches"], ascending=[True, True, False])
    paragraphs["rank_in_doc"] = paragraphs.groupby(["firm_id", "doc_type"]).cumcount() + 1
    paragraphs = paragraphs[paragraphs["rank_in_doc"] <= args.top_n_per_doc]

    packets = (
        paragraphs.groupby(["firm_id", "company"])  # type: ignore[arg-type]
        .apply(
            lambda g: pd.Series(
                {
                    "n_selected_paragraphs": len(g),
                    "text_block": "\n\n".join(
                        [f"[{r.doc_type}] {r.paragraph_text}" for r in g.itertuples()]
                    ),
                }
            )
        )
        .reset_index()
    )

    out = screening.merge(packets, on=["firm_id", "company"], how="left")
    out.to_csv(args.output, index=False, encoding="utf-8-sig")
    print(f"[OK] wrote {args.output} with {len(out)} firm-level annotation packets")


if __name__ == "__main__":
    main()
