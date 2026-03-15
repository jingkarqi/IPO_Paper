# 执行流程

## 一、先维护 IPO 样本底表

优先使用 `scripts/data_collection/`：

```powershell
python scripts/data_collection/build_ipo_master_ak.py
python scripts/data_collection/clean_ipo_master.py
python scripts/data_collection/validate_ipo_by_cninfo.py --limit 30
```

如果你更想走 Tushare，也可以：

```powershell
python scripts/data_collection/build_ipo_master_tushare.py
```

当前整理好的参考底表放在：

- `data/reference/ipo_master/ipo_master_raw_2019_2023.xlsx`
- `data/reference/ipo_master/ipo_master_cleaned_2019_2023.xlsx`

## 二、准备正式输入数据

需要准备的核心文件：

- `data/reference/ipo_master/ipo_master_cleaned_2019_2023.xlsx`
- `data/raw/post_ipo_financials.csv`
- 每家企业对应的 `prospectus_pdf` / `reply_pdf` 路径

如果清洗后的 IPO 底表里还没有 PDF 路径，请先补充这两列：

- `prospectus_pdf`
- `reply_pdf`

## 三、生成标准化样本清单并抽取 PDF 文本

```powershell
python src/pipeline/build_sample_manifest.py --input data/reference/ipo_master/ipo_master_cleaned_2019_2023.xlsx --output data/interim/ipo_manifest.csv --year-start 2019 --year-end 2023
python src/pipeline/extract_pdf_text.py --manifest data/interim/ipo_manifest.csv --output-dir data/interim/text
```

执行后会得到：

- `data/interim/ipo_manifest.csv`
- `data/interim/text/document_index.csv`
- `data/interim/text/prospectus/*.txt`
- `data/interim/text/reply/*.txt`

## 四、做关键词筛选与段落抽取

```powershell
python src/pipeline/keyword_screening.py --manifest data/interim/ipo_manifest.csv --text-index data/interim/text/document_index.csv --lexicon materials/core/ai_keywords_weighted.csv --output data/interim/firm_screening.csv
python src/pipeline/extract_relevant_paragraphs.py --text-index data/interim/text/document_index.csv --lexicon materials/core/ai_keywords_weighted.csv --output data/interim/relevant_paragraphs.csv
python src/pipeline/prepare_annotation_tasks.py --paragraphs data/interim/relevant_paragraphs.csv --screening data/interim/firm_screening.csv --output data/interim/annotation_tasks.csv --max-firms 120
```

## 五、导出 LLM 标注任务

```powershell
python scripts/llm/export_annotation_prompts.py --input data/interim/annotation_tasks.csv --template materials/core/llm_prompt_template.md --output data/interim/annotation_prompts.jsonl
```

标注完成后，请把结果整理成：

- `data/raw/firm_labels.csv`

最低需要字段：

- `firm_id`
- `scene_specificity`
- `prudence`
- `packaging_risk`
- `evidence_support`

## 六、构建指数并运行回归

```powershell
python src/pipeline/score_authenticity.py --screening data/interim/firm_screening.csv --labels data/raw/firm_labels.csv --output data/processed/firm_auth_index.csv
python src/pipeline/merge_post_ipo_financials.py --auth data/processed/firm_auth_index.csv --financials data/raw/post_ipo_financials.csv --output data/processed/analysis_sample.csv
python src/pipeline/run_regression.py --input data/processed/analysis_sample.csv --output-dir outputs/tables
```

主要输出包括：

- `data/processed/firm_auth_index.csv`
- `data/processed/analysis_sample.csv`
- `outputs/tables/regression_results.csv`
- `outputs/tables/regression_results.txt`
- `outputs/tables/regression_results.tex`

## 七、回填论文并编译

把核心结果填入：

- `paper/sections/05_results.tex`

然后编译：

```powershell
powershell -ExecutionPolicy Bypass -File .\paper\build.ps1
```
