# IPO Paper TODO

这份 TODO 面向“把项目从当前骨架状态推进到可提交论文”的完整执行过程。目标不是只跑通脚本，而是把样本、文本、标签、回归结果、论文叙述和最终 PDF 全部收口。

## 1. 先锁定口径，避免后面返工

- [ ] 确认研究窗口是否以 `2019-2024` 为主样本。——已确认：`2019.1.1~2024.12.31`
- [ ] 确认样本范围是否覆盖全部 A 股 IPO，还是先用注册制板块作为技术性降维样本。——已确认：覆盖全部A股IPO。
- [ ] 明确“上市后第一年”口径。
  - 建议写清是“IPO 后第一个完整会计年度”还是“上市后自然年”。——已确认：第一个完整会计年度
- [ ] 明确行业分类口径。
  - 建议统一为证监会行业或申万一级行业，不要混用。
- [ ] 明确问询回复口径。
  - 基准方案建议每家企业保留一个最完整、最靠后的 `reply_pdf` 进入主流水线。
  - 如有多轮回复，另外保留一份轮次元数据台账。
- [ ] 统一论文和代码中的指标定义。
  - 必须在正式回归前统一，否则结果章节无法自洽。
- [ ] 统一回归规格。
  - 当前 `src/pipeline/run_regression.py` 是分别回归 `auth_index` 和 `pack_index`。
  - 当前论文设计部分写的是扩展模型同时纳入两者。
  - 要决定最终采用哪一种，并让脚本与论文一致。
- [ ] 决定是否要在正式结果前新增“描述性统计 + 相关系数表”导出步骤。
  - 当前仓库有回归脚本，但没有单独导出描述统计和相关系数表的脚本。

## 2. 准备环境和目录

- [ ] 安装依赖。

```powershell
pip install -r requirements.txt
```

- [ ] 确认本地可用 Python、PowerShell、LaTeX 编译环境。
- [ ] 确认以下目录存在并可写入：
  - `data/reference/`
  - `data/raw/`
  - `data/interim/`
  - `data/processed/`
  - `outputs/tables/`
  - `outputs/figures/`
- [ ] 建议额外准备 PDF 存放目录，方便路径统一。
  - `data/raw_pdfs/prospectus/`
  - `data/raw_pdfs/reply/`

## 3. 维护 IPO 样本底表

### 3.1 生成原始 IPO 名单

- [ ] 运行 IPO 底表抓取脚本。

```powershell
python scripts/data_collection/build_ipo_master_ak.py
```

- [ ] 如果 AkShare 数据不完整，使用 Tushare 补充。

```powershell
python scripts/data_collection/build_ipo_master_tushare.py
```

- [ ] 如使用 Tushare，提前配置环境变量 `TUSHARE_TOKEN`。

### 3.2 清洗底表

- [ ] 运行底表清洗脚本。

```powershell
python scripts/data_collection/clean_ipo_master.py
```

- [ ] 检查清洗后底表中的关键字段是否规范：
  - `stock_code`
  - `name` 或 `company`
  - `board`
  - `list_date`
  - `list_year`
- [ ] 检查股票代码是否统一为 6 位。
- [ ] 检查上市日期是否是标准日期格式。
- [ ] 检查板块命名是否统一，避免同一板块出现多个别名。

### 3.3 抽样校验

- [ ] 用 CNInfo 做抽样验证。

```powershell
python scripts/data_collection/validate_ipo_by_cninfo.py --limit 30
```

- [ ] 抽查至少以下信息是否一致：
  - 公司名称
  - 股票代码
  - 上市日期
  - 板块
- [ ] 记录校验误差类型。
  - 代码缺前导零
  - 日期格式不一致
  - 板块映射错误
  - 企业简称和全称不一致

### 3.4 在底表中补齐后续流水线必需字段

- [ ] 在清洗底表中补入以下字段。
  - `industry`
  - `established_year`
  - `prospectus_pdf`
  - `reply_pdf`
- [ ] 建议额外保留以下元数据字段，便于追溯与扩展：
  - `prospectus_version`
  - `prospectus_source_url`
  - `prospectus_download_date`
  - `reply_round`
  - `reply_type`
  - `reply_source_url`
  - `reply_download_date`
  - `notes`

### 3.5 底表阶段验收标准

