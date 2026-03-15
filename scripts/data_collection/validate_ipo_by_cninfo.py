from __future__ import annotations

import argparse
import time
from pathlib import Path

import akshare as ak
import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_INPUT = ROOT_DIR / "data" / "reference" / "ipo_master" / "ipo_master_cleaned_2019_2024.xlsx"
DEFAULT_OUTPUT = ROOT_DIR / "data" / "reference" / "validation" / "ipo_master_cninfo_validation_sample.xlsx"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="抽样调用巨潮接口校验 IPO 底表。")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--limit", type=int, default=30)
    parser.add_argument("--sleep-seconds", type=float, default=0.3)
    return parser.parse_args()


def read_table(path: Path) -> pd.DataFrame:
    if path.suffix.lower() in {".xlsx", ".xls"}:
        return pd.read_excel(path, dtype={"stock_code": str, "ts_code": str})
    return pd.read_csv(path, dtype={"stock_code": str, "ts_code": str})


def main() -> None:
    args = parse_args()
    output_path = args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)

    df = read_table(args.input)
    if "stock_code" not in df.columns:
        raise SystemExit("输入文件缺少 `stock_code`。")

    df["stock_code"] = df["stock_code"].astype(str).str.replace(".0", "", regex=False).str.zfill(6)
    sample_df = df.head(args.limit).copy()

    results: list[dict] = []
    for idx, row in sample_df.iterrows():
        stock_code = row["stock_code"]
        name = row["name"] if "name" in sample_df.columns else ""
        print(f"[{idx + 1}/{len(sample_df)}] 正在查询 {stock_code} {name}")

        try:
            temp_df = ak.stock_ipo_summary_cninfo(symbol=stock_code)
            if temp_df is not None and not temp_df.empty:
                first = temp_df.iloc[0]
                result = {
                    "stock_code": stock_code,
                    "has_ipo_summary": 1,
                    "招股公告日期": first.get("招股公告日期"),
                    "中签率公告日": first.get("中签率公告日"),
                    "上网发行日期": first.get("上网发行日期"),
                    "上市日期_巨潮": first.get("上市日期"),
                    "发行价格": first.get("发行价格"),
                    "总发行数量_万股": first.get("总发行数量"),
                    "募集资金净额_万元": first.get("募集资金净额"),
                    "主承销商": first.get("主承销商"),
                    "error_msg": "",
                }
            else:
                result = {
                    "stock_code": stock_code,
                    "has_ipo_summary": 0,
                    "招股公告日期": None,
                    "中签率公告日": None,
                    "上网发行日期": None,
                    "上市日期_巨潮": None,
                    "发行价格": None,
                    "总发行数量_万股": None,
                    "募集资金净额_万元": None,
                    "主承销商": None,
                    "error_msg": "返回为空",
                }
        except Exception as exc:  # noqa: BLE001
            result = {
                "stock_code": stock_code,
                "has_ipo_summary": 0,
                "招股公告日期": None,
                "中签率公告日": None,
                "上网发行日期": None,
                "上市日期_巨潮": None,
                "发行价格": None,
                "总发行数量_万股": None,
                "募集资金净额_万元": None,
                "主承销商": None,
                "error_msg": str(exc),
            }

        results.append(result)
        time.sleep(args.sleep_seconds)

    result_df = pd.DataFrame(results)
    final_df = sample_df.merge(result_df, on="stock_code", how="left")
    for column in ["招股公告日期", "中签率公告日", "上网发行日期", "上市日期_巨潮"]:
        if column in final_df.columns:
            final_df[column] = pd.to_datetime(final_df[column], errors="coerce").dt.strftime("%Y-%m-%d")

    final_df.to_excel(output_path, index=False)
    print(f"[OK] wrote {output_path} with {len(final_df)} rows")


if __name__ == "__main__":
    main()
