import pandas as pd
import numpy as np
import os
import statsmodels.api as sm
from linearmodels.panel import PanelOLS

def run_robustness_regression():
    print("=== 开始稳健性检验：替换核心变量分析 ===")
    
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    panel_path = os.path.join(base_dir, 'processed_data', 'final_panel_data.csv')
    res_out_path = os.path.join(base_dir, 'processed_data', 'robustness_results.txt')
    
    # 1. 载入并设置面板索引
    df = pd.read_csv(panel_path)
    df['Year'] = df['Year'].astype(int)
    df['Accper_Time'] = pd.to_datetime(df['Accper'])
    df = df.set_index(['Stkcd', 'Accper_Time'])
    
    # 控制变量维持基准回归的一致性
    controls = ['ROE', '净利润增长率', '营业收入增长率', '资产负债率', 'ln_Asset']
    
    output_buffer = []
    output_buffer.append("========== 稳健性检验：替换变量 (变量=研发总资产强度) ==========\n")
    output_buffer.append("为剥离公司天然规模带来的研发绝对资金差距，这里将核心解释变量由 ln_RD 替换为 RD_Intensity\n\n")
    
    # -------------------------------------------------------------
    # 模型 (1): 验证假设 H1 (当期 RD_Intensity 对 TobinQ 的影响)
    # -------------------------------------------------------------
    print("\n运行检验(1): 稳健性 H1 (当期 R&D 强度与公司估值)")
    exog_vars_1 = ['RD_Intensity'] + controls
    
    df_mod1 = df[['TobinQ', 'Quarter'] + exog_vars_1].dropna()
    quarters_dummy_1 = pd.get_dummies(df_mod1['Quarter'], prefix='Q', drop_first=True)
    
    Y1 = df_mod1['TobinQ']
    X1 = sm.add_constant(pd.concat([df_mod1[exog_vars_1], quarters_dummy_1], axis=1))
    
    # 同样使用个体固定效应 + 聚类稳健标准误
    mod1 = PanelOLS(Y1, X1, entity_effects=True, time_effects=False)
    res1 = mod1.fit(cov_type='clustered', cluster_entity=True)
    
    print(res1.summary)
    output_buffer.append("【检验1: 稳健假设 H1 - 当期 R&D 强度对估值的影响 (带季度固定效应)】\n")
    output_buffer.append(res1.summary.as_text())
    output_buffer.append("\n\n")
    
    # -------------------------------------------------------------
    # 模型 (2): 验证假设 H2 (存在一年滞后效应)
    # -------------------------------------------------------------
    print("\n运行模型(2): 稳健性 H2 (真实滞后1年同季度 R&D 强度与公司估值)")
    exog_vars_2 = ['Lag_1yr_RD_Intensity'] + controls
    
    df_mod2 = df[['TobinQ', 'Quarter'] + exog_vars_2].dropna()
    quarters_dummy_2 = pd.get_dummies(df_mod2['Quarter'], prefix='Q', drop_first=True)
    
    Y2 = df_mod2['TobinQ']
    X2 = sm.add_constant(pd.concat([df_mod2[exog_vars_2], quarters_dummy_2], axis=1))
    
    mod2 = PanelOLS(Y2, X2, entity_effects=True, time_effects=False)
    res2 = mod2.fit(cov_type='clustered', cluster_entity=True)
    
    print(res2.summary)
    output_buffer.append("【检验2: 稳健假设 H2 - 滞后1年同期 R&D 强度对估值的影响 (带季度固定效应)】\n")
    output_buffer.append(res2.summary.as_text())
    output_buffer.append("\n\n")
    
    # 保存稳健性结果
    with open(res_out_path, 'w', encoding='utf-8') as f:
        f.writelines(output_buffer)
    
    print(f"=== 稳健性检验结果已保存至 {res_out_path} ===")

if __name__ == "__main__":
    run_robustness_regression()