- [ ] `data/reference/ipo_master/ipo_master_cleaned_2019_2023.xlsx` 已存在。
- [ ] 每家企业至少有公司名、股票代码、板块、上市日期、IPO 年份。
- [ ] 研究窗口内企业名单数量稳定，去重逻辑明确。
- [ ] 进入正式文本处理的企业都已经能匹配到 PDF 路径。

## 4. 收集招股说明书 PDF

### 4.1 数据来源

- [ ] 优先来源：
  - 巨潮资讯
  - 上交所官网
  - 深交所官网
  - 北交所官网
- [ ] 备选来源：
  - 东方财富
  - 公司官网投资者关系页面

### 4.2 每家企业至少要收集什么

- [ ] 至少保留 1 份最接近发行/注册时点、信息较完整的招股说明书 PDF。
- [ ] 建议同时记录以下信息：
  - `prospectus_pdf`
  - `prospectus_version`
  - `download_date`
  - `source_url`
  - `is_text_pdf`

### 4.3 文件命名建议

- [ ] 统一命名，避免后续路径混乱。
  - `股票代码_公司简称_prospectus.pdf`
- [ ] 如果存在多个版本，建议加版本后缀。
  - `股票代码_公司简称_prospectus_v1.pdf`
  - `股票代码_公司简称_prospectus_registered.pdf`

### 4.4 质量检查

- [ ] 优先保留可复制文本的 PDF，而不是纯图片版。
- [ ] 确认文件不是目录页残缺版、摘要版或扫描失败版。
- [ ] 确认同一企业没有误把旧版和终版混淆。
- [ ] 随机抽查 20 家企业，手动打开 PDF，确认文本抽取可用。

### 4.5 这一阶段的产物

- [ ] 更新后的 `ipo_master_cleaned_2019_2023.xlsx` 已填好 `prospectus_pdf`。
- [ ] 如有需要，另存一份 PDF 路径追踪表。

## 5. 收集问询函与回复函 PDF

### 5.1 数据来源

- [ ] 优先来源：
  - 上交所审核项目动态页面
  - 深交所发行上市审核信息公开页面
  - 北交所公开审核文件
  - 巨潮资讯

### 5.2 每家企业至少要收集什么

- [ ] 基准样本至少保留 1 份进入主流水线的 `reply_pdf`。
- [ ] 如果企业存在多轮回复，建议全部下载，但至少在主流水线里指定“最完整、最靠后的一轮”。
- [ ] 建议记录以下元数据：
  - `reply_pdf`
  - `reply_round`
  - `reply_type`
  - `download_date`
  - `source_url`
  - `is_text_pdf`

### 5.3 推荐保留的文件类型

- [ ] 审核问询函回复
- [ ] 回复意见
- [ ] 审核中心意见落实函回复
- [ ] 多轮回复文件

### 5.4 文件命名建议

- [ ] 使用统一命名。
  - `股票代码_公司简称_reply_round1.pdf`
  - `股票代码_公司简称_reply_round2.pdf`
- [ ] 如果最终只保留一份进入主流程，建议在底表中的 `reply_pdf` 指向最终使用文件。

### 5.5 质量检查

- [ ] 不要只保存问询函本身而漏掉回复文件。
- [ ] 不要只保存第一轮回复而忽略最后一轮完整回复。
- [ ] 检查文本是否是企业自身回复，而非交易所公告摘要。
- [ ] 随机抽查 20 家企业，确认 `reply_pdf` 指向的是可读、可抽取、内容完整的文件。

### 5.6 这一阶段的产物

- [ ] 更新后的底表已填好 `reply_pdf`。
- [ ] 如有多轮回复，额外维护一份轮次元数据表。

## 6. 收集上市前后财务数据

### 6.1 先定义财务口径

- [ ] 明确 `t0`、`t1` 的定义。
  - `t0` 建议是上市前一年。
  - `t1` 建议是上市后第一个完整会计年度。
- [ ] 在开始导数据前把公式写定，避免不同来源口径不一致。

### 6.2 结果变量需要什么数据

- [ ] 为计算 `roa_t1`，至少需要：
  - `net_profit_t1`
  - `avg_total_assets_t1` 或足以计算平均总资产的期初/期末总资产
- [ ] 为计算 `rev_growth_t1`，至少需要：
  - `revenue_t0`
  - `revenue_t1`
