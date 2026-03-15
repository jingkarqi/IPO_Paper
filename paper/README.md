# LaTeX 论文工程说明

主文件：`main.tex`

章节文件：

- `sections/01_abstract.tex`
- `sections/02_introduction.tex`
- `sections/03_literature.tex`
- `sections/04_design.tex`
- `sections/05_results.tex`
- `sections/06_conclusion.tex`
- `sections/appendix.tex`

参考文献：

- `references.bib`

编译命令：

```powershell
powershell -ExecutionPolicy Bypass -File .\build.ps1
```

当前版本说明：

由于当前仓库中尚未导入正式样本数据，实证结果章节保留了表格模板与替换说明。跑完 `src/` 中的回归流程后，可将结果表替换到 `sections/05_results.tex`。
