import pandas as pd

# 全局后缀变量
suffix_num = "0" 
suffix_repo = "pytorch" 
suffix_branch = "main"
suffix_file = "pytorch_data"

files = [f"code_churns{suffix_num}.csv", f"diffusion_features{suffix_num}.csv", f"exp{suffix_num}.csv", f"fix_features{suffix_num}.csv", f"history{suffix_num}.csv", f"lt{suffix_num}.csv"]

duplicate_counts = {}

for file in files:
    df = pd.read_csv(file, low_memory=False)
    
    duplicates = df.duplicated(subset='commit_hash', keep=False)

    duplicate_count = duplicates.sum()
    duplicate_counts[file] = duplicate_count

for file, count in duplicate_counts.items():
    print(f"File {file} has {count} duplicate rows based on 'commit_hash'.")
