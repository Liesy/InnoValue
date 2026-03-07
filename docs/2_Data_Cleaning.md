# 数据整理与清洗 (Data Cleaning)

## 1. 缺失值处理
原始数据 `raw_data/merged_data.csv` 含有 522 条非平衡面板样本数据。由于本研究重点探讨研发投入对 Tobin's Q 的影响，任何核心变量的缺失都不能为回归模型提供有效信息。相比于多重插补，直接剔除缺失值更为客观严谨。

处理后：删除了在核心连续变量（ROE, 净利润增长率, 营业收入增长率, 资产负债率, 总资产, 研发投入, TobinQ）上具有 NaN 空值的行。清洗掉这部分噪音后，样本最终剩余 **345** 条高质量观测记录。

## 2. 异常值处理 (Winsorization)
在公司财务指标如净利润增长率、资产负债率中，往往容易受到极值拉抬或压低，从而导致异方差或偏倚的参数估计结果。
为此，我们在 Python 中利用 Numpy 的裁剪功能，将各项核心连续型变量在其 **1%** 和 **99%** 分位数处进行了 Winsorize 缩尾处理。超出该区间范围的极高值或极低记录被强制拉回并同值替换为对应界限的值。

该策略最大程度地保障了异常值不再牵引回归曲线，并维持了原始样本数量。最终清洗后的分析数据集保存于：`processed_data/cleaned_data.csv`。

---

## 💻 附：Python 代码小白通俗解析
如果你完全不懂编程，可以看看这里的“大白话”翻译。这部分代码记录在本项目 `src/01_data_cleaning.py` 文件中，它是我们全套分析的“净水器”。

#### 第一层：教电脑“剔除坏样本” (处理缺失值)
```python
# 找到我们关心的这几列（即研究里的核心变量）
numeric_vars = ['ROE', '净利润增长率', '营业收入增长率', '资产负债率', '总资产', '研发投入', 'TobinQ']

for var in numeric_vars:
    # pd.to_numeric 的意思是：强制把这一列的字都当成数字看，如果遇到写着“未知”或者空白填歪了的，直接变成 NaN（电脑眼里的“空”）
    df[var] = pd.to_numeric(df[var], errors='coerce')
    
# dropna (drop NA) 意思是：只要这几列里只要有任何一列是 NaN (空的)，就把这整家公司在这个季度的【这一行】完全扔进垃圾桶。
df_dropped = df.dropna(subset=numeric_vars)
```
**解读**：就像老师改卷子，只看那些把选择题全部涂满的学生成绩，只要有一道题（这里指研发投入等变量）漏涂了，这张卷子就作废，保证留下的纸面数据都是完美的。

#### 第二层：教电脑“掐头去尾” (异常值缩尾处理)
```python
def winsorize_series(series, limits=(0.01, 0.01)):
    # upper_limit 就是找出这堆数字里，排在最前面 99% 的那个分数线
    # lower_limit 就是找出排在最后 1% 的那个分数线
    lower_limit = series.quantile(limits[0])
    upper_limit = series.quantile(1 - limits[1])
    
    # np.clip 就像一把剪刀加上一根橡皮筋：
    # 把所有比 upper_limit 还大的“过高离谱值”，全部强拽下来，变成 upper_limit。
    # 把所有比 lower_limit 还小的“过低离谱值”，全部拽上来，变成 lower_limit。
    return np.clip(series, lower_limit, upper_limit)

# 对刚刚留下来的干净数据，挨个变量使用这把“剪刀”
for var in numeric_vars:
    df_cleaned[var] = winsorize_series(df_cleaned[var], limits=(0.01, 0.01))
```
**解读**：这叫做“去极端化”。比如算全班平均分，有个天才考了 1000 分，有个同学考了 -500 分，这会严重破坏平均数。代码干的事情就是：把天才的成绩降成班里第2名的成绩（比如99分），把那个 -500 分的同学变成倒数第2名的成绩（比如10分）。大家都被挤在了一个正常的常理范围内，避免走极端。

#### 第三层：保存洗好的数据
```python
# to_csv 就是把 Python 内存里处理好的数据，写成平时你用 Excel 能打得开的 .csv 电子表格。
df_cleaned.to_csv(cleaned_path, index=False, encoding='utf-8-sig')
```
**解读**：洗完菜之后，装盘打包，放在 `processed_data/cleaned_data.csv` 里面，交给下一个厨师（第二步的脚本）去切配。
