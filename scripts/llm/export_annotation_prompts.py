from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_INPUT = ROOT_DIR / "data" / "interim" / "annotation_tasks.csv"
DEFAULT_TEMPLATE = ROOT_DIR / "materials" / "core" / "llm_prompt_template.md"
DEFAULT_OUTPUT = ROOT_DIR / "data" / "interim" / "annotation_prompts.jsonl"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="把标注任务导出成适合 LLM 批处理的 JSONL。")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--template", type=Path, default=DEFAULT_TEMPLATE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def require_columns(df: pd.DataFrame, columns: list[str], file_label: str) -> None:
    missing = [column for column in columns if column not in df.columns]
    if missing:
        raise ValueError(f"{file_label} 缺少字段: {missing}")


def build_task_rows(df: pd.DataFrame) -> pd.DataFrame:
    if "text_block" in df.columns:
        require_columns(df, ["firm_id", "text_block"], "annotation task file")
        if "company" not in df.columns:
            df["company"] = ""
        return df[["firm_id", "company", "text_block"]].copy()

    if "paragraph_text" in df.columns:
        require_columns(df, ["firm_id", "paragraph_text"], "annotation task file")
        company_col = "company" if "company" in df.columns else "firm_name" if "firm_name" in df.columns else None
        if company_col is None:
            df["company"] = ""
            company_col = "company"
        grouped = (
            df.groupby(["firm_id", company_col], as_index=False)
            .agg(text_block=("paragraph_text", lambda values: "\n\n".join(str(v) for v in values if pd.notna(v))))
            .rename(columns={company_col: "company"})
        )
        return grouped

    raise ValueError("输入文件需要包含 `text_block` 或 `paragraph_text`。")


def main() -> None:
    args = parse_args()
    template = args.template.read_text(encoding="utf-8")
    task_df = build_task_rows(pd.read_csv(args.input))

    if "{{TEXT_BLOCK}}" not in template:
        template = template.rstrip() + "\n\n{{TEXT_BLOCK}}\n"

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        for row in task_df.itertuples(index=False):
            prompt = (
                template.replace("{{TEXT_BLOCK}}", str(row.text_block))
                .replace("{{FIRM_ID}}", str(row.firm_id))
                .replace("{{COMPANY}}", str(row.company))
            )
            payload = {
                "custom_id": str(row.firm_id),
                "firm_id": str(row.firm_id),
                "company": str(row.company),
                "prompt": prompt,
            }
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")

    print(f"[OK] wrote {args.output} with {len(task_df)} prompts")


if __name__ == "__main__":
    main()
