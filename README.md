# InnoValue: AI企业研发投入与估值实证研究项目

## 项目概述 (Overview)

**InnoValue** 是一个完整的计量经济学实证研究项目。本项目以 CSMAR 数据库中 18 家中国 A 股头部 AI 相关上市公司（覆盖 2020Q4–2024）的财务面板数据为底座，深入探讨了**企业研发投入 (R&D) 对公司资本市场估值 (Tobin's Q) 的当期驱动与跨期滞后效应**。

本项目包含从底层原始数据的抽取清洗，到核心面板变量的设计构造，再到双向固定效应多元回归与稳健性检验（基于多基准规模缩放指标）的全流程实证代码与学术报告。

## 目录结构与核心文档 (Project Structure & Docs)

本项目按操作顺序分为多个严谨的实证分析阶段。在 `docs/` 目录下存放了所有阶段对应的学术报告材料和带有通俗代码解析的研讨版说明：

1. [核心研究假设 (Research Hypothesis)](docs/1_Research_Hypothesis.md)
2. [数据整理与清洗 (Data Cleaning)](docs/2_Data_Cleaning.md)
3. [变量定义与面板数据汇总 (Variables and Panel Data)](docs/3_Variables_and_Panel_Data.md)
4. [描述性统计分析 (Descriptive Statistics)](docs/4_Descriptive_Statistics.md)
5. [相关性与多重共线性检验 (Correlation and Multicollinearity)](docs/5_Correlation_and_Multicollinearity.md)
6. [基准回归分析 (Baseline Regression)](docs/6_Baseline_Regression.md)
7. [稳健性检验 (Robustness Checks)](docs/7_Robustness_Checks.md)
8. **👑 [博士论文终版实证核心大章 (Final Empirical Chapter)](docs/Chapter_Empirical_Study.md)** 

## 数据提取与合并

本项目从 CSMAR 数据库的多个 Excel 数据表中，提取 18 家 AI 相关上市公司的关键财务与市场指标，合并为一个统一的 CSV 文件，供后续研究使用。

### 目标公司

来源：`raw_data/filtered_tobinq.xlsx`，共 **18 家公司**，覆盖 2020Q4–2024 时间段。

| Stkcd  | 公司简称 |
|--------|----------|
| 938    | 紫光股份 |
| 977    | 浪潮信息 |
| 2230   | 科大讯飞 |
| 2362   | 汉王科技 |
| 300002 | 神州泰岳 |
| 300033 | 同花顺   |
| 300229 | 拓尔思   |
| 300308 | 中际旭创 |
| 300339 | 润和软件 |
| 300394 | 天孚通信 |
| 300418 | 昆仑万维 |
| 300474 | 景嘉微   |
| 300502 | 新易盛   |
| 300624 | 万兴科技 |
| 601138 | 工业富联 |
| 601360 | 三六零   |
| 603019 | 中科曙光 |
| 688256 | 寒武纪   |

### 数据源与提取列

从以下 6 个 CSMAR 数据表中各提取指定列：

| 数据表 | 文件 | 提取列（Excel 列号） | 输出列名 | CSMAR 字段编码 |
|--------|------|---------------------|----------|---------------|
| 盈利能力表 | `盈利能力.xlsx` | AA列 | ROE | F050502B |
| 发展能力表 | `发展能力.xlsx` | Z列 | 净利润增长率 | F081001B |
| 发展能力表 | `发展能力.xlsx` | AI列 | 营业收入增长率 | F081601B |
| 偿债能力表 | `偿债能力.xlsx` | U列 | 资产负债率 | F011201A |
| 资产负债表 | `资产负债表.xlsx` | CC列 | 总资产 | A001000000 |
| 利润表 | `利润表.xlsx` | AO列 | 研发投入 | B001216000 |
| TobinQ 表 | `tobinq.xlsx` | AB列 | TobinQ | F100903A |

### 数据处理逻辑

#### 1. 源数据特征

- 各 Excel 文件第 1 行为英文列名，第 2、3 行为中文字段描述和单位说明，实际数据从第 4 行开始
- `Stkcd`（股票代码）在大表中为零填充字符串（如 `"000938"`），在 `filtered_tobinq.xlsx` 中为整数（如 `938`）
- 大部分表包含 `Typrep` 列，区分合并报表（`A`）和母公司报表（`B`）

#### 2. 处理步骤

1. **读取目标公司列表**：从 `filtered_tobinq.xlsx` 获取 18 家公司的 `Stkcd`
2. **逐表提取**：
   - 使用 `usecols` 参数只读取所需列（Stkcd、Accper、Typrep、目标数据列），避免加载整个大文件
   - 使用 `skiprows=[1,2]` 跳过中文描述行
   - 过滤只保留**合并报表**（`Typrep='A'`），`tobinq.xlsx` 无此列则跳过
   - 将 `Stkcd` 转为整数格式，匹配目标公司
3. **合并**：按 `Stkcd` + `Accper`（会计期间）逐步 outer merge
4. **关联公司简称**并整理列顺序
5. **输出** CSV 文件

#### 3. 输出文件

- **路径**：`raw_data/merged_data.csv`
- **编码**：UTF-8 with BOM（`utf-8-sig`）
- **行数**：522 行
- **列结构**：

| 列名 | 说明 |
|------|------|
| Stkcd | 股票代码 |
| ShortName | 公司简称 |
| Accper | 会计期间（日期） |
| ROE | 净资产收益率 |
| 净利润增长率 | 净利润同比增长率 |
| 营业收入增长率 | 营业收入同比增长率 |
| 资产负债率 | 资产负债率 |
| 总资产 | 总资产（元） |
| 研发投入 | 研发投入（元） |
| TobinQ | 托宾Q值 |

## 实证分析代码管线 (Source Code Pipeline)

在 `src/` 及 `utils/` 目录下，包含了一键即可复现所有实验结果的系列 Python 脚本串联栈：

| 顺序 | 脚本路径 | 核心作用说明 |
| :--- | :--- | :--- |
| **00** | `utils/extract_and_merge.py` | (预处理) 解析 CSMAR 庞大的原始 Excel 财务多表，并按股票代码 `Stkcd` 和报表期提纯组装基础大宽表 (`raw_data/merged_data.csv`) |
| **00-B** | `src/extract_revenue.py` | (特征补充) 专门从利润表剥离提取核心分母特征“营业总收入”，用于计算营收比滞后参数 |
| **01** | `src/01_data_cleaning.py` | 清洗缺失样本，并在 1% 与 99% 分位数执行严格的极值 Winsorize 缩尾平滑处理 |
| **02** | `src/02_variable_construction.py` | 转化绝对金额对数 ($ln$)；构建基于总资产占比的研发强度；应用时间平移法计算 1/2/3 年度滞后因子 |
| **03** | `src/03_descriptive_stats.py` | 输出面板样本数据关键变量分布情况的中英文对照描述性统计报表 |
| **04** | `src/04_correlation_vif.py` | 构建带 P 值显著性标注的 Pearson 矩阵，并按各模型变量组合分组实施 VIF 方差膨胀检测 |
| **05** | `src/05_baseline_regression.py` | 应用面板数据个体固定效应以及聚类鲁棒标准误 (`PanelOLS`) 并导入季度虚拟控制变量，实施主回归测算 |
| **06** | `src/06_robustness_checks.py` | 引入并列循环的多维替换变量（研发/总资产 及 研发/营业收入），自动比对验证短长期的估值倒置反转规律 |
| **07** | `src/07_dynamic_lag_analysis.py` | 多期滞后动态分析：对三种 R&D 度量维度在当期、滞后 1/2/3 年的 12 模型 PanelOLS 系数演进对比 |

## 快速复现 (Quick Start)

环境依赖要求：Python 3.12 及以上，核心分析包基于 `pandas`, `numpy`, `scipy`, `statsmodels`, `linearmodels`。

```bash
# 1. 提取原始数据表并在宽表中融合营业总收入
python utils/extract_and_merge.py
python src/extract_revenue.py

# 2. 从头执行全套核心分析流 (可依次单独执行)
python src/01_data_cleaning.py
python src/02_variable_construction.py
python src/03_descriptive_stats.py
python src/04_correlation_vif.py
python src/05_baseline_regression.py
python src/06_robustness_checks.py
python src/07_dynamic_lag_analysis.py
```

## 核心实证结论预告

本项目在研究论证中发现了强烈的**戴维斯双击（Davis Double Play）机制异响**：
即大金额层面的研发资金规模会很快在当期推高企业市值；但在相对强度的考量维度中（即剥离规模量纲后审视研发下注比例），短期的市场倾向于惩罚这些报表利润受到极度压抑的创新开拓企业。然而历经一至两年季报的沉淀出清后，前期的超额高比例研发投入会爆发出惊人的估值跨越反转溢价。

多期滞后动态分析进一步揭示了估值反转的**倒 U 型时序轨迹**：研发营收比的估值系数从当期 -0.24 → 滞后1年 +12.15 → **滞后2年 +15.93 (P=0.046, 统计显著)** → 滞后3年 +13.97，在第二年达到峰值后逐渐回落。详细学术推演请见 `docs/Chapter_Empirical_Study.md`。
