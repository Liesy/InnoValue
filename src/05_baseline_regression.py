import pandas as pd
import numpy as np
import os
import statsmodels.api as sm
from linearmodels.panel import PanelOLS

def run_baseline_regression():
    print("=== 开始基准面板数据回归分析 ===")
    
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    panel_path = os.path.join(base_dir, 'processed_data', 'final_panel_data.csv')
    res_out_path = os.path.join(base_dir, 'processed_data', 'regression_results.txt')
    
    # 1. 读取并设置面板数据的双重索引 [Entity, Time]
    df = pd.read_csv(panel_path)
    df['Year'] = df['Year'].astype(int)
    # Stkcd作为个体(entity_id), Year作为时间(time_id)
    # 由于该数据中存在相同年份不同季度，标准的年份面板需进行季度年度化或将季度直接作为时间戳
    # 为了简化且避免重复项报错，将 Stkcd + Year + Quarter 组合或直接保留用 (Stkcd, Accper) 做索引
    df['Accper_Time'] = pd.to_datetime(df['Accper'])
    df = df.set_index(['Stkcd', 'Accper_Time'])
    
    print(f"载入多级索引面板数据，开始模型构建...")
    
    controls = ['ROE', '净利润增长率', '营业收入增长率', '资产负债率', 'ln_Asset']
    
    output_buffer = []
    output_buffer.append("========== 面板回归（固定效应 FE）实证结果 ==========\n")
    
    # -------------------------------------------------------------
    # 模型 (1): 验证假设 H1 (当期 ln_RD 对 TobinQ 的影响)
    # -------------------------------------------------------------
    print("\n运行模型(1): H1 (当期 R&D 投入与公司估值)")
    exog_vars_1 = ['ln_RD'] + controls
    
    # 引入真实的季度固定效应以消除累计数据带来的误差
    # pd.get_dummies 是引入离散控制变量的最简单途径，配合截距项通常 drop_first
    df_mod1 = df[['TobinQ', 'Quarter'] + exog_vars_1].dropna()
    quarters_dummy_1 = pd.get_dummies(df_mod1['Quarter'], prefix='Q', drop_first=True)
    
    Y1 = df_mod1['TobinQ']
    X1 = sm.add_constant(pd.concat([df_mod1[exog_vars_1], quarters_dummy_1], axis=1))
    
    # 由于加入了Quarter假变量，这里仅需要实体固定效应即可（Year效应非必须，因为已经处理滞后项对齐）
    mod1 = PanelOLS(Y1, X1, entity_effects=True, time_effects=False)
    res1 = mod1.fit(cov_type='clustered', cluster_entity=True)
    
    print(res1.summary)
    output_buffer.append("【模型1: 主假设 H1 - 当期 R&D 投入对估值的影响 (带季度固定效应)】\n")
    output_buffer.append(res1.summary.as_text())
    output_buffer.append("\n\n")
    
    # -------------------------------------------------------------
    # 模型 (2): 验证假设 H2 (存在一年滞后效应)
    # -------------------------------------------------------------
    print("\n运行模型(2): H2 (真实滞后1年同季度 R&D 投入与公司估值)")
    exog_vars_2 = ['Lag_1yr_ln_RD'] + controls
    
    df_mod2 = df[['TobinQ', 'Quarter'] + exog_vars_2].dropna()
    quarters_dummy_2 = pd.get_dummies(df_mod2['Quarter'], prefix='Q', drop_first=True)
    
    Y2 = df_mod2['TobinQ']
    X2 = sm.add_constant(pd.concat([df_mod2[exog_vars_2], quarters_dummy_2], axis=1))
    
    mod2 = PanelOLS(Y2, X2, entity_effects=True, time_effects=False)
    res2 = mod2.fit(cov_type='clustered', cluster_entity=True)
    
    print(res2.summary)
    output_buffer.append("【模型2: 滞后假设 H2 - 滞后1年同期 R&D 投入对估值的影响 (带季度固定效应)】\n")
    output_buffer.append(res2.summary.as_text())
    output_buffer.append("\n\n")
    
    # 将回归结果写入文件
    with open(res_out_path, 'w', encoding='utf-8') as f:
        f.writelines(output_buffer)
    
    print(f"=== 回归结果已保存至 {res_out_path} ===")

if __name__ == "__main__":
    run_baseline_regression()
