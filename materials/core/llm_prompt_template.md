# LLM 辅助标注 Prompt 模板

以下模板适合复制到你使用的大模型工具中。建议一次输入一家企业整理后的 6-10 段关键文本，而不是整份招股书全文。

---

## System / Role Prompt

你是一名管理学与信息披露研究助理。你的任务不是判断企业“好不好”，而是根据给定文本，帮助研究者识别 IPO 企业关于 AI / 数字化披露的**真实性与包装性特征**。请严格根据文本内容评分，不要用常识替代文本，不要擅自补充事实。

你必须按 JSON 输出，不得输出任何多余说明。

## User Prompt

请阅读以下来自某 IPO 企业招股说明书与问询回复的相关段落，并完成评分。

### 评分规则

1. `scene_specificity`（0-3）
- 0 = 纯口号、纯概念
- 1 = 有方向但较抽象
- 2 = 有明确业务环节或技术对象
- 3 = 场景清晰且可落地

2. `prudence`（0-3）
- 0 = 明显宣传式或承诺式
- 1 = 宣传与事实混合
- 2 = 基本客观、偏事实陈述
- 3 = 高度审慎、边界清楚

3. `packaging_risk`（0-3）
- 0 = 几乎无包装风险
- 1 = 轻度包装
- 2 = 中度包装
- 3 = 高度包装

4. `evidence_support`（0-2）
- 0 = 无证据
- 1 = 弱证据
- 2 = 强证据

### 输出要求

请输出如下 JSON：

```json
{
  "firm_id": "",
  "scene_specificity": 0,
  "prudence": 0,
  "packaging_risk": 0,
  "evidence_support": 0,
  "key_scenarios": [""],
  "packaging_signals": [""],
  "evidence_signals": [""],
  "final_judgement": "一句话总结，说明更接近真实转型还是叙事包装",
  "confidence": "high/medium/low"
}
```

### 待评文本

{{TEXT_BLOCK}}

---

## 使用建议

1. 先让模型给初评；
2. 人工只复核模型置信度为 `low` 或打分冲突较大的样本；
3. 同一家企业至少保留一句人工复核备注；
4. 最终写回 `firm_labels.csv`。
