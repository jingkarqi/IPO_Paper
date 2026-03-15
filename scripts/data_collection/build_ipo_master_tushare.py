from __future__ import annotations

import argparse
import os
from pathlib import Path

import pandas as pd
import tushare as ts


ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = ROOT_DIR / "data" / "reference" / "ipo_master" / "ipo_master_raw_tushare_2019_2024.xlsx"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="用 Tushare 按上市日期构建 IPO 样本底表。")
    parser.add_argument("--token", default=os.getenv("TUSHARE_TOKEN"))
    parser.add_argument("--start-date", default="20190101", help="上市日期窗口起点，格式 YYYYMMDD。")
    parser.add_argument("--end-date", default="20241231", help="上市日期窗口终点，格式 YYYYMMDD。")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--query-buffer-days",
        type=int,
        default=60,
        help="Tushare new_share 接口按网上申购日期筛选，向前回溯若干天以覆盖跨年上市样本。",
    )
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

    target_start = pd.Timestamp(args.start_date)
    target_end = pd.Timestamp(args.end_date)
    query_start = (target_start - pd.Timedelta(days=args.query_buffer_days)).strftime("%Y%m%d")
    query_end = target_end.strftime("%Y%m%d")

    pro = ts.pro_api(args.token)
    ipo = pro.new_share(start_date=query_start, end_date=query_end)
    ipo["stock_code"] = ipo["ts_code"].astype(str).str.split(".").str[0]
    ipo["exchange"] = ipo["ts_code"].astype(str).str.split(".").str[1]
    ipo["board"] = ipo["stock_code"].map(judge_board)
    ipo["subscription_date"] = pd.to_datetime(ipo["ipo_date"], format="%Y%m%d", errors="coerce")
    ipo["list_date"] = pd.to_datetime(ipo["issue_date"], format="%Y%m%d", errors="coerce")
    ipo = ipo[(ipo["list_date"] >= target_start) & (ipo["list_date"] <= target_end)].copy()
    ipo = ipo.drop_duplicates(subset=["ts_code"]).sort_values(["list_date", "ts_code"]).reset_index(drop=True)
    ipo["list_year"] = ipo["list_date"].dt.year
    ipo["subscription_date"] = ipo["subscription_date"].dt.strftime("%Y-%m-%d")
    ipo["list_date"] = ipo["list_date"].dt.strftime("%Y-%m-%d")

    cols = [
        "ts_code",
        "stock_code",
        "name",
        "exchange",
        "board",
        "list_date",
        "list_year",
        "subscription_date",
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
