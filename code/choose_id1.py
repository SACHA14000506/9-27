import json
import pandas as pd

suffix_num = "1" 
suffix_repo = "z3" 
suffix_branch = "master"
suffix_file = "z3_data"

# 假设 json 文件的路径
json_file = f'./{suffix_file}/fix_and_introducers_pairs.json'

# 读取 json 文件
with open(json_file, 'r') as file:
    data = json.load(file)

# 查找并删除重复项
unique_data = []
seen = set()
duplicate_count = 0

# 假设 json 数据是一个列表，其中每个项也是一个列表
for item in data:
    data_pair = tuple(item)  # 将每个列表转换为元组
    if data_pair not in seen:
        unique_data.append(item)
        seen.add(data_pair)
    else:
        duplicate_count += 1

# 保存唯一的数据对到 CSV 文件 '不同数据对.csv' 中
df_unique = pd.DataFrame(unique_data, columns=['commit_hash_1', 'commit_hash_2'])
df_unique.to_csv('不同数据对.csv', index=False)

# 提取每个数据对的第二个数据，保存到 'commit_id1.csv' 的 commit_hash 列中
commit_df = df_unique[['commit_hash_2']].copy()
commit_df.columns = ['commit_hash']  # 重命名列
commit_df.to_csv(f'./{suffix_file}/commit_id1.csv', index=False)

# 输出重复的数量
print(f"Number of duplicate data pairs removed: {duplicate_count}")

