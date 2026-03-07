import pandas as pd
import numpy as np
import os

def construct_variables():
    print("=== 开始变量构造与面板融合 ===")
    
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cleaned_path = os.path.join(base_dir, 'processed_data', 'cleaned_data.csv')
    panel_path = os.path.join(base_dir, 'processed_data', 'final_panel_data.csv')
    
    # 1. 读入清洗后数据
    df = pd.read_csv(cleaned_path)
    
    # 2. 从日期(Accper)中提取面板核心基准：Year
    df['Accper'] = pd.to_datetime(df['Accper'])
    df['Year'] = df['Accper'].dt.year
    df['Quarter'] = df['Accper'].dt.quarter
    
    # 3. 构造变量对数和强度
    # （1）总资产对数化 ln_Asset
    df['ln_Asset'] = np.log(df['总资产'].replace(0, np.nan))
    
    # （2）研发投入对数化 ln_RD (防范0)
    df['ln_RD'] = np.log(df['研发投入'] + 1)
    
    # （3）研发强度 RD_Intensity（研发投入 / 营业收入... 这里假设没有单列营业收入总额可以考虑总资产，这里用总资产更为严密）
    df['RD_Intensity'] = df['研发投入'] / df['总资产']
    
    # 4. 按公司和时间升序排列，构造可能需要的滞后期
    # 设定多级索引为 面板数据规范
    df = df.sort_values(by=['Stkcd', 'Year', 'Quarter'])
    
    # 构造滞后1期的滞后项 (Lag_1_ln_RD 和 Lag_1_RD_Intensity)
    # df.groupby('Stkcd')['ln_RD'].shift(1) 可以提取上一个周期的值
    df['Lag_1_ln_RD'] = df.groupby('Stkcd')['ln_RD'].shift(1)
    df['Lag_1_RD_Intensity'] = df.groupby('Stkcd')['RD_Intensity'].shift(1)
    
    # 因为存在部分只有 2021而没2020的情况，shift操作会产生NaN，这是滞后效应测试的正规折损
    # 作为面板数据可以直接提供包含空值滞后项的csv给后续选用dropna
    
    # 5. 保存带有生成字段且排序完成的面板数据核心表
    df.to_csv(panel_path, index=False, encoding='utf-8-sig')
    print(f"新增字段：['Year', 'Quarter', 'ln_Asset', 'ln_RD', 'RD_Intensity', 'Lag_1_ln_RD', 'Lag_1_RD_Intensity']")
    print(f"=== 对数处理与面板整理完成，已保存至 {panel_path} ===")

if __name__ == "__main__":
    construct_variables()
