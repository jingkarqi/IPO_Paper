from __future__ import annotations

import argparse
import time
from pathlib import Path

import akshare as ak
import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = ROOT_DIR / "data" / "reference" / "ipo_master" / "ipo_master_raw_2019_2024.xlsx"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="用 AkShare 构建 IPO 样本底表。")
    parser.add_argument("--start-date", default="2019-01-01")
    parser.add_argument("--end-date", default="2024-12-31")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--retries", type=int, default=4, help="单个数据源抓取失败后的最大重试次数。")
    parser.add_argument("--retry-delay", type=float, default=2.0, help="首次重试前等待秒数；后续按次数线性增加。")
    return parser.parse_args()


def rename_if_present(df: pd.DataFrame, mapping: dict[str, str]) -> pd.DataFrame:
    keep_mapping = {src: dst for src, dst in mapping.items() if src in df.columns}
    return df.rename(columns=keep_mapping).copy()


def keep_core_columns(df: pd.DataFrame) -> pd.DataFrame:
    desired = ["stock_code", "name", "company_full_name", "list_date", "exchange", "board"]
    for column in desired:
        if column not in df.columns:
            df[column] = pd.NA
    return df[desired].copy()


def judge_sh_board(code: str) -> str | None:
    code = str(code)
    if code.startswith("688"):
        return "科创板"
    if code.startswith(("600", "601", "603", "605")):
        return "上交所主板"
    return None


def judge_sz_board(code: str) -> str | None:
    code = str(code)
    if code.startswith("300"):
        return "创业板"
    if code.startswith(("000", "001", "002", "003")):
        return "深交所主板"
    return None


def fetch_with_retry(label: str, func, retries: int, retry_delay: float) -> pd.DataFrame:
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            return func()
        except Exception as exc:  # noqa: BLE001 - AkShare 会抛出多类网络异常
            last_error = exc
            if attempt >= retries:
                break
            sleep_seconds = retry_delay * attempt
            print(
                f"[WARN] {label} 抓取失败，第 {attempt}/{retries} 次尝试出错：{exc}. "
                f"{sleep_seconds:.1f} 秒后重试..."
            )
            time.sleep(sleep_seconds)
    raise RuntimeError(f"{label} 抓取失败，已重试 {retries} 次") from last_error


def build_master(retries: int, retry_delay: float) -> pd.DataFrame:
    sh_main = rename_if_present(
        fetch_with_retry("上交所主板", lambda: ak.stock_info_sh_name_code(symbol="主板A股"), retries, retry_delay),
        {"证券代码": "stock_code", "证券简称": "name", "公司全称": "company_full_name", "上市日期": "list_date"},
    )
    sh_main["exchange"] = "SH"
    sh_main["board"] = "上交所主板"

    sh_kcb = rename_if_present(
        fetch_with_retry("科创板", lambda: ak.stock_info_sh_name_code(symbol="科创板"), retries, retry_delay),
        {"证券代码": "stock_code", "证券简称": "name", "公司全称": "company_full_name", "上市日期": "list_date"},
    )
    sh_kcb["exchange"] = "SH"
    sh_kcb["board"] = "科创板"

    sz = rename_if_present(
        fetch_with_retry("深交所A股列表", lambda: ak.stock_info_sz_name_code(symbol="A股列表"), retries, retry_delay),
        {"A股代码": "stock_code", "A股简称": "name", "A股上市日期": "list_date"},
    )
    sz["exchange"] = "SZ"
    if "板块" in sz.columns:
        sz["board"] = sz["板块"]

    bj = rename_if_present(
        fetch_with_retry("北交所", ak.stock_info_bj_name_code, retries, retry_delay),
        {"证券代码": "stock_code", "证券简称": "name", "上市日期": "list_date"},
    )
    bj["exchange"] = "BJ"
    bj["board"] = "北交所"

    sh_delist = rename_if_present(
        fetch_with_retry("上交所终止上市", lambda: ak.stock_info_sh_delist(symbol="全部"), retries, retry_delay),
        {"公司代码": "stock_code", "公司简称": "name", "上市日期": "list_date"},
    )
    sh_delist["exchange"] = "SH"
    sh_delist["board"] = sh_delist["stock_code"].map(judge_sh_board)

    sz_delist = rename_if_present(
        fetch_with_retry(
            "深交所终止上市",
            lambda: ak.stock_info_sz_delist(symbol="终止上市公司"),
            retries,
            retry_delay,
        ),
        {"证券代码": "stock_code", "证券简称": "name", "上市日期": "list_date"},
    )
    sz_delist["exchange"] = "SZ"
    sz_delist["board"] = sz_delist["stock_code"].map(judge_sz_board)

    frames = [keep_core_columns(df) for df in [sh_main, sh_kcb, sz, bj, sh_delist, sz_delist]]
    master = pd.concat(frames, ignore_index=True)
    master = master[master["board"].notna()].copy()
    master["stock_code"] = master["stock_code"].astype(str).str.extract(r"(\d+)", expand=False).str.zfill(6)
    master["list_date"] = pd.to_datetime(master["list_date"], errors="coerce")
    master = master[master["list_date"].notna()].copy()

    exchange_suffix = {"SH": ".SH", "SZ": ".SZ", "BJ": ".BJ"}
    master["ts_code"] = master.apply(
        lambda row: f"{row['stock_code']}{exchange_suffix.get(row['exchange'], '')}" if pd.notna(row["exchange"]) else pd.NA,
        axis=1,
    )
    return master


def main() -> None:
    args = parse_args()
    output_path = args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)

    start = pd.Timestamp(args.start_date)
    end = pd.Timestamp(args.end_date)

    master = build_master(retries=args.retries, retry_delay=args.retry_delay)
    master = master[(master["list_date"] >= start) & (master["list_date"] <= end)].copy()
    master = master.drop_duplicates(subset=["ts_code"]).sort_values(["list_date", "ts_code"]).reset_index(drop=True)
    master["list_year"] = master["list_date"].dt.year
    master["list_date"] = master["list_date"].dt.strftime("%Y-%m-%d")

    ordered = ["ts_code", "stock_code", "name", "company_full_name", "exchange", "board", "list_date", "list_year"]
    master[ordered].to_excel(output_path, index=False)
    print(f"[OK] wrote {output_path} with {len(master)} rows")


if __name__ == "__main__":
    main()