- [ ] 为计算 `asset_turnover_t1`，至少需要：
  - `revenue_t1`
  - `avg_total_assets_t1`

### 6.3 控制变量需要什么数据

- [ ] 为计算 `ln_assets_preipo`，需要：
  - `total_assets_preipo`
- [ ] 为计算 `leverage_preipo`，需要：
  - `total_liabilities_preipo`
  - `total_assets_preipo`
- [ ] 为计算 `firm_age`，需要：
  - `ipo_year`
  - `established_year`
- [ ] 为计算 `rd_intensity_preipo`，需要：
  - `rd_expense_preipo`
  - `revenue_preipo`
- [ ] 为生成 `soe`，需要：
  - 企业所有制性质信息
- [ ] 为固定效应和合并需要，保留：
  - `industry`
  - `ipo_year`

### 6.4 推荐收集的原始财务字段

- [ ] 建议先保留一份“原始财务台账”，不要只保留回归所需最终变量。
- [ ] 原始台账建议字段：
  - `firm_id`
  - `company`
  - `stock_code`
  - `ipo_year`
  - `established_year`
  - `industry`
  - `soe`
  - `total_assets_preipo`
  - `total_liabilities_preipo`
  - `revenue_preipo`
  - `rd_expense_preipo`
  - `revenue_t0`
  - `revenue_t1`
  - `net_profit_t1`
  - `total_assets_t1_begin`
  - `total_assets_t1_end`
  - `source_report_year`
  - `source_url`
  - `notes`

### 6.5 写入主流水线所需的最小输入文件

- [ ] 生成 `data/raw/post_ipo_financials.csv`。
- [ ] 最少字段必须包括：
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

### 6.6 财务数据来源建议

- [ ] 优先使用学校数据库或商业数据库：
  - Wind
  - CSMAR
  - 同花顺 iFinD
- [ ] 如果数据库不可用，备选：
  - 上市公司年报
  - 巨潮资讯
  - 东方财富

### 6.7 财务阶段验收标准

- [ ] 每条财务记录都能用 `firm_id` 与文本样本合并。
- [ ] 极端值和缺失值已做标记。
- [ ] 核心变量公式口径已写清。
- [ ] 至少抽查 20 家企业，确认手工计算值与导入值一致。

## 7. 生成标准化样本清单

- [ ] 用清洗后的 IPO 底表生成 manifest。

```powershell
python src/pipeline/build_sample_manifest.py --input data/reference/ipo_master/ipo_master_cleaned_2019_2023.xlsx --output data/interim/ipo_manifest.csv --year-start 2019 --year-end 2023
```

- [ ] 检查 `data/interim/ipo_manifest.csv` 是否包含以下字段：
  - `firm_id`
  - `company`
  - `stock_code`
  - `board`
  - `listing_date`
  - `ipo_year`
  - `industry`
  - `established_year`
  - `prospectus_pdf`
  - `reply_pdf`
- [ ] 抽查 `firm_id` 是否为 `股票代码_IPO年份`。
- [ ] 检查路径列是否存在空值、错路径、无权限路径。

## 8. 批量抽取 PDF 文本

- [ ] 运行 PDF 文本抽取。

```powershell
python src/pipeline/extract_pdf_text.py --manifest data/interim/ipo_manifest.csv --output-dir data/interim/text
```

- [ ] 检查生成的文件：
  - `data/interim/text/document_index.csv`
  - `data/interim/text/prospectus/*.txt`
  - `data/interim/text/reply/*.txt`
- [ ] 在 `document_index.csv` 中检查以下字段：
  - `firm_id`
  - `company`
  - `doc_type`
  - `pdf_path`
  - `txt_path`
  - `pages`
  - `n_chars`
- [ ] 关注以下异常：
  - `n_chars` 极低，说明可能抽取失败
  - 页数正常但文本很短，说明可能是图片 PDF
  - `reply` 文本缺失率过高，说明问询文件收集不完整
- [ ] 随机打开 20 份 `.txt`，确认段落未被严重截断或乱码。

## 9. 关键词筛选与相关段落抽取

### 9.1 企业级筛选

- [ ] 运行关键词筛选。

```powershell
python src/pipeline/keyword_screening.py --manifest data/interim/ipo_manifest.csv --text-index data/interim/text/document_index.csv --lexicon materials/core/ai_keywords_weighted.csv --output data/interim/firm_screening.csv
```

