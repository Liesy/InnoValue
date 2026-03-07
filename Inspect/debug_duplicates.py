"""
调试数据重复问题：
检查各表中目标公司的 Typrep（报表类型）和 IfCorrect 等列的取值，
找出导致 merge 后行数膨胀的原因。
"""

import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(BASE_DIR, "raw_data")


def main():
    # 目标公司
    ft = pd.read_excel(os.path.join(RAW_DIR, "filtered_tobinq.xlsx"))
    target_stkcds = set(ft["Stkcd"].values)

    # 各表配置: (文件名, 要检查的额外列索引)
    # Typrep 在 index=3（D列）
    files = [
        ("盈利能力.xlsx", [0, 2, 3]),       # Stkcd, Accper, Typrep
        ("发展能力.xlsx", [0, 2, 3]),
        ("偿债能力.xlsx", [0, 2, 3]),
        ("资产负债表.xlsx", [0, 2, 3, 4]),   # + IfCorrect
        ("利润表.xlsx", [0, 2, 3, 4]),       # + IfCorrect
        ("tobinq.xlsx", [0, 2, 3]),          # Source 而不是 Typrep
    ]

    for fname, usecols in files:
        filepath = os.path.join(RAW_DIR, fname)
        print(f"\n{'='*60}")
        print(f"文件: {fname}")

        df = pd.read_excel(filepath, usecols=usecols, skiprows=[1, 2])
        # 统一 Stkcd 类型
        df["Stkcd"] = pd.to_numeric(df["Stkcd"], errors="coerce").astype("Int64")
        df = df[df["Stkcd"].isin(target_stkcds)]

        print(f"  目标公司记录数: {len(df)}")
        print(f"  列: {list(df.columns)}")

        # 看各列的唯一值
        for col in df.columns:
            if col not in ["Stkcd", "Accper"]:
                uniques = df[col].unique()
                print(f"  {col} 的唯一值({len(uniques)}个): {sorted(uniques)[:10]}")

        # 看一个公司一个日期有多少条
        sample = df[df["Stkcd"] == 938]
        if len(sample) > 0:
            sample_date = sample["Accper"].iloc[0]
            dup = sample[sample["Accper"] == sample_date]
            print(f"\n  示例: 紫光股份(938) {sample_date}")
            print(f"  记录数: {len(dup)}")
            print(dup.to_string())


if __name__ == "__main__":
    main()
