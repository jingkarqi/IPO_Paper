# -*- coding: utf-8 -*-

"""标准化 IPO 样本清单。

支持 CSV / XLSX 输入，并尽量自动识别常见字段名称。
输出统一字段：firm_id, company, stock_code, board, listing_date, ipo_year,
industry, established_year, prospectus_pdf, reply_pdf。
其中 listing_date / ipo_year 统一以上市日期生成。
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, List

import pandas as pd

ALIASES: Dict[str, List[str]] = {
    "company": ["company", "company_name", "name", "企业名称", "公司名称", "证券简称", "发行人名称", "company_full_name"],
    "stock_code": ["stock_code", "code", "股票代码", "证券代码", "公司代码"],
    "board": ["board", "板块", "上市板块"],
    "listing_date": ["listing_date", "list_date", "issue_date", "上市日期", "挂牌日期", "首发上市日期"],
    "industry": ["industry", "行业", "证监会行业", "申万行业"],
    "established_year": ["established_year", "成立年份", "设立年份"],
    "prospectus_pdf": ["prospectus_pdf", "招股书路径", "招股说明书PDF", "prospectus_path"],
    "reply_pdf": ["reply_pdf", "问询回复路径", "回复函PDF", "reply_path"],
}

REQUIRED = ["company", "stock_code", "listing_date"]


def read_table(path: Path) -> pd.DataFrame:
    if path.suffix.lower() in {".xlsx", ".xls"}:
        return pd.read_excel(path)
    return pd.read_csv(path)


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    original_cols = {str(c).strip(): c for c in df.columns}
    rename_map = {}
    lower_lookup = {str(c).strip().lower(): c for c in df.columns}

    for target, candidates in ALIASES.items():
        found = None
        for cand in candidates:
            if cand in original_cols:
                found = original_cols[cand]
                break
            if cand.lower() in lower_lookup:
                found = lower_lookup[cand.lower()]
                break
        if found is not None:
            rename_map[found] = target

    out = df.rename(columns=rename_map).copy()
    return out


def build_manifest(df: pd.DataFrame, year_start: int | None, year_end: int | None) -> pd.DataFrame:
    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        raise ValueError(f"缺少必要字段: {missing}")

    out = df.copy()
    out["stock_code"] = out["stock_code"].astype(str).str.extract(r"(\d+)", expand=False).fillna(out["stock_code"].astype(str))
    out["stock_code"] = out["stock_code"].str.zfill(6)
    out["listing_date"] = pd.to_datetime(out["listing_date"], errors="coerce")
    out["ipo_year"] = out["listing_date"].dt.year

    if "established_year" in out.columns:
        out["established_year"] = pd.to_numeric(out["established_year"], errors="coerce")
    else:
        out["established_year"] = pd.NA

    if year_start is not None:
        out = out[out["ipo_year"] >= year_start]
    if year_end is not None:
        out = out[out["ipo_year"] <= year_end]

    out = out.reset_index(drop=True)
    out["firm_id"] = out["stock_code"] + "_" + out["ipo_year"].astype("Int64").astype(str)

    for col in ["board", "industry", "prospectus_pdf", "reply_pdf"]:
        if col not in out.columns:
            out[col] = pd.NA

    keep_cols = [
        "firm_id",
        "company",
        "stock_code",
        "board",
        "listing_date",
        "ipo_year",
        "industry",
        "established_year",
        "prospectus_pdf",
        "reply_pdf",
    ]
    return out[keep_cols].sort_values(["ipo_year", "stock_code"]).reset_index(drop=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="原始 IPO 清单（csv/xlsx）")
    parser.add_argument("--output", required=True, help="标准化后输出路径")
    parser.add_argument("--year-start", type=int, default=None)
    parser.add_argument("--year-end", type=int, default=None)
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    df = read_table(input_path)
    df = normalize_columns(df)
    manifest = build_manifest(df, args.year_start, args.year_end)
    manifest.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"[OK] wrote {output_path} with {len(manifest)} rows")


if __name__ == "__main__":
    main()