- [ ] 检查输出字段是否至少包括：
  - `firm_id`
  - `company`
  - `core_density_per_10k`
  - `relevant_paragraph_share`
  - `reply_has_ai`
  - `ai_related_firm`
  - `weak_related`

### 9.2 段落级抽取

- [ ] 运行相关段落抽取。

```powershell
python src/pipeline/extract_relevant_paragraphs.py --text-index data/interim/text/document_index.csv --lexicon materials/core/ai_keywords_weighted.csv --output data/interim/relevant_paragraphs.csv
```

- [ ] 检查段落输出字段：
  - `firm_id`
  - `company`
  - `doc_type`
  - `paragraph_id`
  - `paragraph_text`
  - `matched_terms`
  - `n_matches`
  - `txt_path`

### 9.3 这一阶段必须做的人工质检

- [ ] 抽查至少 30-50 家企业，确认 `ai_related_firm = 1` 的企业确实与企业自身 AI/数字化活动有关。
- [ ] 抽查至少 20 家 `weak_related = 1` 企业，判断是否有误伤或漏判。
- [ ] 识别以下典型假阳性：
  - 只在行业背景中提到 AI
  - 只在政策背景中提到数字化
  - 只在客户/供应商介绍中提到 AI
  - 只有口号，没有企业自身业务场景
- [ ] 如果误判较多，回头修订 `materials/core/ai_keywords_weighted.csv`，并保留版本记录。

## 10. 生成标注任务包

- [ ] 运行标注任务打包脚本。

```powershell
python src/pipeline/prepare_annotation_tasks.py --paragraphs data/interim/relevant_paragraphs.csv --screening data/interim/firm_screening.csv --output data/interim/annotation_tasks.csv --max-firms 120
```

- [ ] 确认输出字段至少包括：
  - `firm_id`
  - `company`
  - `n_selected_paragraphs`
  - `text_block`
- [ ] 根据时间精力确认 `--max-firms`。
  - 本科阶段建议先做 `80-150` 家企业的精细复核样本。
- [ ] 如果部分企业 `text_block` 为空，回查其段落抽取是否失败。

## 11. 导出 LLM 标注 Prompt 并完成人工复核

### 11.1 导出 Prompt

- [ ] 运行导出脚本。

```powershell
python scripts/llm/export_annotation_prompts.py --input data/interim/annotation_tasks.csv --template materials/core/llm_prompt_template.md --output data/interim/annotation_prompts.jsonl
```

- [ ] 检查 `data/interim/annotation_prompts.jsonl` 是否可直接送入外部大模型批处理。

### 11.2 LLM 初评

- [ ] 将每家企业的 `text_block` 发给模型，要求按 JSON 输出。
- [ ] 至少要求模型返回以下字段：
  - `firm_id`
  - `scene_specificity`
  - `prudence`
  - `packaging_risk`
  - `evidence_support`
  - `key_scenarios`
  - `packaging_signals`
  - `evidence_signals`
  - `final_judgement`
  - `confidence`
- [ ] 将原始 LLM 输出单独存档，建议文件名：
  - `data/raw/llm_annotation_raw.jsonl`

### 11.3 人工复核

- [ ] 按 `materials/core/annotation_manual.md` 的评分规则复核。
- [ ] 重点复核以下样本：
  - LLM `confidence = low`
  - 极端高分企业
  - 极端低分企业
  - 与研究者直觉明显不一致的企业
  - 招股书和回复函信号冲突的企业
- [ ] 对打分差异 `>= 2` 的样本必须回看原文。
- [ ] 如果招股书和回复函结论不一致，基准判断优先参考回复函，但保留备注。

### 11.4 形成最终标签文件

- [ ] 生成主流水线需要的最小文件 `data/raw/firm_labels.csv`。
- [ ] 必须至少包含：
  - `firm_id`
  - `scene_specificity`
  - `prudence`
  - `packaging_risk`
  - `evidence_support`
- [ ] 建议另存一份更完整的复核文件，字段可包括：
  - `reviewer`
  - `review_date`
  - `confidence_level`
  - `final_notes`
  - `scene_specificity_mean`
  - `prudence_mean`
  - `packaging_risk_mean`
  - `evidence_support_mean`

## 12. 构建真实性指数和包装性指数

- [ ] 运行指数构建脚本。

