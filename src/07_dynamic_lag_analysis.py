"""
Dynamic multi-period lag analysis for R&D investment and firm valuation.

Runs PanelOLS (entity FE + clustered SE) regressions across current,
1-year, 2-year, and 3-year lags for three R&D measures:
  - Absolute: ln_RD
  - Intensity (asset-based): RD_Intensity
  - Intensity (revenue-based): RD_Sales_Intensity

Excludes Stkcd 2362 (汉王科技) and 601360 (三六零) from lag >= 2 models
due to insufficient time depth (original data ends at 2022).
"""

import pandas as pd
import numpy as np
import os
import statsmodels.api as sm
from linearmodels.panel import PanelOLS


# Companies to exclude from lag >= 2 year models
EXCLUDE_LAG2_STKCDS = {2362, 601360}


def run_dynamic_lag_analysis():
    print("=== 开始多期滞后动态分析 ===\n")

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    panel_path = os.path.join(base_dir, 'processed_data', 'final_panel_data.csv')
    res_out_path = os.path.join(base_dir, 'processed_data', 'dynamic_lag_results.txt')

    # 1. Load panel data
    df = pd.read_csv(panel_path)
    df['Year'] = df['Year'].astype(int)
    df['Accper_Time'] = pd.to_datetime(df['Accper'])
    df = df.set_index(['Stkcd', 'Accper_Time'])

    controls = ['ROE', '净利润增长率', '营业收入增长率', '资产负债率', 'ln_Asset']

    output_buffer = []
    output_buffer.append("=" * 70 + "\n")
    output_buffer.append("多期滞后动态分析：R&D 投入对估值的当期、1/2/3 年滞后效应\n")
    output_buffer.append("=" * 70 + "\n\n")
    output_buffer.append(
        "注：滞后 2 年及 3 年模型中剔除了汉王科技 (2362) 和三六零 (601360)，\n"
        "    因其原始数据仅覆盖至 2022 年，无法提供充足的长期滞后样本。\n\n"
    )

    # 2. Define the three R&D variable families
    rd_families = [
        {
            'label': '维度一：绝对量度 (ln_RD)',
            'current': 'ln_RD',
            'lags': {1: 'Lag_1yr_ln_RD', 2: 'Lag_2yr_ln_RD', 3: 'Lag_3yr_ln_RD'},
        },
        {
            'label': '维度二：研发/总资产 (RD_Intensity)',
            'current': 'RD_Intensity',
            'lags': {1: 'Lag_1yr_RD_Intensity', 2: 'Lag_2yr_RD_Intensity', 3: 'Lag_3yr_RD_Intensity'},
        },
        {
            'label': '维度三：研发/营业收入 (RD_Sales_Intensity)',
            'current': 'RD_Sales_Intensity',
            'lags': {1: 'Lag_1yr_RD_Sales_Intensity', 2: 'Lag_2yr_RD_Sales_Intensity', 3: 'Lag_3yr_RD_Sales_Intensity'},
        },
    ]

    # 3. Collect summary rows for the comparison table
    summary_rows = []

    def run_single_model(df_input, exog_var, model_label, lag_years):
        """Run one PanelOLS model, return summary dict and full text."""
        # For lag >= 2, exclude companies with insufficient data
        if lag_years >= 2:
            mask = ~df_input.index.get_level_values(0).isin(EXCLUDE_LAG2_STKCDS)
            df_work = df_input[mask]
        else:
            df_work = df_input

        needed_cols = ['TobinQ', 'Quarter', exog_var] + controls
        df_mod = df_work[needed_cols].dropna()
        quarters_dummy = pd.get_dummies(df_mod['Quarter'], prefix='Q', drop_first=True)

        Y = df_mod['TobinQ']
        X = sm.add_constant(
            pd.concat([df_mod[[exog_var] + controls], quarters_dummy], axis=1)
        )

        mod = PanelOLS(Y, X, entity_effects=True, time_effects=False)
        res = mod.fit(cov_type='clustered', cluster_entity=True)

        # Extract key stats for the core variable
        coef = res.params[exog_var]
        pval = res.pvalues[exog_var]
        tstat = res.tstats[exog_var]
        ci_lo = res.conf_int().loc[exog_var, 'lower']
        ci_hi = res.conf_int().loc[exog_var, 'upper']
        n_obs = int(res.nobs)
        n_ent = int(res.entity_info['total'])
        r2w = res.rsquared

        row = {
            'model': model_label,
            'variable': exog_var,
            'coef': coef,
            't_stat': tstat,
            'p_value': pval,
            'ci_lower': ci_lo,
            'ci_upper': ci_hi,
            'r2_within': r2w,
            'n_obs': n_obs,
            'n_entities': n_ent,
        }
        return row, res

    # 4. Run all models
    for family in rd_families:
        output_buffer.append("-" * 70 + "\n")
        output_buffer.append(f"{family['label']}\n")
        output_buffer.append("-" * 70 + "\n\n")

        # Current period
        label = f"当期 {family['current']}"
        print(f"运行: {label}")
        row, res = run_single_model(df, family['current'], label, lag_years=0)
        row['family'] = family['label']
        summary_rows.append(row)
        output_buffer.append(f"【{label}】\n")
        output_buffer.append(res.summary.as_text())
        output_buffer.append("\n\n")

        # Lag 1/2/3
        for lag_yr, var_name in family['lags'].items():
            label = f"滞后{lag_yr}年 {var_name}"
            print(f"运行: {label}")
            row, res = run_single_model(df, var_name, label, lag_years=lag_yr)
            row['family'] = family['label']
            summary_rows.append(row)
            output_buffer.append(f"【{label}】\n")
            output_buffer.append(res.summary.as_text())
            output_buffer.append("\n\n")

    # 5. Build the consolidated comparison table
    output_buffer.append("=" * 70 + "\n")
    output_buffer.append("汇总对比表：核心变量系数的动态演进\n")
    output_buffer.append("=" * 70 + "\n\n")

    summary_df = pd.DataFrame(summary_rows)

    for family in rd_families:
        sub = summary_df[summary_df['family'] == family['label']]
        output_buffer.append(f"\n{family['label']}:\n")
        output_buffer.append(
            f"{'模型':<30s} {'系数':>10s} {'T值':>8s} {'P值':>8s} "
            f"{'R²(W)':>8s} {'N':>6s} {'公司':>4s}\n"
        )
        output_buffer.append("-" * 80 + "\n")
        for _, r in sub.iterrows():
            sig = ""
            if r['p_value'] < 0.01:
                sig = "***"
            elif r['p_value'] < 0.05:
                sig = "**"
            elif r['p_value'] < 0.1:
                sig = "*"
            output_buffer.append(
                f"{r['model']:<30s} {r['coef']:>9.4f}{sig:<3s} "
                f"{r['t_stat']:>8.3f} {r['p_value']:>8.4f} "
                f"{r['r2_within']:>8.4f} {r['n_obs']:>6d} {r['n_entities']:>4d}\n"
            )
        output_buffer.append("\n")

    output_buffer.append("显著性标记: *** p<0.01, ** p<0.05, * p<0.1\n")

    # 6. Save
    with open(res_out_path, 'w', encoding='utf-8') as f:
        f.writelines(output_buffer)

    print(f"\n=== 动态滞后分析完成，结果已保存至 {res_out_path} ===")


if __name__ == "__main__":
    run_dynamic_lag_analysis()
