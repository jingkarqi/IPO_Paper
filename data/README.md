# 数据目录说明

## 子目录

- `raw/`: 正式研究输入数据，例如财务数据、人工/LLM 标注结果。
- `interim/`: 中间产物，例如标准化样本清单、抽取后的文本、筛选结果、标注任务包。
- `processed/`: 可直接用于回归分析的企业级样本。
- `reference/`: 不直接进入回归、但很有用的参考资产，如 IPO 底表和校验样本。

## 建议放入 `raw/` 的文件

### 1. 财务数据

文件名建议：`raw/post_ipo_financials.csv`

最低字段：

- `firm_id`
- `roa_t1`
- `rev_growth_t1`
- `asset_turnover_t1`
- `ln_assets_preipo`
- `leverage_preipo`
- `firm_age`
- `rd_intensity_preipo`
- `soe`
- `industry`
- `ipo_year`

### 2. 企业标签

文件名建议：`raw/firm_labels.csv`

最低字段：

- `firm_id`
- `scene_specificity`
- `prudence`
- `packaging_risk`
- `evidence_support`

## `reference/` 中已有内容

### IPO 底表

- `reference/ipo_master/ipo_master_raw_2019_2023.xlsx`
- `reference/ipo_master/ipo_master_cleaned_2019_2023.xlsx`

### 校验样例

- `reference/validation/ipo_master_cninfo_validation_sample.xlsx`

## `interim/` 常见中间文件

- `ipo_manifest.csv`
- `text/document_index.csv`
- `firm_screening.csv`
- `relevant_paragraphs.csv`
- `annotation_tasks.csv`
- `annotation_prompts.jsonl`
