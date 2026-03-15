from __future__ import annotations

import argparse
import os
from pathlib import Path

import pandas as pd
import tushare as ts


ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = ROOT_DIR / "data" / "reference" / "ipo_master" / "ipo_master_raw_tushare_2019_2023.xlsx"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="用 Tushare 构建 IPO 样本底表。")
    parser.add_argument("--token", default=os.getenv("TUSHARE_TOKEN"))
    parser.add_argument("--start-date", default="20190101")
    parser.add_argument("--end-date", default="20231231")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def judge_board(code: str) -> str:
    code = str(code)
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
    return "其他"


def main() -> None:
    args = parse_args()
    if not args.token:
        raise SystemExit("缺少 TUSHARE_TOKEN。请设置环境变量，或通过 --token 传入。")

    output_path = args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)

    pro = ts.pro_api(args.token)
    ipo = pro.new_share(start_date=args.start_date, end_date=args.end_date)
    ipo = ipo[(ipo["issue_date"] >= args.start_date) & (ipo["issue_date"] <= args.end_date)].copy()
    ipo["stock_code"] = ipo["ts_code"].astype(str).str.split(".").str[0]
    ipo["exchange"] = ipo["ts_code"].astype(str).str.split(".").str[1]
    ipo["board"] = ipo["stock_code"].map(judge_board)

    cols = [
        "ts_code",
        "stock_code",
        "name",
        "exchange",
        "board",
        "ipo_date",
        "issue_date",
        "amount",
        "market_amount",
        "price",
        "pe",
        "funds",
        "ballot",
    ]
    ipo[cols].to_excel(output_path, index=False)
    print(f"[OK] wrote {output_path} with {len(ipo)} rows")


if __name__ == "__main__":
    main()
