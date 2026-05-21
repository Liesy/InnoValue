import pandas as pd
import numpy as np
import os
from scipy import stats
from sklearn.linear_model import LinearRegression


def calculate_vif(df, features):
    """Calculate Variance Inflation Factor (VIF) for each feature via OLS R²."""
    vif_data = pd.DataFrame()
    vif_data["Feature"] = features
    vif_list = []

    data = df[features].dropna()

    for feature in features:
        X = data.drop(columns=[feature])
        y = data[feature]
        model = LinearRegression()
        model.fit(X, y)
        r_squared = model.score(X, y)
        vif = 1 / (1 - r_squared) if r_squared != 1 else float('inf')
        vif_list.append(vif)

    vif_data["VIF"] = vif_list
    return vif_data


def pearson_with_pvalues(df):
    """
    Compute Pearson correlation matrix with two-tailed p-values.

    Returns:
        corr_matrix: DataFrame of correlation coefficients
        pval_matrix: DataFrame of p-values
    """
    cols = df.columns
    n = len(cols)
    corr_matrix = pd.DataFrame(np.zeros((n, n)), index=cols, columns=cols)
    pval_matrix = pd.DataFrame(np.zeros((n, n)), index=cols, columns=cols)

    for i in range(n):
        for j in range(n):
            if i == j:
                corr_matrix.iloc[i, j] = 1.0
                pval_matrix.iloc[i, j] = 0.0
            elif i < j:
                # Drop rows where either variable is NaN
                mask = df.iloc[:, i].notna() & df.iloc[:, j].notna()
                r, p = stats.pearsonr(df.iloc[mask, i], df.iloc[mask, j])
                corr_matrix.iloc[i, j] = r
                corr_matrix.iloc[j, i] = r
                pval_matrix.iloc[i, j] = p
                pval_matrix.iloc[j, i] = p

    return corr_matrix, pval_matrix


def format_corr_with_stars(corr_matrix, pval_matrix):
    """
    Build a display matrix with significance stars appended to coefficients.

    Stars: *** p<0.01, ** p<0.05, * p<0.1
    Convention: lower triangle shows coefficients with stars,
                diagonal shows 1, upper triangle left blank.
    """
    n = len(corr_matrix)
    display = pd.DataFrame("", index=corr_matrix.index, columns=corr_matrix.columns)

    for i in range(n):
        display.iloc[i, i] = "1"
        for j in range(i):
            r = corr_matrix.iloc[i, j]
            p = pval_matrix.iloc[i, j]
            if p < 0.01:
                star = "***"
            elif p < 0.05:
                star = "**"
            elif p < 0.1:
                star = "*"
            else:
                star = ""
            display.iloc[i, j] = f"{r:.3f}{star}"

    return display


def run_correlation_and_vif():
    print("=== 开始相关性分析与共线性检验 ===")

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    panel_path = os.path.join(base_dir, 'processed_data', 'final_panel_data.csv')
    corr_out_path = os.path.join(base_dir, 'processed_data', 'correlation_matrix.csv')
    corr_pval_path = os.path.join(base_dir, 'processed_data', 'correlation_pvalues.csv')
    corr_stars_path = os.path.join(base_dir, 'processed_data', 'correlation_with_stars.csv')
    vif_out_path = os.path.join(base_dir, 'processed_data', 'vif_results.csv')

    df = pd.read_csv(panel_path)

    # Variables for correlation analysis (dependent + independent + controls)
    vars_to_test = [
        'TobinQ', 'ln_RD', 'Lag_1yr_ln_RD',
        'ROE', '净利润增长率', '营业收入增长率', '资产负债率', 'ln_Asset'
    ]
    corr_df = df[vars_to_test].dropna()
    print(f"\n相关性分析样本量: {len(corr_df)}")

    # 1. Pearson correlation with p-values
    corr_matrix, pval_matrix = pearson_with_pvalues(corr_df)

    print("\n【Pearson 相关系数矩阵】")
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 1000)
    print(corr_matrix.round(3))

    print("\n【P 值矩阵】")
    print(pval_matrix.round(4))

    # Build starred display matrix (lower triangle only, academic convention)
    display_matrix = format_corr_with_stars(corr_matrix, pval_matrix)
    print("\n【带显著性标注的相关系数矩阵（下三角）】")
    print(display_matrix)
    print("\n注: *** p<0.01, ** p<0.05, * p<0.1")

    # Save all three outputs
    corr_matrix.to_csv(corr_out_path, encoding='utf-8-sig')
    pval_matrix.to_csv(corr_pval_path, encoding='utf-8-sig')
    display_matrix.to_csv(corr_stars_path, encoding='utf-8-sig')

    # 2. VIF: compute per model group to avoid inflating VIF by mixing
    #    collinear current/lag variables that never appear in the same regression.
    control_vars = ['ROE', '净利润增长率', '营业收入增长率', '资产负债率', 'ln_Asset']

    vif_groups = [
        ('模型1: 当期 ln_RD',       ['ln_RD'] + control_vars),
        ('模型2: 滞后1年 ln_RD',    ['Lag_1yr_ln_RD'] + control_vars),
        ('模型3: 滞后2年 ln_RD',    ['Lag_2yr_ln_RD'] + control_vars),
        ('模型4: 滞后3年 ln_RD',    ['Lag_3yr_ln_RD'] + control_vars),
    ]

    all_vif_frames = []
    for group_name, vars_list in vif_groups:
        vif_result = calculate_vif(df, vars_list)
        vif_result.insert(0, 'Model', group_name)
        all_vif_frames.append(vif_result)

        print(f"\n【VIF: {group_name}】")
        print(vif_result.round(3).to_string(index=False))

    vif_all = pd.concat(all_vif_frames, ignore_index=True)
    vif_all.to_csv(vif_out_path, index=False, encoding='utf-8-sig')

    print(f"\n=== 相关性及VIF检验完成，文件已保存至 processed_data 目录 ===")


if __name__ == "__main__":
    run_correlation_and_vif()
