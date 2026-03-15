from __future__ import annotations

import argparse
import html
import json
import math
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
import requests


ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_INPUT = ROOT_DIR / "data" / "reference" / "ipo_master" / "ipo_master_cleaned_2019_2024.xlsx"
DEFAULT_OUTPUT = ROOT_DIR / "data" / "reference" / "validation" / "prospectus_scan_2019_2024.csv"
DEFAULT_SUMMARY = ROOT_DIR / "data" / "reference" / "validation" / "prospectus_scan_2019_2024_summary.json"
EASTMONEY_URL = "https://datacenter-web.eastmoney.com/api/data/v1/get"
CNINFO_SEARCH_URL = "https://www.cninfo.com.cn/new/fulltextSearch/full"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36"
)
BOARD_TO_CNINFO_TYPE = {
    "上交所主板": "hzb",
    "深交所主板": "szb",
    "科创板": "kcb",
    "创业板": "cyb",
    "北交所": "bjs",
}
BOARD_TO_EASTMONEY_MARKET = {
    "上交所主板": "沪主板",
    "深交所主板": "深主板",
    "科创板": "科创板",
    "创业板": "创业板",
    "北交所": "北交所",
}
BAD_CNINFO_KEYWORDS = (
    "摘要",
    "英文",
    "提示性公告",
    "法律意见书",
    "审计报告",
    "募集说明书",
    "保荐书",
    "申报会计师",
    "问询",
    "回复",
)


@dataclass
class ProbeResult:
    downloadable: bool
    http_status: int | None
    content_length: int | None
    content_type: str | None
    failure_reason: str | None


_thread_local = threading.local()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="扫描 IPO 招股书可下载覆盖率并估算存储占用。")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--summary-output", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--max-workers", type=int, default=12)
    parser.add_argument("--timeout", type=int, default=20)
    parser.add_argument("--retries", type=int, default=3)
    parser.add_argument("--page-size", type=int, default=500)
    return parser.parse_args()


def make_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    return session


def get_session() -> requests.Session:
    session = getattr(_thread_local, "session", None)
    if session is None:
        session = make_session()
        _thread_local.session = session
    return session


