import csv
import os
import sys
import time
from argparse import ArgumentParser
from multiprocessing import Process, Manager, cpu_count
from pygit2 import Repository, GIT_SORT_REVERSE, GIT_SORT_TOPOLOGICAL
from tqdm import tqdm



# 全局后缀变量
suffix_num = "1" 
suffix_repo = "z3" 
suffix_branch = "master"
suffix_file = "z3_data"

MANAGER = Manager()
RES = MANAGER.dict()

def load_commit_hashes_from_csv(csv_file_path):
    """
    从CSV文件中加载commit_hash列。
    """
    commit_hashes = set()  # 使用set避免重复
    with open(csv_file_path, 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            commit_hashes.add(row['commit_hash'])  # 假设列名为'commit_hash'
    return commit_hashes

def format_author_date(author_time, author_offset):
    """
    格式化author_date为类似 'Tue Sep 2 20:13:38 2008 +0000' 的格式。
    """
    formatted_time = time.strftime("%a %b %d %H:%M:%S %Y", time.gmtime(author_time))
    hours_offset = author_offset // 60
    timezone_offset = f"{hours_offset:+03d}00"  # 格式化为 +0000 或 -0000 的格式
    return f"{formatted_time} {timezone_offset}"

def classify_commit_message(commit_message):
    """
    根据commit_message中的关键词对提交进行分类。
    """
    message = commit_message.lower()
    
    if any(keyword in message for keyword in ["fix", "bug", "defect", "correct"]):
        return "Corrective"
    elif any(keyword in message for keyword in ["add", "feature", "improvement", "introduce"]):
        return "Feature Addition"
    elif any(keyword in message for keyword in ["improve", "enhance", "refactor", "optimize"]):
        return "Perfective"
    elif any(keyword in message for keyword in ["prevent", "avoid", "secure"]):
        return "Preventative"
    elif any(keyword in message for keyword in ["non functional", "documentation", "doc", "comment"]):
        return "Non Functional"
    else:
        return "None"

def parse_code_churns(pid, repo_path, branch, commit_hashes):
    """
    计算指定提交的代码变更，并存储在RES字典中。
    """
    repo = Repository(repo_path)
    head = repo.references.get(branch)
    commits = list(repo.walk(head.target, GIT_SORT_TOPOLOGICAL | GIT_SORT_REVERSE))

    # 只处理 commit_hashes 中指定的提交
    commits = [commit for commit in commits if str(commit.id) in commit_hashes]

    code_churns = [[] for _ in range(len(commits))]
    for i, commit in enumerate(tqdm(commits, position=pid)):
        if commit.parents:
            diff = repo.diff(commit.parents[0], commit)
        else:
            diff = repo.diff(None, commit)

        patches = [p for p in diff]
        stats = diff.stats

        # 统计变更行数
        cloc = stats.insertions  # 增加的代码行数
        dloc = stats.deletions  # 删除的代码行数
        files_churned = len(patches)  # 修改的文件数量

        parent_hashes = ','.join([str(p.id) for p in commit.parents])  # 父提交哈希

        # 提取提交者信息
        author = commit.author
        author_name = author.name
        author_email = author.email
        author_date = format_author_date(author.time, author.offset)  # 格式化 author_date
        author_date_unix_timestamp = str(author.time)  # 提取Unix时间戳
        commit_message = commit.message.strip()

        # 基于commit_message进行分类
        classification = classify_commit_message(commit_message)

        # 存储扩展后的特pytorch
        code_churns[i].append(f"{suffix_repo}")                           # project: 固定为 z3
        code_churns[i].append(parent_hashes)                  # parent_hashes
        code_churns[i].append(str(commit.id))                 # commit_hash
        code_churns[i].append(author_name)                    # author_name
        code_churns[i].append(author_email)                   # author_email
        code_churns[i].append(author_date)                    # author_date
        code_churns[i].append(author_date_unix_timestamp)     # author_date_unix_timestamp
        code_churns[i].append(commit_message)                 # commit_message
        code_churns[i].append(str(cloc))                      # la: 代码增加行数
        code_churns[i].append(str(dloc))                      # ld: 代码删除行数
        code_churns[i].append(str(files_churned))             # nf: 变更的文件数
        code_churns[i].append(classification)                 # classification: 提交的分类

    RES[pid] = code_churns

def get_code_churns(repo_path, branch, commit_hashes):
    """
    提取指定提交的代码变更信息。
    """
    cpus =  cpu_count() 
    print(f"Using {cpus} CPUs...")

    # 将提交列表分为多份，以便并行处理
    commit_list = list(commit_hashes)
    quotes, remainder = divmod(len(commit_list), cpus)

    processes = [
        Process(target=parse_code_churns, args=(i, repo_path, branch, set(commit_list[i * quotes + min(i, remainder): (i + 1) * quotes + min(i + 1, remainder)])))
        for i in range(cpus)
    ]

    for process in processes:
        process.start()

    start_time = time.time()
    for process in processes:
        process.join()
    end_time = time.time()

    print("Done")
    print(f"Overall processing time: {end_time - start_time} seconds")

    churns = []
    for _, churn in RES.items():
        churns.extend(churn)

    churns = list(reversed(churns))
    return churns

def save_churns(churns, path=f"./{suffix_file}/code_churns{suffix_num}.csv"):
    """
    将结果保存为CSV文件。
    """
    with open(path, 'w') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow([
            "project", "parent_hashes", "commit_hash", "author_name", "author_email",
            "author_date", "author_date_unix_timestamp", "commit_message", "la", "ld", "nf", "classification"
        ])

        for row in churns:
            if row:
                writer.writerow(row)

if __name__ == "__main__":
    PARSER = ArgumentParser(description="从指定仓库和CSV文件中的提交中提取代码变更。")
    PARSER.add_argument("--repository", "-r", type=str, default=f"/home/WangZiyang/szz/{suffix_repo}", help="本地Git仓库的路径")
    PARSER.add_argument("--branch", "-b", type=str, default=f"refs/heads/{suffix_branch}", help="要分析的分支")
    PARSER.add_argument("--csv_file", "-c", type=str, default=f"./{suffix_file}/commit_id{suffix_num}.csv", help="包含提交哈希的CSV文件路径")

    ARGS = PARSER.parse_args()
    REPOPATH = ARGS.repository
    BRANCH = ARGS.branch
    CSV_FILE_PATH = ARGS.csv_file

    if not os.path.exists(REPOPATH):
        print("仓库路径不存在!")
        sys.exit(1)

    if not os.path.exists(CSV_FILE_PATH):
        print("CSV文件不存在!")
        sys.exit(1)

    # 从CSV文件中加载commit_hash列
    commit_hashes = load_commit_hashes_from_csv(CSV_FILE_PATH)

    # 获取代码变更信息
    churns = get_code_churns(REPOPATH, BRANCH, commit_hashes)

    # 保存变更数据
    save_churns(churns)

