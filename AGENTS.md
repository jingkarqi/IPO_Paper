# Repository Guidelines

## Project Structure & Module Organization
`src/pipeline/` contains the main Python CLI pipeline from manifest building through regression. `scripts/data_collection/` maintains the IPO master sheet and `scripts/llm/` exports annotation prompts. Keep source inputs under `data/`: `reference/` for baseline assets, `raw/` for study inputs, `interim/` for pipeline artifacts, and `processed/` for regression-ready tables. `materials/` stores lexicons, annotation manuals, and drafting notes. `paper/` is the LaTeX manuscript (`main.tex`, `sections/`, `build.ps1`). `outputs/` is for generated tables and figures.

## Build, Test, and Development Commands
Install dependencies with `pip install -r requirements.txt`. Read `docs/execution_workflow.md` before changing the pipeline.

- `python scripts/data_collection/build_ipo_master_ak.py` builds the IPO sample frame.
- `python scripts/data_collection/clean_ipo_master.py` standardizes dates, boards, and fields.
- `python scripts/data_collection/validate_ipo_by_cninfo.py --limit 30` spot-checks the sample against CNInfo.
- `python src/pipeline/run_regression.py --input data/processed/analysis_sample.csv --output-dir outputs/tables` runs the main regressions.
- `powershell -ExecutionPolicy Bypass -File .\paper\build.ps1` compiles the manuscript.

## Coding Style & Naming Conventions
Follow the existing Python style: 4-space indentation, `snake_case` for files, functions, and CLI flags, and `UPPER_SNAKE_CASE` for constants. Prefer small, single-purpose scripts with `argparse` entry points, type hints where they improve clarity, and UTF-8-safe CSV writes. Keep imports grouped as standard library, third-party, then local. LaTeX section files stay numerically ordered, for example `paper/sections/05_results.tex`.

## Testing Guidelines
There is no dedicated `tests/` package yet, so validate changes by running the smallest affected command on the real pipeline inputs when analytics code changes. Inspect regenerated artifacts in `data/interim/`, `data/processed/`, and `outputs/tables/`. Rebuild `paper/` after editing manuscript sections or table templates.

## Commit & Pull Request Guidelines
This workspace snapshot does not include `.git`, so no local commit history is available. Use short imperative commit subjects with a scope, such as `pipeline: tighten keyword screening thresholds`. In pull requests, list the commands you ran, the data directories you changed, and any regenerated outputs. Include table or PDF diffs when `paper/` or `outputs/` changes, and never hard-code secrets such as `TUSHARE_TOKEN`.