```powershell
python src/pipeline/score_authenticity.py --screening data/interim/firm_screening.csv --labels data/raw/firm_labels.csv --output data/processed/firm_auth_index.csv
```

- [ ] 检查输出字段是否至少包括：
  - `firm_id`
  - `company`
  - `stock_code`
  - `board`
  - `ipo_year`
  - `industry`
  - `mention_z`
  - `scene_specificity`
  - `prudence`
  - `packaging_risk`
  - `evidence_support`
  - `auth_index`
  - `pack_index`
- [ ] 核查以下问题：
  - 是否只保留了 `ai_related_firm = 1` 的企业
  - 是否有企业因为标签缺失被意外丢掉
  - 指数是否出现异常集中或极端值

## 13. 合并财务数据，生成正式分析样本

- [ ] 运行合并脚本。

```powershell
python src/pipeline/merge_post_ipo_financials.py --auth data/processed/firm_auth_index.csv --financials data/raw/post_ipo_financials.csv --output data/processed/analysis_sample.csv
```

- [ ] 检查 `analysis_sample.csv` 是否至少包含：
  - `auth_index`
  - `pack_index`
  - `roa_t1`
  - `rev_growth_t1`
  - `asset_turnover_t1`
  - `perf_index`
  - `ln_assets_preipo`
  - `leverage_preipo`
  - `firm_age`
  - `rd_intensity_preipo`
  - `soe`
  - `industry`
  - `ipo_year`
- [ ] 记录合并前后样本量：
  - 文本样本量
  - 有标签样本量
  - 有财务数据样本量
  - 最终回归样本量
- [ ] 检查缺失值和异常值处理是否一致。

## 14. 生成描述性统计、相关系数和回归结果

### 14.1 回归结果

- [ ] 运行基准回归。

```powershell
python src/pipeline/run_regression.py --input data/processed/analysis_sample.csv --output-dir outputs/tables
```

- [ ] 检查输出文件：
  - `outputs/tables/regression_results.csv`
  - `outputs/tables/regression_results.txt`
  - `outputs/tables/regression_results.tex`

### 14.2 描述性统计和相关系数

- [ ] 生成描述性统计表。
- [ ] 生成相关系数表。
- [ ] 如果仓库中尚无对应脚本，补一份脚本或 notebook，不要手工抄数字后丢失可复现性。
- [ ] 将结果输出到 `outputs/tables/`，建议文件名：
  - `descriptive_stats.csv`
  - `descriptive_stats.tex`
  - `correlation_matrix.csv`
  - `correlation_matrix.tex`

### 14.3 结果阶段验收标准

- [ ] 回归结果中的样本量与 `analysis_sample.csv` 一致。
- [ ] 变量名、系数方向和论文叙述口径一致。
- [ ] 所有表格都能追溯到具体输入文件和脚本。

## 15. 进行稳健性和补充检验

- [ ] 视时间允许，至少完成 2-4 项补充检验：
  - 替换被解释变量为 `perf_index`
  - 拆分真实性维度分别回归
  - 单独检验 `pack_index`
  - 剔除极端值样本
  - 剔除高波动行业样本
  - 扩展到上市后第二年
- [ ] 为每项稳健性检验保留：
  - 脚本或命令
  - 样本筛选说明
  - 输出表格
  - 结论一句话摘要

## 16. 回填论文正文

### 16.1 先修正文稿与代码不一致问题

- [ ] 修改 `paper/sections/04_design.tex`，使指标公式与最终脚本一致。
- [ ] 修改 `paper/sections/appendix.tex`，使附录变量定义与最终脚本一致。
- [ ] 修改论文中的回归模型表述，使之与最终跑出的规格一致。

### 16.2 替换结果章节模板

- [ ] 更新 `paper/sections/05_results.tex`。
- [ ] 将以下占位内容替换为正式结果：
  - 描述性统计表
  - 基准回归表
  - 稳健性检验表
  - 结果解释文字
- [ ] 不要只替换数字，要同步改写叙述中的“若结果符合预期”“待填”等模板语言。

### 16.3 更新全文中的“拟”“预期”表述

- [ ] 更新摘要 `paper/sections/01_abstract.tex`，把计划式表述改为完成式表述。
- [ ] 更新引言 `paper/sections/02_introduction.tex`，使研究设计和实际执行一致。
- [ ] 更新结论 `paper/sections/06_conclusion.tex`，把“预期结论”改成“本文发现”。
- [ ] 如样本范围、指标口径、回归规格有调整，同步更新引言、设计、附录。

