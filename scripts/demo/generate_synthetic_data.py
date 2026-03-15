# -*- coding: utf-8 -*-

"""生成合成数据，用于检查 06-08 三个脚本能否跑通。"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    rng = np.random.default_rng(42)
    n = 60
    firms = [f"{i:06d}_{2019 + i % 5}" for i in range(1, n + 1)]
    boards = ["科创板", "创业板", "主板", "北交所"]
    industries = ["制造业", "软件和信息技术服务业", "医药制造业", "专用设备制造业"]

    screening = pd.DataFrame(
        {
            "firm_id": firms,
            "company": [f"示例公司{i:03d}" for i in range(1, n + 1)],
            "stock_code": [f"{i:06d}" for i in range(1, n + 1)],
            "board": [boards[i % len(boards)] for i in range(n)],
            "ipo_year": [2019 + i % 5 for i in range(n)],
            "industry": [industries[i % len(industries)] for i in range(n)],
            "ai_related_firm": 1,
            "core_density_per_10k": rng.normal(3.0, 1.0, n).clip(0.2, None),
            "relevant_paragraph_share": rng.uniform(0.01, 0.08, n),
            "reply_has_ai": rng.integers(0, 2, n),
        }
    )
    screening.to_csv(out_dir / "synthetic_firm_screening.csv", index=False, encoding="utf-8-sig")

    labels = pd.DataFrame(
        {
            "firm_id": firms,
            "scene_specificity": rng.integers(0, 4, n),
            "prudence": rng.integers(0, 4, n),
            "packaging_risk": rng.integers(0, 4, n),
            "evidence_support": rng.integers(0, 3, n),
        }
    )
    labels.to_csv(out_dir / "synthetic_labels.csv", index=False, encoding="utf-8-sig")

    latent_auth = (
        0.4 * (labels["scene_specificity"] - labels["scene_specificity"].mean())
        + 0.3 * (labels["prudence"] - labels["prudence"].mean())
        - 0.2 * (labels["packaging_risk"] - labels["packaging_risk"].mean())
        + rng.normal(0, 0.5, n)
    )

    fin = pd.DataFrame(
        {
            "firm_id": firms,
            "roa_t1": 0.03 + 0.01 * latent_auth + rng.normal(0, 0.01, n),
            "rev_growth_t1": 0.15 + 0.03 * latent_auth + rng.normal(0, 0.05, n),
            "asset_turnover_t1": 0.65 + 0.08 * latent_auth + rng.normal(0, 0.08, n),
            "ln_assets_preipo": rng.normal(22.0, 1.0, n),
            "leverage_preipo": rng.uniform(0.15, 0.75, n),
            "firm_age": rng.integers(3, 25, n),
            "rd_intensity_preipo": rng.uniform(0.01, 0.18, n),
            "soe": rng.integers(0, 2, n),
            "industry": [industries[i % len(industries)] for i in range(n)],
            "ipo_year": [2019 + i % 5 for i in range(n)],
        }
    )
    fin.to_csv(out_dir / "synthetic_financials.csv", index=False, encoding="utf-8-sig")
    print(f"[OK] wrote demo files into {out_dir}")


if __name__ == "__main__":
    main()
