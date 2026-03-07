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
    output_buffer.append("========== 稳健性检验：双重核心比例变量替换分析 ==========\n")
    output_buffer.append("为从不同维度剥离公司天然体型差距，本检验分布使用 '研发投入/总资产'(RD_Intensity) "
                         "和 '研发投入/营业总收入'(RD_Sales_Intensity) 进行对比估计。\n\n")
    
    # 定义辅助回归函数
    def run_panel_model(exog_var, model_name, desc):
        print(f"\n运行: {model_name} ({desc})")
        df_mod = df[['TobinQ', 'Quarter', exog_var] + controls].dropna()
        quarters_dummy = pd.get_dummies(df_mod['Quarter'], prefix='Q', drop_first=True)
        
        Y = df_mod['TobinQ']
        X = sm.add_constant(pd.concat([df_mod[[exog_var] + controls], quarters_dummy], axis=1))
        
        mod = PanelOLS(Y, X, entity_effects=True, time_effects=False)
        res = mod.fit(cov_type='clustered', cluster_entity=True)
        
        print(res.summary)
        output_buffer.append(f"【{model_name}: {desc}】\n")
        output_buffer.append(res.summary.as_text())
        output_buffer.append("\n\n")

    # -------------------------------------------------------------
    # 维度一：基于总资产的研发强度 (RD_Intensity)
    # -------------------------------------------------------------
    output_buffer.append("--- 维度一：(研发投入 / 总资产) ---\n\n")
    run_panel_model('RD_Intensity', '模型 A1', '当期 R&D 资产占比对估值的影响')
    run_panel_model('Lag_1yr_RD_Intensity', '模型 A2', '滞后1年同期 R&D 资产占比对估值的影响')

    # -------------------------------------------------------------
    # 维度二：基于营业收入的研发强度 (RD_Sales_Intensity)
    # -------------------------------------------------------------
    output_buffer.append("--- 维度二：(研发投入 / 营业收入) ---\n\n")
    run_panel_model('RD_Sales_Intensity', '模型 B1', '当期 R&D 营收占比对估值的影响')
    run_panel_model('Lag_1yr_RD_Sales_Intensity', '模型 B2', '滞后1年同期 R&D 营收占比对估值的影响')
    
    # 保存稳健性结果
    with open(res_out_path, 'w', encoding='utf-8') as f:
        f.writelines(output_buffer)
    
    print(f"=== 稳健性检验结果已保存至 {res_out_path} ===")

if __name__ == "__main__":
    run_robustness_regression()