### 16.4 参考文献与表格引用

- [ ] 检查 `paper/references.bib` 中键名与正文引用是否一致。
- [ ] 重新编译后确认不再出现未定义引用。
- [ ] 检查表格标题、注释、变量名中英文写法是否统一。

## 17. 编译论文并处理渲染问题

- [ ] 运行编译脚本。

```powershell
powershell -ExecutionPolicy Bypass -File .\paper\build.ps1
```

- [ ] 确认生成：
  - `paper/main.pdf`
- [ ] 检查编译日志中的问题：
  - undefined citations
  - missing references
  - Overfull/Underfull box
  - 表格溢出
  - 中文字体缺失
- [ ] 逐页检查 PDF：
  - 摘要与英文 Abstract 排版是否正常
  - 目录和页码是否正常
  - 表格是否跨页或截断
  - 数学公式是否显示正常
  - 附录是否完整

## 18. 最终交付前的完整质检

- [ ] 检查整个项目是否可复现。
  - 原始参考底表在 `data/reference/`
  - 正式输入在 `data/raw/`
  - 中间产物在 `data/interim/`
  - 分析样本在 `data/processed/`
  - 结果表在 `outputs/tables/`
  - 最终论文在 `paper/main.pdf`
- [ ] 记录最终使用的样本口径。
  - 时间窗口
  - 板块范围
  - 问询回复选择逻辑
  - 财务口径定义
  - 异常值处理
- [ ] 记录最终使用的指标定义。
  - `auth_index`
  - `pack_index`
  - 结果变量
  - 控制变量
- [ ] 检查论文中的所有数字都能追溯到输出文件。
- [ ] 检查论文中的所有结论都与表格方向和显著性一致。

## 19. 建议最终保留的成果文件

- [ ] `data/reference/ipo_master/ipo_master_cleaned_2019_2023.xlsx`
- [ ] `data/raw/post_ipo_financials.csv`
- [ ] `data/raw/firm_labels.csv`
- [ ] `data/interim/ipo_manifest.csv`
- [ ] `data/interim/text/document_index.csv`
- [ ] `data/interim/firm_screening.csv`
- [ ] `data/interim/relevant_paragraphs.csv`
- [ ] `data/interim/annotation_tasks.csv`
- [ ] `data/interim/annotation_prompts.jsonl`
- [ ] `data/processed/firm_auth_index.csv`
- [ ] `data/processed/analysis_sample.csv`
- [ ] `outputs/tables/regression_results.csv`
- [ ] `outputs/tables/regression_results.tex`
- [ ] 描述性统计与相关系数表
- [ ] `paper/main.pdf`

## 20. 当前最优先的执行顺序

- [ ] 第一步：补齐清洗底表中的 `industry`、`established_year`、`prospectus_pdf`、`reply_pdf`。
- [ ] 第二步：完成 `data/raw/post_ipo_financials.csv` 的整理。
- [ ] 第三步：跑 `manifest -> text -> screening -> annotation_tasks`。
- [ ] 第四步：完成 LLM 初评与人工复核，生成 `data/raw/firm_labels.csv`。
- [ ] 第五步：统一代码与论文口径。
- [ ] 第六步：跑指数、合并财务、输出回归结果。
- [ ] 第七步：补描述性统计和相关系数表。
- [ ] 第八步：回填 `paper/sections/05_results.tex`，同步更新摘要、结论、附录。
- [ ] 第九步：编译论文并逐页检查 PDF。

## 21. 最容易踩坑的地方

- [ ] 同一企业存在多个版本招股书，误把旧版当终版。
- [ ] 只保留了问询函，没有保留企业回复。
- [ ] 多轮回复只抓了第一轮，漏掉最后一轮完整说明。
- [ ] PDF 是图片版，导致文本抽取后为空。
- [ ] `firm_id` 生成规则不一致，导致文本、标签、财务无法合并。
- [ ] 财务口径没有先写清，导致 `t0/t1` 混乱。
- [ ] 论文中的公式、权重和脚本实际实现不一致。
- [ ] 结果章节只改了数字，没改掉“模板语言”。
- [ ] LaTeX 虽然编译成功，但参考文献、表格宽度或交叉引用仍有问题。
