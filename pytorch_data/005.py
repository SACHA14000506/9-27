import csv
import re
from argparse import ArgumentParser
from tqdm import tqdm
from pygit2 import Repository, GIT_SORT_TOPOLOGICAL, GIT_SORT_REVERSE

# 全局后缀变量
suffix_num = "0" 
suffix_repo = "pytorch" 
suffix_branch = "main"

# Patterns to search for in commit messages to identify "fix" commits
PATTERNS = [r"bug", r"fix", r"defect", r"patch"]

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

def is_fix(message):
    """
    Check if a message contains any of the fix patterns.
    """
    for pattern in PATTERNS:
        if re.search(pattern, message, re.IGNORECASE):  # 忽略大小写
            return True
    return False

def get_purpose_features(repo_path, branch, commit_hashes):
    """
    Extract the purpose features for each commit, but only process commits
    that are listed in commit_hashes.
    """
    repo = Repository(repo_path)
    head = repo.references.get(branch)

    # 获取所有提交
    commits = list(repo.walk(head.target, GIT_SORT_TOPOLOGICAL | GIT_SORT_REVERSE))

    features = []
    for _, commit in enumerate(tqdm(commits)):
        # 只处理在 commit_hashes 中指定的提交
        if str(commit.id) in commit_hashes:  # 修改为 commit.id
            message = commit.message

            # 检查提交信息中是否有修复相关的关键词
            fix = 1.0 if is_fix(message) else 0.0

            feat = [str(commit.id), str(fix)]
            features.append(feat)
    return features

def save_features(purpose_features, path=f"./fix_features{suffix_num}.csv"):
    """
    Save the purpose features to a csv file.
    """
    with open(path, 'w') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["commit_hash", "fix"])
        for row in purpose_features:
            if row:
                writer.writerow([row[0], row[1]])

if __name__ == "__main__":
    PARSER = ArgumentParser(
        description="Utility to extract fix features from a repository " +
                    "or a single commit.")

    PARSER.add_argument(
        "--repository",
        "-r",
        type=str,
        default=f"/home/WangZiyang/szz/{suffix_repo}",
        help="Path to local git repository.")
    PARSER.add_argument(
        "--branch",
        "-b",
        type=str,
        default=f"refs/heads/{suffix_branch}",
        help="Which branch to use.")
    PARSER.add_argument(
        "--csv_file", "-c",
        type=str,
        default=f"./commit_id{suffix_num}.csv",
        help="Path to CSV file containing commit hashes.")

    ARGS = PARSER.parse_args()
    REPOPATH = ARGS.repository
    BRANCH = ARGS.branch
    CSV_FILE_PATH = ARGS.csv_file

    if not CSV_FILE_PATH or not REPOPATH:
        print("Please specify a valid repository and CSV file path.")
        sys.exit(1)

    # 从CSV文件中加载commit_hash列
    commit_hashes = load_commit_hashes_from_csv(CSV_FILE_PATH)

    # 获取提交的特征信息
    FEATURES = get_purpose_features(REPOPATH, BRANCH, commit_hashes)

    # 保存特征信息
    save_features(FEATURES)

