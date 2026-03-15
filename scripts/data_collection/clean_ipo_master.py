from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_INPUT = ROOT_DIR / "data" / "reference" / "ipo_master" / "ipo_master_raw_2019_2024.xlsx"
DEFAULT_OUTPUT = ROOT_DIR / "data" / "reference" / "ipo_master" / "ipo_master_cleaned_2019_2024.xlsx"

ALIASES = {
    "ts_code": ["ts_code", "TS_CODE"],
    "stock_code": ["stock_code", "code", "股票代码", "证券代码"],
    "name": ["name", "company", "company_name", "证券简称", "公司名称"],
    "exchange": ["exchange", "交易所"],
    "board": ["board", "板块", "上市板块"],
    "list_date": ["list_date", "listing_date", "issue_date", "上市日期", "首发上市日期"],
    "company_full_name": ["company_full_name", "公司全称", "发行人名称"],
}

VALID_BOARDS = {"上交所主板", "深交所主板", "科创板", "创业板", "北交所"}
EXCLUDE_NAMES = {"招商南油"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="清洗 IPO 样本底表，时间口径统一按上市日期。")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--start-date", default="2019-01-01")
    parser.add_argument("--end-date", default="2024-12-31")
    return parser.parse_args()


def read_table(path: Path) -> pd.DataFrame:
    if path.suffix.lower() in {".xlsx", ".xls"}:
        return pd.read_excel(path)
    return pd.read_csv(path)


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    original_cols = {str(col).strip(): col for col in df.columns}
    lower_lookup = {str(col).strip().lower(): col for col in df.columns}
    rename_map: dict[str, str] = {}

    for target, candidates in ALIASES.items():
        for candidate in candidates:
            if candidate in original_cols:
                rename_map[original_cols[candidate]] = target
                break
            if candidate.lower() in lower_lookup:
                rename_map[lower_lookup[candidate.lower()]] = target
                break

    return df.rename(columns=rename_map).copy()


def infer_exchange(ts_code: str) -> str | None:
    if pd.isna(ts_code):
        return None
    parts = str(ts_code).split(".")
    if len(parts) == 2:
        return parts[1]
    return None


def normalize_board(value: str, stock_code: str) -> str | None:
    value = str(value).strip()
    if value == "主板":
        return "深交所主板"
    if value in VALID_BOARDS:
        return value

    code = str(stock_code)
    if code.startswith("688"):
        return "科创板"
    if code.startswith("300"):
        return "创业板"
    if code.startswith(("600", "601", "603", "605")):
        return "上交所主板"
    if code.startswith(("000", "001", "002", "003")):
        return "深交所主板"
    if code.startswith("8") or code.startswith(("430", "831", "832", "833", "835", "836", "837", "838", "839")):
        return "北交所"
    return None


def main() -> None:
    args = parse_args()
    output_path = args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)

    df = normalize_columns(read_table(args.input))

    if "stock_code" not in df.columns and "ts_code" not in df.columns:
        raise SystemExit("输入文件至少需要 `stock_code` 或 `ts_code`。")

    if "stock_code" not in df.columns:
        df["stock_code"] = df["ts_code"].astype(str).str.split(".").str[0]
    df["stock_code"] = df["stock_code"].astype(str).str.extract(r"(\d+)", expand=False).str.zfill(6)

    if "exchange" not in df.columns:
        df["exchange"] = df["ts_code"].map(infer_exchange) if "ts_code" in df.columns else pd.NA
    if "ts_code" not in df.columns:
        df["ts_code"] = df.apply(
            lambda row: f"{row['stock_code']}.{row['exchange']}" if pd.notna(row["exchange"]) else pd.NA,
            axis=1,
        )

    if "name" not in df.columns:
        df["name"] = pd.NA

    df["board"] = df.apply(lambda row: normalize_board(row.get("board", ""), row["stock_code"]), axis=1)
    df["list_date"] = pd.to_datetime(df["list_date"], errors="coerce")
    df = df[df["board"].isin(VALID_BOARDS)].copy()
    df = df[df["list_date"].notna()].copy()
    df = df[~df["name"].isin(EXCLUDE_NAMES)].copy()

    start = pd.Timestamp(args.start_date)
    end = pd.Timestamp(args.end_date)
    df = df[(df["list_date"] >= start) & (df["list_date"] <= end)].copy()
    df = df.drop_duplicates(subset=["ts_code"]).sort_values(["list_date", "ts_code"]).reset_index(drop=True)
    df["list_year"] = df["list_date"].dt.year
    df["list_date"] = df["list_date"].dt.strftime("%Y-%m-%d")

    ordered = ["ts_code", "stock_code", "name", "company_full_name", "exchange", "board", "list_date", "list_year"]
    keep_cols = [col for col in ordered if col in df.columns]
    df[keep_cols].to_excel(output_path, index=False)
    print(f"[OK] wrote {output_path} with {len(df)} rows")


if __name__ == "__main__":
    main()
