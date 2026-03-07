"""
从各 CSMAR Excel 数据表中提取指定列，
按 filtered_tobinq.xlsx 中的公司列表匹配后合并输出为一个 CSV 文件。

使用 usecols 参数只读取必要列，避免加载整个大文件。
"""

import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(BASE_DIR, "raw_data")
OUTPUT_PATH = os.path.join(BASE_DIR, "raw_data", "merged_data.csv")


def col_letter_to_index(letter: str) -> int:
    """将 Excel 列字母转为 0-based 索引"""
    result = 0
    for c in letter.upper():
        result = result * 26 + (ord(c) - ord("A") + 1)
    return result - 1


# 各表的提取配置:
# key: 文件名
# value: list of (Excel列字母, 输出列名)
# 公共列 Stkcd(A), Accper(C) 会自动包含用于匹配
EXTRACT_CONFIG = {
    "盈利能力.xlsx": [
        ("AA", "ROE"),
    ],
    "发展能力.xlsx": [
        ("Z", "净利润增长率"),
        ("AI", "营业收入增长率"),
    ],
    "偿债能力.xlsx": [
        ("U", "资产负债率"),
    ],
    "资产负债表.xlsx": [
        ("CC", "总资产"),
    ],
    "利润表.xlsx": [
        ("AO", "研发投入"),
    ],
    "tobinq.xlsx": [
        ("AB", "TobinQ"),
    ],
}

# 公共列索引: Stkcd=A(0), Accper=C(2), Typrep=D(3)
COMMON_COL_INDICES = [0, 2]  # Stkcd, Accper
TYPREP_COL_INDEX = 3         # 报表类型列

# tobinq 表没有 Typrep 列，需单独处理
NO_TYPREP_FILES = {"tobinq.xlsx"}


def extract_from_file(
    filename: str,
    columns: list[tuple[str, str]],
    target_stkcds: set,
) -> pd.DataFrame:
    """从单个 Excel 文件中提取指定列，仅保留目标公司的合并报表数据"""
    filepath = os.path.join(RAW_DIR, filename)

    # 构建 usecols: 公共列 + 目标列（+ Typrep 列，如有）
    target_indices = [col_letter_to_index(letter) for letter, _ in columns]
    has_typrep = filename not in NO_TYPREP_FILES
    usecols = COMMON_COL_INDICES + ([TYPREP_COL_INDEX] if has_typrep else []) + target_indices

    print(f"  读取 {filename} (usecols={usecols})...")
    # skiprows=[1,2]: 跳过第2、3行（中文字段描述和单位说明）
    df = pd.read_excel(filepath, usecols=usecols, skiprows=[1, 2])

    # 只保留合并报表（Typrep='A'），然后删掉 Typrep 列
    if has_typrep:
        typrep_col = df.columns[2]  # Typrep 在 Stkcd, Accper 之后
        df = df[df[typrep_col] == "A"].copy()
        df = df.drop(columns=[typrep_col])

    # 标准化列名: 目标列重命名为用户指定的中文名
    original_cols = list(df.columns)
    rename_map = {}
    for i, (letter, new_name) in enumerate(columns):
        old_name = original_cols[len(COMMON_COL_INDICES) + i]
        rename_map[old_name] = new_name
    df = df.rename(columns=rename_map)

    # Stkcd 统一转为整数（大表中是零填充字符串如 "000938"）
    df["Stkcd"] = pd.to_numeric(df["Stkcd"], errors="coerce").astype("Int64")

    # 筛选目标公司
    df = df[df["Stkcd"].isin(target_stkcds)].copy()
    print(f"  → 提取 {len(df)} 条记录")

    return df


def main():
    # 1. 读取目标公司列表
    print("读取目标公司列表...")
    ft = pd.read_excel(os.path.join(RAW_DIR, "filtered_tobinq.xlsx"))
    target_stkcds = set(ft["Stkcd"].values)
    print(f"目标公司: {len(target_stkcds)} 家")
    print(f"Stkcd: {sorted(target_stkcds)}\n")

    # 2. 逐个表提取数据
    merged = None
    for filename, columns in EXTRACT_CONFIG.items():
        print(f"处理 {filename}...")
        df = extract_from_file(filename, columns, target_stkcds)

        if merged is None:
            merged = df
        else:
            # 按 Stkcd + Accper 合并
            merged = merged.merge(df, on=["Stkcd", "Accper"], how="outer")

    # 3. 关联公司简称
    merged = merged.merge(
        ft[["Stkcd", "ShortName"]], on="Stkcd", how="left"
    )

    # 4. 整理列顺序
    col_order = ["Stkcd", "ShortName", "Accper"]
    data_cols = ["ROE", "净利润增长率", "营业收入增长率", "资产负债率", "总资产", "研发投入", "TobinQ"]
    col_order += [c for c in data_cols if c in merged.columns]
    merged = merged[col_order]

    # 按公司代码和日期排序
    merged = merged.sort_values(["Stkcd", "Accper"]).reset_index(drop=True)

    # 5. 输出
    merged.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")
    print(f"\n✅ 合并完成!")
    print(f"   输出文件: {OUTPUT_PATH}")
    print(f"   总行数: {len(merged)}")
    print(f"   列: {list(merged.columns)}")
    print(f"\n前10行预览:")
    print(merged.head(10).to_string())


if __name__ == "__main__":
    main()
