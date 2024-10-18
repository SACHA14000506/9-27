import pandas as pd

# 全局后缀变量
suffix_num = "1" 
suffix_repo = "z3" 
suffix_branch = "master"
suffix_file = "z3_data"

# 定义列的顺序
columns_order = [
    'project', 'parent_hashes', 'commit_hash', 'author_name', 'author_email', 
    'author_date', 'author_date_unix_timestamp', 'commit_message', 'la', 'ld', 
    'fileschanged', 'nf', 'ns', 'nd', 'entropy', 'ndev', 'lt', 'nuc', 'age', 
    'exp', 'rexp', 'sexp', 'classification', 'fix', 'is_buggy_commit'
]

# 文件列表
files = [f"./{suffix_file}/code_churns{suffix_num}.csv", f"./{suffix_file}/diffusion_features{suffix_num}.csv", f"./{suffix_file}/exp{suffix_num}.csv", f"./{suffix_file}/fix_features{suffix_num}.csv", f"./{suffix_file}/history{suffix_num}.csv", f"./{suffix_file}/lt{suffix_num}.csv"]

# 用于存储每个文件的 DataFrame 列表
df_list = []

# 遍历每个文件，删除重复的 commit_hash，并存储处理后的 DataFrame
for file in files:
    df = pd.read_csv(file, low_memory=False)
    
    # 删除同一文件中重复的 commit_hash 行，保留首次出现的
    df = df.drop_duplicates(subset='commit_hash', keep='first')
    
    # 将处理后的 DataFrame 添加到列表中
    df_list.append(df)

# 逐步合并所有文件，基于 commit_hash 列
merged_df = df_list[0]
for df in df_list[1:]:
    merged_df = pd.merge(merged_df, df, on='commit_hash', how='outer')

# 添加 'is_buggy_commit' 列，默认值为 1
merged_df['is_buggy_commit'] = 1

# 按照指定的列顺序排列列
available_columns = [col for col in columns_order if col in merged_df.columns]
merged_df = merged_df[available_columns]

# 删除合并后的空值行，但排除 'classification' 列，不将 'None' 作为空值处理
cols_to_check = [col for col in available_columns if col != 'classification']
merged_df = merged_df.dropna(subset=cols_to_check)

# 保存合并后的数据为新的 CSV 文件
output_file = f"/home/WangZiyang/szz/{suffix_file}/merged_data{suffix_num}.csv"
merged_df.to_csv(output_file, index=False)

print(f"Merged CSV saved as {output_file}")
