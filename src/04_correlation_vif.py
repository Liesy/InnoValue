import pandas as pd
import numpy as np
import os
from sklearn.linear_model import LinearRegression

def calculate_vif(df, features):
    """手动计算特征的方差膨胀因子（VIF）以便无痛兼容环境"""
    vif_data = pd.DataFrame()
    vif_data["Feature"] = features
    vif_list = []
    
    # 确保没有空值参与回归
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

def run_correlation_and_vif():
    print("=== 开始相关性分析与共线性检验 ===")
    
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    panel_path = os.path.join(base_dir, 'processed_data', 'final_panel_data.csv')
    corr_out_path = os.path.join(base_dir, 'processed_data', 'correlation_matrix.csv')
    vif_out_path = os.path.join(base_dir, 'processed_data', 'vif_results.csv')
    
    df = pd.read_csv(panel_path)
    
    # 选取进行相关性和多重共线性检验的变量（自变量+控制变量为主，这里也把因变量拉进相关系数看初步关系）
    vars_to_test = [
        'TobinQ', 'ln_RD', 'Lag_1_ln_RD',
        'ROE', '净利润增长率', '营业收入增长率', '资产负债率', 'ln_Asset'
    ]
    corr_df = df[vars_to_test].dropna()
    
    # 1. 相关系数矩阵 (Pearson)
    pearson_corr = corr_df.corr(method='pearson')
    print("\n【Pearson 相关系数矩阵】")
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 1000)
    print(pearson_corr.round(3))
    pearson_corr.to_csv(corr_out_path, encoding='utf-8-sig')
    
    # 2. VIF 检验 (只检验自变量与控制变量间的共线性)
    iv_vars = ['ln_RD', 'Lag_1_ln_RD', 'ROE', '净利润增长率', '营业收入增长率', '资产负债率', 'ln_Asset']
    vif_results = calculate_vif(df, iv_vars)
    
    print("\n【多重共线性 VIF 检验结果】")
    print(vif_results.round(3))
    vif_results.to_csv(vif_out_path, index=False, encoding='utf-8-sig')
    
    print(f"\n=== 相关性及VIF检验完成，文件已保存至 processed_data 目录 ===")

if __name__ == "__main__":
    run_correlation_and_vif()
