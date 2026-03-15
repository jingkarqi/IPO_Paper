# IPO_Paper

这是一个围绕 IPO 企业 AI / 数字化披露真实性的实证研究仓库。当前仓库已经把样本底表维护、文本抽取、关键词筛选、标注任务准备、指数构建、回归分析和 LaTeX 论文写作整理到同一目录下，适合继续沿着一条主流水线推进。

当前状态可以概括为两点：

1. 骨架已经齐全：主流水线脚本、研究材料和论文章节都已放好。
2. 正式数据还没补齐：`data/raw/`、`data/interim/`、`data/processed/`、`outputs/tables/`、`outputs/figures/` 目前为空，说明正式样本尚未完整跑通。

## 一、根目录现在有什么

```text
IPO_Paper/
├── data/                  # 数据目录：参考资产、正式输入、中间产物、处理结果
├── docs/                  # 执行流程与资产清单
├── materials/             # 关键词表、标注手册、变量定义、论文草稿、计划
├── outputs/               # 回归结果与图表输出
├── paper/                 # LaTeX 论文工程
├── scripts/               # 数据抓取与 LLM prompt 导出
├── src/pipeline/          # 主分析流水线
├── AGENTS.md              # 仓库协作说明
└── requirements.txt       # Python 依赖
```

## 二、各目录的现有内容

### 1. `src/pipeline/`

这是正式主流水线，按顺序对应：

- `build_sample_manifest.py`：生成标准化样本清单
- `extract_pdf_text.py`：抽取招股书 / 问询回复文本
- `keyword_screening.py`：做企业级关键词筛选
- `extract_relevant_paragraphs.py`：抽取相关段落
- `prepare_annotation_tasks.py`：生成标注任务
- `score_authenticity.py`：构建真实性 / 包装性指标
- `merge_post_ipo_financials.py`：合并上市后财务数据
- `run_regression.py`：输出回归表

### 2. `scripts/`

- `scripts/data_collection/`：维护 IPO 样本底表，包含抓取、清洗、巨潮校验脚本
- `scripts/llm/export_annotation_prompts.py`：把待标注文本导出成 LLM 批处理 prompt

### 3. `data/`

- `reference/`：已整理好的 IPO 底表和校验样例
- `raw/`：正式研究输入，当前应补入 `post_ipo_financials.csv` 和 `firm_labels.csv`
- `interim/`：主流水线中间产物，当前为空
- `processed/`：最终分析样本，当前为空

### 4. `materials/`

- `core/`：当前主口径材料，如 `ai_keywords_weighted.csv`、`annotation_manual.md`、`llm_prompt_template.md`
- `reference/`：补充说明和备用材料
- `drafts/`：摘要、引言、开题提纲草稿
- `planning/`：研究计划与时间安排

### 5. `paper/`

论文工程已经可编译，核心文件包括：

- `main.tex`
- `sections/01_abstract.tex` 到 `sections/06_conclusion.tex`
- `references.bib`
- `build.ps1`

当前 `paper/main.pdf` 已存在，但 `05_results.tex` 仍主要是结果模板，后续要用正式回归结果回填。

## 三、建议从哪里开始

先读两份说明：

1. `docs/execution_workflow.md`：看完整执行顺序
2. `data/README.md`：看正式输入文件应放什么

然后按下面顺序推进。

## 四、如何继续推进工作

### 路线 A：先把正式数据链条补齐

1. 用 `scripts/data_collection/` 更新或校验 IPO 样本底表。
2. 在清洗后的底表里补齐 `prospectus_pdf` 和 `reply_pdf` 路径。
3. 把正式财务数据放入 `data/raw/post_ipo_financials.csv`。

### 路线 B：跑正式文本与标注流程

1. 生成 `data/interim/ipo_manifest.csv`
2. 抽取 PDF 文本到 `data/interim/text/`
3. 跑关键词筛选、相关段落抽取和标注任务生成
4. 导出 `annotation_prompts.jsonl`，完成 LLM + 人工复核
5. 把标签整理成 `data/raw/firm_labels.csv`

### 路线 C：形成正式结果并回填论文

1. 生成 `data/processed/firm_auth_index.csv`
2. 合并财务数据得到 `data/processed/analysis_sample.csv`
3. 输出 `outputs/tables/regression_results.*`
4. 把核心表格回填到 `paper/sections/05_results.tex`
5. 编译论文 PDF

## 五、常用命令

安装依赖：

```powershell
pip install -r requirements.txt
```

维护底表：

```powershell
python scripts/data_collection/build_ipo_master_ak.py
python scripts/data_collection/clean_ipo_master.py
python scripts/data_collection/validate_ipo_by_cninfo.py --limit 30
```

如果使用 Tushare：

```powershell
python scripts/data_collection/build_ipo_master_tushare.py
```

需要先配置环境变量 `TUSHARE_TOKEN`。

编译论文：

```powershell
powershell -ExecutionPolicy Bypass -File .\paper\build.ps1
```

## 六、最现实的下一步

如果目标是尽快把项目推进到“能出正式结果”的状态，优先级建议是：

1. 补齐正式 `raw` 数据和 PDF 路径
2. 跑通一次 `manifest -> text -> screening -> annotation_tasks`
3. 完成标签整理与真实性指数构建
4. 产出正式回归表并更新论文结果章节

也就是说，这个仓库现在最缺的不是脚本骨架，而是正式输入数据和一次完整的正式样本跑通。
