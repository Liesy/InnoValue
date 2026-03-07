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
    
    # 4. 按公司和时间升序排列
    df = df.sort_values(by=['Stkcd', 'Accper'])
    
    # 构造滞后4期的滞后项 (即前一年同一季度的 R&D，以控制报表累计波动并提供明确的1年滞后)
    # 策略：创建一个副本，使其日期向未来平移1年(4个季度)，然后再和原表按 (公司, 时间) 进行左连接
    df_lag = df[['Stkcd', 'Accper', 'ln_RD', 'RD_Intensity']].copy()
    # 加上一年（通常为四个季度的距离，相当于去年的现在）
    df_lag['Accper'] = df_lag['Accper'] + pd.DateOffset(years=1)
    
    # 重命名准备合并
    df_lag = df_lag.rename(columns={
        'ln_RD': 'Lag_1yr_ln_RD',
        'RD_Intensity': 'Lag_1yr_RD_Intensity'
    })
    
    # 按照实体和时间严格合并，只要原表中当前季度没有找到去年同季度的记录，就会留空 (NaN)
    df = pd.merge(df, df_lag, on=['Stkcd', 'Accper'], how='left')
    
    # 5. 保存带有生成字段且排序完成的面板数据核心表
    df.to_csv(panel_path, index=False, encoding='utf-8-sig')
    print(f"新增字段：['Year', 'Quarter', 'ln_Asset', 'ln_RD', 'RD_Intensity', 'Lag_1yr_ln_RD', 'Lag_1yr_RD_Intensity']")
    print(f"=== 对数处理与面板整理完成，已保存至 {panel_path} ===")

if __name__ == "__main__":
    construct_variables()
