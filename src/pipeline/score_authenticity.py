# -*- coding: utf-8 -*-

"""根据关键词筛选结果和人工/LLM 标签构建真实性指数。"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


def zscore(series: pd.Series) -> pd.Series:
    s = pd.to_numeric(series, errors="coerce")
    std = s.std(ddof=0)
    if std == 0 or pd.isna(std):
        return pd.Series(np.zeros(len(s)), index=s.index)
    return (s - s.mean()) / std


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--screening", required=True)
    parser.add_argument("--labels", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    screening = pd.read_csv(args.screening)
    labels = pd.read_csv(args.labels)

    required_label_cols = ["firm_id", "scene_specificity", "prudence"]
    missing = [c for c in required_label_cols if c not in labels.columns]
    if missing:
        raise ValueError(f"标签文件缺少字段: {missing}")

    if "packaging_risk" not in labels.columns:
        labels["packaging_risk"] = 0
    if "evidence_support" not in labels.columns:
        labels["evidence_support"] = 0

    merged = screening.merge(labels, on="firm_id", how="left", suffixes=("", "_label"))
    merged = merged[merged["ai_related_firm"] == 1].copy()

    merged["mention_z"] = (
        zscore(merged.get("core_density_per_10k", 0))
        + zscore(merged.get("relevant_paragraph_share", 0))
        + zscore(merged.get("reply_has_ai", 0))
    ) / 3
    merged["scene_z"] = zscore(merged["scene_specificity"])
    merged["prudence_z"] = zscore(merged["prudence"])
    merged["packaging_z"] = zscore(merged["packaging_risk"])
    merged["evidence_z"] = zscore(merged["evidence_support"])

    merged["auth_index"] = 0.3 * merged["mention_z"] + 0.4 * merged["scene_z"] + 0.3 * merged["prudence_z"]
    merged["pack_index"] = 0.4 * merged["mention_z"] - 0.3 * merged["scene_z"] - 0.2 * merged["prudence_z"] + 0.1 * merged["packaging_z"]

    keep = [
        "firm_id",
        "company",
        "stock_code",
        "board",
        "ipo_year",
        "industry",
        "mention_z",
        "scene_specificity",
        "prudence",
        "packaging_risk",
        "evidence_support",
        "auth_index",
        "pack_index",
    ]
    out = merged[keep].copy()
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.output, index=False, encoding="utf-8-sig")
    print(f"[OK] wrote {args.output} with {len(out)} firms")


if __name__ == "__main__":
    main()
