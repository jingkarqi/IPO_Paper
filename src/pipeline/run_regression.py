# -*- coding: utf-8 -*-

"""运行基准回归。"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import List

import pandas as pd
import statsmodels.formula.api as smf


BASE_CONTROLS = [
    "ln_assets_preipo",
    "leverage_preipo",
    "firm_age",
    "rd_intensity_preipo",
    "soe",
    "C(industry)",
    "C(ipo_year)",
]

OUTCOMES = ["roa_t1", "rev_growth_t1", "asset_turnover_t1", "perf_index"]


def fit_model(df: pd.DataFrame, outcome: str, explain: str):
    formula = f"{outcome} ~ {explain} + " + " + ".join(BASE_CONTROLS)
    model = smf.ols(formula=formula, data=df).fit(cov_type="HC1")
    return model


def collect_coef(model, outcome: str, explain: str) -> dict:
    coef = model.params.get(explain, float("nan"))
    se = model.bse.get(explain, float("nan"))
    pval = model.pvalues.get(explain, float("nan"))
    return {
        "outcome": outcome,
        "explain": explain,
        "coef": coef,
        "se": se,
        "p_value": pval,
        "nobs": int(model.nobs),
        "r2": model.rsquared,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    df = pd.read_csv(args.input)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    text_blocks: List[str] = []
    tex_rows: List[str] = []

    for explain in ["auth_index", "pack_index"]:
        for outcome in OUTCOMES:
            model = fit_model(df, outcome, explain)
            rows.append(collect_coef(model, outcome, explain))
            text_blocks.append("=" * 80)
            text_blocks.append(f"Outcome: {outcome} | Explain: {explain}")
            text_blocks.append(model.summary().as_text())
            coef = model.params.get(explain, float("nan"))
            se = model.bse.get(explain, float("nan"))
            tex_rows.append(f"{outcome} & {explain} & {coef:.4f} & {se:.4f} & {model.rsquared:.4f} \\")

    results = pd.DataFrame(rows)
    results.to_csv(out_dir / "regression_results.csv", index=False, encoding="utf-8-sig")
    (out_dir / "regression_results.txt").write_text("\n".join(text_blocks), encoding="utf-8")

    tex = [
        r"\begin{tabular}{lllrr}",
        r"\toprule",
        r"Outcome & Explain & Coef & SE & R$^2$ \\",
        r"\midrule",
        *tex_rows,
        r"\bottomrule",
        r"\end{tabular}",
    ]
    (out_dir / "regression_results.tex").write_text("\n".join(tex), encoding="utf-8")
    print(f"[OK] wrote regression outputs to {out_dir}")


if __name__ == "__main__":
    main()
