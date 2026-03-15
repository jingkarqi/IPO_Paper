# 资产清单

## 已保留的高价值部分

### 来自 `aaaaaaaaa555`

- `paper/`：分章节 LaTeX 论文骨架、参考文献、PowerShell 编译脚本。
- `materials/reference/annotation_guideline_extended.md`：更细的扩展标注口径说明。
- `materials/reference/variable_definition_notes.md`：变量设计的文字版补充说明。
- `materials/reference/ai_keyword_dictionary_basic.csv`：较简化的备用关键词表。
- 原执行流程文档中的结构思路，已重写到当前项目的 `docs/execution_workflow.md`。

### 来自 `ipo_ai_disclosure_research_package`

- `src/pipeline/`：完整主分析流水线。
- `materials/core/`：核心研究材料，包括筛选规则、标注手册、变量定义、数据清单、LLM 模板。
- `materials/core/ai_keywords_weighted.csv`：与当前筛选脚本直接配套的关键词表。
- `materials/drafts/` 与 `materials/planning/`：提纲、摘要、引言草稿和研究进度安排。

### 来自 `ipo_project`

- `data/reference/ipo_master/`：IPO 样本底表原始版与清洗版。
- `data/reference/validation/`：巨潮校验样例输出。
- `scripts/data_collection/`：基于旧脚本逻辑重写后的样本抓取、清洗、校验工具。

## 有意剔除的内容

- `ipo_ai_disclosure_research_package/paper/main.pdf`
- `ipo_ai_disclosure_research_package/paper/*.aux`
- `ipo_ai_disclosure_research_package/paper/*.log`
- `ipo_ai_disclosure_research_package/paper/*.out`
- `ipo_ai_disclosure_research_package/code/__pycache__/`
- `ipo_project/~$ipo_master_test_with_cninfo.xlsx`

这些文件要么是生成物，要么是临时文件，不适合作为长期主项目的一部分。

## 功能取舍说明

- 主分析流水线统一采用 `ipo_ai_disclosure_research_package` 那一套，因为它覆盖了 `manifest -> PDF文本 -> 筛选 -> 标注任务 -> 指数 -> 回归` 的完整链路。
- `aaaaaaaaa555` 里与主流水线功能重复的旧版脚本没有继续保留到 `src/`，避免项目内部出现两套并行口径。
- 论文工程优先保留 `aaaaaaaaa555` 的分章节 LaTeX 版本，因为后续维护和补写更方便。
