"""
调试 Stkcd 匹配问题：
检查各 Excel 表中 Stkcd 的实际数据类型和格式，
与 filtered_tobinq 中的 Stkcd 进行对比。
"""

import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(BASE_DIR, "raw_data")

FILES = [
    "tobinq.xlsx",        # 最小的文件，快速验证
    "偿债能力.xlsx",       # 第二小
]


def main():
    # 1. filtered_tobinq 的 Stkcd
    ft = pd.read_excel(os.path.join(RAW_DIR, "filtered_tobinq.xlsx"))
    print("=== filtered_tobinq.xlsx ===")
    print(f"  Stkcd dtype: {ft['Stkcd'].dtype}")
    print(f"  Stkcd 示例: {list(ft['Stkcd'].head(5))}")
    print(f"  Stkcd 类型: {[type(x).__name__ for x in ft['Stkcd'].head(5)]}")
    target_stkcds = set(ft["Stkcd"].values)

    # 2. 各大表的 Stkcd
    for fname in FILES:
        filepath = os.path.join(RAW_DIR, fname)
        print(f"\n=== {fname} ===")

        # 只读 Stkcd 列（index=0），前 100 行
        df = pd.read_excel(filepath, usecols=[0], nrows=100)
        col_name = df.columns[0]
        print(f"  列名: '{col_name}'")
        print(f"  dtype: {df[col_name].dtype}")
        print(f"  示例值: {list(df[col_name].head(10))}")
        print(f"  值类型: {[type(x).__name__ for x in df[col_name].head(5)]}")

        # 尝试各种匹配方式
        direct_match = df[df[col_name].isin(target_stkcds)]
        print(f"  直接匹配: {len(direct_match)} 条")

        # 转为 int 试试
        try:
            df_int = df[col_name].astype(int)
            int_match = df[df_int.isin(target_stkcds)]
            print(f"  转 int 匹配: {len(int_match)} 条")
        except Exception as e:
            print(f"  转 int 失败: {e}")

        # 转为 str 试试
        df_str = df[col_name].astype(str)
        target_str = set(str(x) for x in target_stkcds)
        str_match = df[df_str.isin(target_str)]
        print(f"  转 str 匹配: {len(str_match)} 条")

        # 看看大表中有没有包含目标值的行（模糊查找）
        for t in sorted(target_stkcds)[:3]:
            found = df[df[col_name].astype(str).str.contains(str(t))]
            if len(found) > 0:
                print(f"  包含 '{t}' 的行: {len(found)}, 实际值: {list(found[col_name].head(3))}")


if __name__ == "__main__":
    main()
