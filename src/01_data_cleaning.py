import pandas as pd
import numpy as np
import os

# 配置与路径
RAW_DATA_PATH = '../raw_data/merged_data.csv'
CLEANED_DATA_PATH = '../processed_data/cleaned_data.csv'

def winsorize_series(series, limits=(0.01, 0.01)):
    """对 Pandas Series 进行上下分位数的缩尾处理(Winsorization)"""
    lower_limit = series.quantile(limits[0])
    upper_limit = series.quantile(1 - limits[1])
    # 将超出边界的值替换为边界值
    return np.clip(series, lower_limit, upper_limit)

def run_data_cleaning():
    print("=== 开始数据清洗 ===")
    
    # 获取当前执行目录相对于项目根目录的路径，或者确保当前路径
    # 由于该脚本部署在 src 目录下，所以向上级目录寻找
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    raw_path = os.path.join(base_dir, 'raw_data', 'merged_data.csv')
    processed_dir = os.path.join(base_dir, 'processed_data')
    cleaned_path = os.path.join(processed_dir, 'cleaned_data.csv')
    
    # 创建输出文件夹
    if not os.path.exists(processed_dir):
        os.makedirs(processed_dir)

    # 1. 加载数据
    print(f"[{raw_path}] 数据加载中...")
    df = pd.read_csv(raw_path)
    print(f"初始数据形状: {df.shape}")
    
    # 2. 缺失值处理
    # 对于面板回归，保留没有缺失值的核心数据进行回归是最严谨的
    numeric_vars = ['ROE', '净利润增长率', '营业收入增长率', '资产负债率', '总资产', '研发投入', 'TobinQ']
    # 强制将非数值型转换为数值型，无法转换的变为 NaN
    for var in numeric_vars:
        df[var] = pd.to_numeric(df[var], errors='coerce')
        
    df_dropped = df.dropna(subset=numeric_vars)
    print(f"缺失值剔除后形状: {df_dropped.shape}")
    
    # 3. 异常值处理 (Winsorize 1%)
    # 为了避免极端值，在上下 1% 水平上做缩尾处理
    print("对连续变量进行1%和99%水平的 Winsorize 处理...")
    df_cleaned = df_dropped.copy()
    for var in numeric_vars:
        df_cleaned[var] = winsorize_series(df_cleaned[var], limits=(0.01, 0.01))
    
    # 4. 其他类型整理
    df_cleaned['Accper'] = pd.to_datetime(df_cleaned['Accper'], errors='coerce')
    # 再次清理异常日期
    df_cleaned = df_cleaned.dropna(subset=['Accper'])
    
    # 5. 保存结果
    df_cleaned.to_csv(cleaned_path, index=False, encoding='utf-8-sig')
    print(f"=== 数据清洗完成，已保存至 {cleaned_path} ===")
    print(f"最终输出数据形状: {df_cleaned.shape}")

if __name__ == "__main__":
    run_data_cleaning()
