import pandas as pd

suffix_num = "1" 
suffix_repo = "z3" 
suffix_branch = "master"
suffix_file = "z3_data"

# 读取 all_id.csv 和 commit_id1.csv
all_id_df = pd.read_csv(f'./{suffix_file}/all_id.csv')
commit_id1_df = pd.read_csv(f'./{suffix_file}/commit_id1.csv')

# 查找 all_id.csv 中不在 commit_id1.csv 中的 commit_hash
# 使用 set 来比较两个文件中的 commit_hash 列
commit_id1_hashes = set(commit_id1_df['commit_hash'])
missing_commit_hashes = all_id_df[~all_id_df['commit_hash'].isin(commit_id1_hashes)]

# 将结果保存到 commit_id0.csv 中
missing_commit_hashes.to_csv(f'./{suffix_file}/commit_id0.csv', index=False)

print(f"Missing commit_hashes saved to commit_id0.csv")
