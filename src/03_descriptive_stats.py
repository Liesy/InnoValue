import pandas as pd
import numpy as np
import os

def run_descriptive_stats():
    print("=== 开始描述性统计分析 ===")
    
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    panel_path = os.path.join(base_dir, 'processed_data', 'final_panel_data.csv')
    stats_out_path = os.path.join(base_dir, 'processed_data', 'descriptive_stats.csv')
    
    # 获取需要统计的变量
    df = pd.read_csv(panel_path)
    # 添加处理前绝对值以及修正名称
    vars_to_describe = [
        'TobinQ', '研发投入', 'ln_RD', 'RD_Intensity', 'Lag_1yr_ln_RD', 'Lag_1yr_RD_Intensity',
        '总资产', '营业总收入', 'ROE', '净利润增长率', '营业收入增长率', '资产负债率', 'ln_Asset'
    ]
    
    # 计算统计量：样本量、均值、标准差、最小值、25分位数、中位数、75分位数、最大值
    stats_df = df[vars_to_describe].describe().T
    
    # 打印到控制台
    print("\n【描述性统计结果】")
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 1000)
    print(stats_df)
    
    # 保存结果备用
    stats_df.to_csv(stats_out_path, encoding='utf-8-sig')
    print(f"\n=== 完毕，表格已保存至 {stats_out_path} ===")

if __name__ == "__main__":
    run_descriptive_stats()
