"""
探查各 Excel 文件的列名，验证用户指定的列位置是否正确。
使用 nrows=0 只读取列头，不加载数据行。
"""

import pandas as pd
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(BASE_DIR, "raw_data")


def col_letter_to_index(letter: str) -> int:
    """将 Excel 列字母（如 'AA', 'CC'）转为 0-based 索引"""
    result = 0
    for c in letter.upper():
        result = result * 26 + (ord(c) - ord("A") + 1)
    return result - 1


# 用户指定的各表列位置
TARGET_COLUMNS = {
    "盈利能力.xlsx": {"ROE": "AA"},
    "发展能力.xlsx": {"净利润增长率": "Z", "营业收入增长率": "AI"},
    "偿债能力.xlsx": {"资产负债率": "U"},
    "资产负债表.xlsx": {"总资产": "CC"},
    "利润表.xlsx": {"研发投入": "AO"},
    "tobinq.xlsx": {"tobinq值": "AB"},
}


def main():
    for fname, col_map in TARGET_COLUMNS.items():
        filepath = os.path.join(RAW_DIR, fname)
        print(f"\n{'='*60}")
        print(f"文件: {fname}")

        if not os.path.exists(filepath):
            print("  ❌ 文件不存在!")
            continue

        # 只读列头
        df = pd.read_excel(filepath, nrows=0)
        cols = list(df.columns)
        print(f"  总列数: {len(cols)}")
        print(f"  前5列: {cols[:5]}")

        # 查找 Stkcd 列
        for i, c in enumerate(cols):
            if c and "stkcd" in str(c).lower():
                print(f"  Stkcd 列: index={i}, 列名='{c}'")
                break

        # 验证目标列
        for desc, letter in col_map.items():
            idx = col_letter_to_index(letter)
            if idx < len(cols):
                actual = cols[idx]
                match = "✅" if desc.lower() in str(actual).lower() else "⚠️"
                print(f"  {match} {letter}列(index={idx}): '{actual}'  ← 期望: {desc}")
            else:
                print(f"  ❌ {letter}列(index={idx}): 超出范围! 总列数={len(cols)}")

    # 同时打印 filtered_tobinq 的信息
    print(f"\n{'='*60}")
    print("文件: filtered_tobinq.xlsx")
    ft = pd.read_excel(os.path.join(RAW_DIR, "filtered_tobinq.xlsx"))
    print(f"  公司数: {len(ft)}")
    print(f"  列: {list(ft.columns)}")
    print(f"  Stkcd 示例: {list(ft['Stkcd'].head())}")


if __name__ == "__main__":
    main()
