import pandas as pd
import numpy as np
import os

def extract_revenue_and_merge():
    print("=== 开始提取营业总收入并合成新面板数据 ===")
    
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    income_path = os.path.join(base_dir, 'raw_data', '利润表.xlsx')
    panel_path = os.path.join(base_dir, 'processed_data', 'final_panel_data.csv')
    
    # 1. 提取 H 列数据 (第8列)
    # H 列即大写的营业总收入
    print(f"读取 {income_path}...")
    
    def col_letter_to_index(letter: str) -> int:
        result = 0
        for c in letter.upper():
            result = result * 26 + (ord(c) - ord("A") + 1)
        return result - 1
        
    stkcd_idx = col_letter_to_index('A')
    accper_idx = col_letter_to_index('C')
    typrep_idx = col_letter_to_index('D')
    h_idx = col_letter_to_index('H')
    
    usecols = [stkcd_idx, accper_idx, typrep_idx, h_idx]
    
    # 必须跳过第 2 和第 3 行 (索引 1 和 2)
    df_income = pd.read_excel(income_path, usecols=usecols, skiprows=[1, 2])
    
    # 只提取合并报表（Typrep = 'A'）
    typrep_col = df_income.columns[2]
    df_income = df_income[df_income[typrep_col] == 'A'].copy()
    df_income = df_income.drop(columns=[typrep_col])
    
    # 重命名列
    h_col_name = df_income.columns[2]
    df_income = df_income.rename(columns={h_col_name: '营业总收入'})
    
    # Stkcd 统一转为数字以匹配现有面板
    df_income["Stkcd"] = pd.to_numeric(df_income["Stkcd"], errors="coerce").astype("Int64")
    
    # 统一日期格式以便 merge
    df_income['Accper'] = pd.to_datetime(df_income['Accper'], errors='coerce')
    df_income = df_income.dropna(subset=['Accper'])
    
    # 如果利润表针对同一家公司和同一天有多条类型(例如母公司和合并表)，通常保留最新或首条
    df_income = df_income.drop_duplicates(subset=['Stkcd', 'Accper'], keep='first')
        
    # 2. 与现有面板合并
    print(f"\n读取现有面板表: {panel_path}")
    df_panel = pd.read_csv(panel_path)
    df_panel['Accper'] = pd.to_datetime(df_panel['Accper'])
    
    original_shape = df_panel.shape
    df_merged = pd.merge(df_panel, df_income, on=['Stkcd', 'Accper'], how='left')
    
    # 3. 计算基于营业收入的研发强度 (RD / Sales)
    # 处理可能的 0 营收和缺失值问题
    df_merged['营业总收入'] = pd.to_numeric(df_merged['营业总收入'], errors='coerce')
    # 避免除以0或极小的值，对于营业收入小于0或等于0的予以排除或标为np.nan
    df_merged['营业总收入'] = df_merged['营业总收入'].replace(0, np.nan)
    
    # 生成当期的新稳健性测试指标
    df_merged['RD_Sales_Intensity'] = df_merged['研发投入'] / df_merged['营业总收入']
    
    # 因为存在极端异常的营收比(比如收入只有几毛而研发上亿)，我们最好也像处理主核心变量那样做一个简单的1%缩尾
    lower_limit = df_merged['RD_Sales_Intensity'].quantile(0.01)
    upper_limit = df_merged['RD_Sales_Intensity'].quantile(0.99)
    df_merged['RD_Sales_Intensity'] = np.clip(df_merged['RD_Sales_Intensity'], lower_limit, upper_limit)
    
    print(f"\n合并前后数据行数对比: {original_shape[0]} -> {df_merged.shape[0]}")
    missing_revenue = df_merged['营业总收入'].isna().sum()
    print(f"匹配发现营业收入为 NaN 的行数: {missing_revenue} (将在回归中 dropna)")
    
    # 4. 生成 1/2/3 年滞后期（按 02_ 的平移逻辑）
    df_final = df_merged
    lag_cols_added = []
    for lag_years in [1, 2, 3]:
        df_lag = df_final[['Stkcd', 'Accper', 'RD_Sales_Intensity']].copy()
        df_lag['Accper'] = df_lag['Accper'] + pd.DateOffset(years=lag_years)
        col_name = f'Lag_{lag_years}yr_RD_Sales_Intensity'
        df_lag = df_lag.rename(columns={'RD_Sales_Intensity': col_name})
        df_final = pd.merge(df_final, df_lag, on=['Stkcd', 'Accper'], how='left')
        lag_cols_added.append(col_name)
    
    # 5. 覆盖保存
    df_final.to_csv(panel_path, index=False, encoding='utf-8-sig')
    added = ['营业总收入', 'RD_Sales_Intensity'] + lag_cols_added
    print(f"\n成功添加 {added}。")
    print(f"覆盖写回 {panel_path}")

if __name__ == "__main__":
    extract_revenue_and_merge()
