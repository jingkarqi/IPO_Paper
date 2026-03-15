# -*- coding: utf-8 -*-

"""合并真实性指数与上市后经营表现数据。"""

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
    parser.add_argument("--auth", required=True)
    parser.add_argument("--financials", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    auth = pd.read_csv(args.auth)
    fin = pd.read_csv(args.financials)
    merged = auth.merge(fin, on="firm_id", how="inner", suffixes=("_auth", "_fin"))

    # 处理 merge 后可能出现的同名字段后缀
    for base in ["industry", "ipo_year"]:
        auth_col = f"{base}_auth"
        fin_col = f"{base}_fin"
        if base not in merged.columns:
            if auth_col in merged.columns and fin_col in merged.columns:
                merged[base] = merged[auth_col].combine_first(merged[fin_col])
            elif auth_col in merged.columns:
                merged[base] = merged[auth_col]
            elif fin_col in merged.columns:
                merged[base] = merged[fin_col]

    required = [
        "roa_t1",
        "rev_growth_t1",
        "asset_turnover_t1",
        "ln_assets_preipo",
        "leverage_preipo",
        "firm_age",
        "rd_intensity_preipo",
        "soe",
        "industry",
        "ipo_year",
    ]
    missing = [c for c in required if c not in merged.columns]
    if missing:
        raise ValueError(f"财务文件缺少字段: {missing}")

    merged["perf_index"] = (
        zscore(merged["roa_t1"]) + zscore(merged["rev_growth_t1"]) + zscore(merged["asset_turnover_t1"])
    ) / 3

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    merged.to_csv(args.output, index=False, encoding="utf-8-sig")
    print(f"[OK] wrote {args.output} with {len(merged)} rows")


if __name__ == "__main__":
    main()
