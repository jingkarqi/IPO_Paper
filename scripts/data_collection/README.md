# Data Collection Scripts

这组脚本负责维护 IPO 样本底表，不直接进入论文主回归，但决定后续样本范围和 PDF 抽取质量。

## 推荐顺序

1. 用 `build_ipo_master_ak.py` 抓一个 A 股 IPO 样本底表。
2. 用 `clean_ipo_master.py` 统一板块、日期和字段。
3. 用 `validate_ipo_by_cninfo.py` 对一部分样本做巨潮校验。
4. 如果你更依赖 Tushare，再用 `build_ipo_master_tushare.py` 作为补充来源。

## 环境说明

- `build_ipo_master_tushare.py` 需要 `TUSHARE_TOKEN`
- 其余脚本依赖 `akshare`
