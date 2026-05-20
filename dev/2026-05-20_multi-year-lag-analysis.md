# 2026-05-20 新增多期滞后动态分析 (Lag 2yr / 3yr)

## Task
在现有滞后 1 年分析的基础上，扩展至滞后 2 年和 3 年的动态效应分析，以展示 R&D 投入对估值的跨期演进规律。

## Assumptions
- 汉王科技 (Stkcd=2362) 和三六零 (Stkcd=601360) 原始数据仅覆盖至 2022 年，在滞后 ≥2 年的模型中有效观测不足（各仅 2 条），予以剔除
- 滞后 1 年模型保持原有 17 家公司不变，以兼容已有结论
- 滞后 2 年: 200 行 / 15 家公司; 滞后 3 年: 147 行 / 15 家公司

## Implementation

### Modified files
1. **`src/02_variable_construction.py`**: 将单一 1 年滞后构造改为 `for lag_years in [1, 2, 3]` 循环，新增 `Lag_2yr_ln_RD`, `Lag_2yr_RD_Intensity`, `Lag_3yr_ln_RD`, `Lag_3yr_RD_Intensity`
2. **`src/extract_revenue.py`**: 同样将营收比率滞后从单一 1 年扩展至 1/2/3 年循环，新增 `Lag_2yr_RD_Sales_Intensity`, `Lag_3yr_RD_Sales_Intensity`

### New files
3. **`src/07_dynamic_lag_analysis.py`** [NEW]: 12 个模型的动态滞后对比分析脚本
   - 三大 R&D 度量维度 × (当期 + Lag1 + Lag2 + Lag3) = 12 个 PanelOLS 模型
   - 滞后 ≥2 年模型自动剔除 EXCLUDE_LAG2_STKCDS = {2362, 601360}
   - 输出完整回归详情 + 汇总对比表至 `processed_data/dynamic_lag_results.txt`

## Verification
- 管线重跑: `02_variable_construction.py` → `extract_revenue.py` → `07_dynamic_lag_analysis.py` 全部成功
- 面板数据 `final_panel_data.csv` 含 26 列，9 个滞后列非空数完全符合预期 (271/204/147)
- 12 个回归模型全部正常收敛

## Key Results

| 模型 | 当期 | 滞后1年 | 滞后2年 | 滞后3年 |
|:-----|:-----|:--------|:--------|:--------|
| ln_RD | +1.81*** | +1.70 | **+2.56** ** | +1.27 |
| RD/总资产 | -0.25 | +8.69 | +11.47 | +11.10 |
| RD/营收 | -0.24 | +12.15 | **+15.93** ** | +13.97 |

核心发现：
- **RD/营收维度的滞后 2 年系数达到 +15.93 并在 5% 水平显著 (P=0.046)**，这是所有模型中第一个在相对强度维度上击穿统计显著性门槛的结果
- 绝对量度 ln_RD 在滞后 2 年达到峰值 (+2.56, P=0.036)
- 滞后 3 年系数回落但仍保持正向，暗示估值反转效应在第 2 年达到峰值后逐渐消退

## Risks
- 滞后 3 年样本仅 147 行，统计功效有限
- 现有结论基于 15-18 家 AI 公司，样本外推力有限

## Next Steps
- 可更新 `docs/Chapter_Empirical_Study.md` 加入多期滞后发现
- 可绘制系数动态演进折线图用于论文展示
