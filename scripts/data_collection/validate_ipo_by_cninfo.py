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
                    "股票代码_巨潮": first.get("股票代码"),
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
                    "股票代码_巨潮": None,
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
                "股票代码_巨潮": None,
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

    if "list_date" in final_df.columns:
        final_df["list_date"] = pd.to_datetime(final_df["list_date"], errors="coerce").dt.strftime("%Y-%m-%d")

    final_df["股票代码_巨潮"] = final_df["股票代码_巨潮"].astype(str).str.extract(r"(\d+)", expand=False).str.zfill(6)
    final_df["stock_code_match"] = final_df["stock_code"].astype(str).str.zfill(6).eq(final_df["股票代码_巨潮"])
    final_df["list_date_match"] = False
    has_list_date = final_df["list_date"].notna() if "list_date" in final_df.columns else False
    has_cninfo_date = final_df["上市日期_巨潮"].notna()
    if "list_date" in final_df.columns:
        final_df.loc[has_list_date & has_cninfo_date, "list_date_match"] = (
            final_df.loc[has_list_date & has_cninfo_date, "list_date"] == final_df.loc[has_list_date & has_cninfo_date, "上市日期_巨潮"]
        )

    def classify_issue(row: pd.Series) -> str:
        if int(row.get("has_ipo_summary", 0)) != 1:
            return "missing_cninfo_summary"
        if bool(row.get("list_date_match", False)):
            return "ok"
        if pd.isna(row.get("上市日期_巨潮")):
            return "missing_cninfo_list_date"
        return "list_date_mismatch"

    final_df["validation_issue_type"] = final_df.apply(classify_issue, axis=1)
    final_df["validation_scope_note"] = "巨潮 IPO 摘要接口可直接校验股票代码与上市日期，不返回公司简称和板块字段。"

    final_df.to_excel(output_path, index=False)
    print(f"[OK] wrote {output_path} with {len(final_df)} rows")


if __name__ == "__main__":
    main()