def request_json(url: str, *, params: dict[str, Any], timeout: int, retries: int) -> dict[str, Any]:
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            response = get_session().get(url, params=params, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except Exception as exc:
            last_error = exc
            if attempt == retries:
                break
            time.sleep(min(2 ** (attempt - 1), 4))
    raise RuntimeError(f"request failed after {retries} attempts: {last_error}") from last_error


def request_stream(url: str, *, timeout: int, retries: int, headers: dict[str, str] | None = None) -> requests.Response:
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            response = get_session().get(url, timeout=timeout, stream=True, headers=headers, allow_redirects=True)
            return response
        except Exception as exc:
            last_error = exc
            if attempt == retries:
                break
            time.sleep(min(2 ** (attempt - 1), 4))
    raise RuntimeError(f"stream request failed after {retries} attempts: {last_error}") from last_error


def read_master(path: Path) -> pd.DataFrame:
    if path.suffix.lower() in {".xlsx", ".xls"}:
        df = pd.read_excel(path)
    else:
        df = pd.read_csv(path)
    df = df.copy()
    df["stock_code"] = df["stock_code"].astype(str).str.extract(r"(\d+)", expand=False).str.zfill(6)
    df["name"] = df["name"].astype("string")
    df["board"] = df["board"].astype("string")
    df["list_date"] = pd.to_datetime(df["list_date"], errors="coerce")
    return df


def fetch_eastmoney_source(page_size: int, timeout: int, retries: int) -> pd.DataFrame:
    params = {
        "sortColumns": "UPDATE_DATE,ORG_CODE",
        "sortTypes": "-1,-1",
        "pageSize": str(page_size),
        "pageNumber": "1",
        "reportName": "RPT_IPO_INFOALLNEW",
        "columns": (
            "SECURITY_CODE,DECLARE_ORG,PREDICT_LISTING_MARKET,INFO_CODE,UPDATE_DATE,ACCEPT_DATE,"
            "ORG_CODE,IS_REGISTRATION,STATE"
        ),
        "source": "WEB",
        "client": "WEB",
    }
    first_payload = request_json(EASTMONEY_URL, params=params, timeout=timeout, retries=retries)
    result = first_payload["result"]
    pages = int(result["pages"])
    rows = list(result["data"])
    for page in range(2, pages + 1):
        params["pageNumber"] = str(page)
        payload = request_json(EASTMONEY_URL, params=params, timeout=timeout, retries=retries)
        rows.extend(payload["result"]["data"])
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    df["SECURITY_CODE"] = df["SECURITY_CODE"].astype(str).str.zfill(6)
    df["eastmoney_prospectus_url"] = df["INFO_CODE"].map(lambda item: f"https://pdf.dfcfw.com/pdf/H2_{item}_1.pdf")
    df["eastmoney_market_match"] = df["PREDICT_LISTING_MARKET"].map(str)
    return df


def normalize_text(value: Any) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    text = html.unescape(re.sub(r"<[^>]+>", "", text))
    text = text.replace("\u3000", "").replace(" ", "")
    return text


def normalize_name(value: Any) -> str:
    text = normalize_text(value)
    for token in ("股份有限公司", "有限责任公司", "股份公司", "公司"):
        text = text.replace(token, "")
    return text


def map_board_to_cninfo(board: Any) -> str:
    return BOARD_TO_CNINFO_TYPE.get(str(board).strip(), "")


def candidate_url_from_adjunct(adjunct_url: str | None) -> str | None:
    if not adjunct_url:
        return None
    if adjunct_url.startswith("http://") or adjunct_url.startswith("https://"):
        return adjunct_url
    return f"https://static.cninfo.com.cn/{adjunct_url.lstrip('/')}"


def score_cninfo_candidate(candidate: dict[str, Any], row: pd.Series) -> float:
    title = normalize_text(candidate.get("announcementTitle"))
    score = 0.0
    if candidate.get("secCode") == row["stock_code"]:
        score += 120
    if "招股说明书" in title:
        score += 50
    if "首次公开发行" in title:
        score += 25
    if normalize_name(row["name"]) and normalize_name(row["name"]) in normalize_name(title):
        score += 20
    if str(row["stock_code"]) in title:
        score += 10
    if candidate_url_from_adjunct(candidate.get("adjunctUrl", "")):
        score += 10
    if str(candidate.get("adjunctType", "")).upper() == "PDF":
        score += 8
    for bad_keyword in BAD_CNINFO_KEYWORDS:
        if bad_keyword in title:
            score -= 35
    announcement_time = candidate.get("announcementTime")
    if announcement_time:
        try:
            ann_ts = pd.to_datetime(int(announcement_time), unit="ms", errors="coerce")
            if pd.notna(ann_ts) and pd.notna(row["list_date"]):
                delta_days = abs((row["list_date"] - ann_ts).days)
                score -= min(delta_days / 365.0, 10)
        except Exception:
            pass
    return score


def search_cninfo(row: pd.Series, timeout: int, retries: int) -> dict[str, Any] | None:
    queries = [
        ("code_board", f"{row['stock_code']} 招股说明书", map_board_to_cninfo(row["board"])),
        ("code_all", f"{row['stock_code']} 招股说明书", ""),
    ]
    name = normalize_text(row["name"])
    if name:
        queries.extend(
            [
                ("name_board", f"{name} 招股说明书", map_board_to_cninfo(row["board"])),
                ("name_all", f"{name} 招股说明书", ""),
            ]
        )

    best: tuple[float, dict[str, Any]] | None = None
    for strategy, search_key, market_type in queries:
        params = {
            "searchkey": search_key,
            "sdate": "",
            "edate": "",
            "isfulltext": "false",
            "sortName": "nothing",
            "sortType": "desc",
            "pageNum": 1,
            "pageSize": 20,
            "type": market_type,
        }
        try:
            payload = request_json(CNINFO_SEARCH_URL, params=params, timeout=timeout, retries=retries)
        except Exception:
            continue
        announcements = payload.get("announcements") or []
        for candidate in announcements:
            candidate_score = score_cninfo_candidate(candidate, row)
            if best is None or candidate_score > best[0]:
                enriched = dict(candidate)
                enriched["strategy"] = strategy
                enriched["market_type"] = market_type
                best = (candidate_score, enriched)
        if best and best[0] >= 100:
            break
    if best is None or best[0] < 70:
        return None
    return best[1]


def resolve_eastmoney_candidate(row: pd.Series, eastmoney_df: pd.DataFrame) -> dict[str, Any]:
    matches = eastmoney_df[eastmoney_df["SECURITY_CODE"] == row["stock_code"]]
    expected_market = BOARD_TO_EASTMONEY_MARKET.get(str(row["board"]).strip())
    if expected_market and not matches.empty:
        market_filtered = matches[matches["PREDICT_LISTING_MARKET"] == expected_market]
        if not market_filtered.empty:
            matches = market_filtered
    if not matches.empty:
        picked = matches.sort_values(["UPDATE_DATE", "ACCEPT_DATE"], ascending=[False, False]).iloc[0]
        return {
            "prospectus_source": "eastmoney_code",
            "prospectus_url": picked["eastmoney_prospectus_url"],
            "source_title": "东方财富 IPO 审核信息招股说明书链接",
            "source_reference": picked.get("INFO_CODE"),
            "source_market": picked.get("PREDICT_LISTING_MARKET"),
            "source_name": picked.get("DECLARE_ORG"),
        }

    return {
        "prospectus_source": pd.NA,
        "prospectus_url": pd.NA,
        "source_title": pd.NA,
        "source_reference": pd.NA,
        "source_market": pd.NA,
        "source_name": pd.NA,
    }


def resolve_cninfo_candidate(row: pd.Series, timeout: int, retries: int) -> dict[str, Any]:
    cninfo_candidate = search_cninfo(row, timeout=timeout, retries=retries)
    if cninfo_candidate:
        return {
            "prospectus_source": f"cninfo_{cninfo_candidate['strategy']}",
            "prospectus_url": candidate_url_from_adjunct(cninfo_candidate.get("adjunctUrl")),
            "source_title": normalize_text(cninfo_candidate.get("announcementTitle")),
            "source_reference": cninfo_candidate.get("adjunctUrl"),
            "source_market": cninfo_candidate.get("secName"),
            "source_name": cninfo_candidate.get("secCode"),
        }

    return {
        "prospectus_source": pd.NA,
        "prospectus_url": pd.NA,
            "source_title": pd.NA,
            "source_reference": pd.NA,
            "source_market": pd.NA,
            "source_name": pd.NA,
        }


def probe_pdf(url: str, timeout: int, retries: int) -> ProbeResult:
    if not url or str(url) == "<NA>":
        return ProbeResult(False, None, None, None, "missing_url")

    extra_headers: dict[str, str] = {}
    if "cninfo.com.cn" in url:
        extra_headers["Referer"] = "https://www.cninfo.com.cn/"

    response: requests.Response | None = None
    try:
        response = request_stream(url, timeout=timeout, retries=retries, headers=extra_headers)
        status = response.status_code
        content_type = response.headers.get("Content-Type")
        content_length_raw = response.headers.get("Content-Length")
        try:
            content_length = int(content_length_raw) if content_length_raw else None
        except ValueError:
            content_length = None
        if status != 200:
            return ProbeResult(False, status, content_length, content_type, f"http_{status}")
        first_chunk = next(response.iter_content(chunk_size=16), b"")
        is_pdf = first_chunk.lstrip().startswith(b"%PDF")
        if not is_pdf:
            return ProbeResult(False, status, content_length, content_type, "not_pdf")
        return ProbeResult(True, status, content_length, content_type, None)
    except Exception as exc:
        return ProbeResult(False, None, None, None, exc.__class__.__name__)
    finally:
        if response is not None:
            response.close()


def scan_row(row: pd.Series, eastmoney_df: pd.DataFrame, timeout: int, retries: int) -> dict[str, Any]:
    resolved = resolve_eastmoney_candidate(row, eastmoney_df=eastmoney_df)
    probe = ProbeResult(False, None, None, None, "missing_candidate")
    attempted_sources: list[str] = []
    if pd.notna(resolved["prospectus_url"]):
        attempted_sources.append(str(resolved["prospectus_source"]))
        probe = probe_pdf(str(resolved["prospectus_url"]), timeout=timeout, retries=retries)

    if not probe.downloadable:
        cninfo_resolved = resolve_cninfo_candidate(row, timeout=timeout, retries=retries)
        if pd.notna(cninfo_resolved["prospectus_url"]):
            attempted_sources.append(str(cninfo_resolved["prospectus_source"]))
            cninfo_probe = probe_pdf(str(cninfo_resolved["prospectus_url"]), timeout=timeout, retries=retries)
            if cninfo_probe.downloadable or pd.isna(resolved["prospectus_url"]):
                resolved = cninfo_resolved
                probe = cninfo_probe

    result = row.to_dict()
    result.update(resolved)
    result.update(
        {
            "attempted_sources": ",".join(attempted_sources) if attempted_sources else pd.NA,
            "downloadable": probe.downloadable,
            "http_status": probe.http_status,
            "content_length": probe.content_length,
            "content_type": probe.content_type,
            "failure_reason": probe.failure_reason,
            "size_mb": round((probe.content_length or 0) / 1024 / 1024, 3) if probe.content_length else pd.NA,
        }
    )
    return result


def build_summary(scan_df: pd.DataFrame) -> dict[str, Any]:
    matched = scan_df["prospectus_url"].notna().sum()
    downloadable = scan_df["downloadable"].fillna(False).sum()
    known_sizes = scan_df.loc[scan_df["downloadable"] & scan_df["content_length"].notna(), "content_length"]
    missing_sizes = scan_df.loc[scan_df["downloadable"] & scan_df["content_length"].isna()]
    estimated_total_bytes = int(known_sizes.sum())
    size_estimation_method = "exact_headers_only"
    if not missing_sizes.empty:
        avg_bytes = int(known_sizes.mean()) if not known_sizes.empty else 0
        estimated_total_bytes += avg_bytes * len(missing_sizes)
        size_estimation_method = "exact_headers_plus_mean_fill"
    summary = {
        "input_rows": int(len(scan_df)),
        "candidate_urls_found": int(matched),
        "downloadable_count": int(downloadable),
        "failed_count": int(len(scan_df) - downloadable),
        "coverage_ratio": round(float(downloadable) / float(len(scan_df)), 4) if len(scan_df) else 0.0,
        "source_breakdown": {str(k): int(v) for k, v in scan_df["prospectus_source"].fillna("missing").value_counts().items()},
        "failure_breakdown": {str(k): int(v) for k, v in scan_df["failure_reason"].fillna("ok").value_counts().items()},
        "downloadable_by_board": {
            str(k): int(v)
            for k, v in scan_df.loc[scan_df["downloadable"]].groupby("board").size().items()
        },
        "downloadable_by_year": {
            str(int(k)): int(v)
            for k, v in scan_df.loc[scan_df["downloadable"]].groupby(scan_df["list_date"].dt.year).size().items()
        },
        "known_size_count": int(known_sizes.notna().sum()),
        "size_estimation_method": size_estimation_method,
        "estimated_total_bytes": estimated_total_bytes,
        "estimated_total_gb": round(estimated_total_bytes / 1024 / 1024 / 1024, 3),
        "mean_file_mb": round(float(known_sizes.mean()) / 1024 / 1024, 3) if not known_sizes.empty else None,
        "median_file_mb": round(float(known_sizes.median()) / 1024 / 1024, 3) if not known_sizes.empty else None,
        "p90_file_mb": round(float(known_sizes.quantile(0.9)) / 1024 / 1024, 3) if not known_sizes.empty else None,
    }
    return summary


def main() -> None:
    args = parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.summary_output.parent.mkdir(parents=True, exist_ok=True)

    master_df = read_master(args.input)
    if args.limit is not None:
        master_df = master_df.head(args.limit).copy()
    eastmoney_df = fetch_eastmoney_source(page_size=args.page_size, timeout=args.timeout, retries=args.retries)

    results: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=args.max_workers) as executor:
        futures = {
            executor.submit(scan_row, row, eastmoney_df, args.timeout, args.retries): index
            for index, row in master_df.iterrows()
        }
        total = len(futures)
        for idx, future in enumerate(as_completed(futures), start=1):
            results.append(future.result())
            if idx % 100 == 0 or idx == total:
                print(f"[scan] {idx}/{total}")

    scan_df = pd.DataFrame(results)
    scan_df = scan_df.sort_values(["list_date", "stock_code"]).reset_index(drop=True)
    scan_df["list_date"] = scan_df["list_date"].dt.strftime("%Y-%m-%d")
    scan_df.to_csv(args.output, index=False, encoding="utf-8-sig")

    summary = build_summary(pd.DataFrame(results))
    args.summary_output.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[OK] wrote {args.output}")
    print(f"[OK] wrote {args.summary_output}")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
