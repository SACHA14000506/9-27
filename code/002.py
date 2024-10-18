import csv
import os
import sys
import time
import pandas as pd

from argparse import ArgumentParser
from multiprocessing import Process, Manager, cpu_count
from numpy import log2
from pygit2 import Repository, GIT_SORT_TOPOLOGICAL, GIT_SORT_REVERSE
from tqdm import tqdm

# 全局后缀变量
suffix_num = "1" 
suffix_repo = "z3" 
suffix_branch = "master"
suffix_file = "z3_data" 

# 初始化多进程管理器
MANAGER = Manager()
RES = MANAGER.dict()

def count_diffing_subsystems(subsystems):
    """
    计算提交中变更的子系统数量。
    """
    number = 0
    for system in subsystems.values():
        number += count_diffing_subsystems(system)
    return number + len(subsystems.keys())

def count_entropy(file_changes, total_change):
    """
    计算文件修改的熵。
    """
    if total_change == 0:
        return 0
    return sum([
        -1 * (float(x) / total_change) * (log2(float(x) / total_change) if x > 0 else 0)
        for x in file_changes
    ])

def parse_diffusion_features(pid, repo_path, branch, commit_hashes):
    """
    提取每个提交的扩散特征：ns、nd、entropy和fileschanged。
    """
    repo = Repository(repo_path)
    head = repo.references.get(branch)
    commits = list(repo.walk(head.target, GIT_SORT_TOPOLOGICAL | GIT_SORT_REVERSE))
    
    features = []
    
    for commit in tqdm(commits, position=pid):
        if str(commit.id) not in commit_hashes:
            continue  # 如果当前提交不在CSV中的commit_hash里，跳过

        diff = repo.diff(commit.parents[0], commit) if commit.parents else repo.diff(None, commit)

        patches = [p for p in diff]
        
        # 初始化特征值
        fileschanged = []  # 修改的文件路径
        modules = set([])  # 修改的模块
        subsystems_mapping = {}  # 存储子系统层次结构
        entropy_change = 0  # 熵
        file_changes = []  # 每个文件的修改行数
        total_change = 0  # 总行数变化

        for patch in patches:
            if patch.delta.is_binary:
                continue  # 跳过二进制文件
            _, addition, deletions = patch.line_stats
            total_change += (addition + deletions)
            file_changes.append(addition + deletions)

            # 获取被修改的文件路径
            fpath = patch.delta.new_file.path
            fileschanged.append(fpath)

            # 解析文件所属的子系统（路径的子目录）
            subsystems = fpath.split('/')[:-1]
            root = subsystems_mapping
            for system in subsystems:
                if system not in root:
                    root[system] = {}
                root = root[system]
            if subsystems:
                modules.add(subsystems[0])  # 添加第一级目录作为模块
        
        # 计算变更的子系统数量 ns
        modified_systems = count_diffing_subsystems(subsystems_mapping)

        # 计算变更的模块数量 nd
        modified_modules = len(modules)

        # 计算熵
        entropy_change = count_entropy(file_changes, total_change)

        # 添加到特征列表中
        features.append([
            str(commit.id),              # commit id
            str(float(modified_systems)), # ns：变更子系统数量
            str(float(modified_modules)), # nd：变更模块数量
            str(float(entropy_change)),   # 熵
            ','.join(fileschanged)        # fileschanged：修改的文件路径
        ])

    RES[pid] = features

def get_diffusion_features(repo_path, branch, csv_file=f'./{suffix_file}/commit_id{suffix_num}.csv'):
    """
    从 CSV 文件获取 commit_hash，并提取扩散特征。
    """
    repo = Repository(repo_path)

    # 读取CSV文件，并提取commit_hash列
    df = pd.read_csv(csv_file)
    commit_hashes = set(df['commit_hash'].tolist())  # 从csv中提取commit_hash

    # 获取提交并并行处理
    cpus = cpu_count()
    print(f"Using {cpus} CPUs...")
    
    processes = []
    quote, remainder = divmod(len(commit_hashes), cpus)
    
    # 多进程处理提交
    for i in range(cpus):
        start = i * quote + min(i, remainder)
        end = (i + 1) * quote + min(i + 1, remainder)
        commit_batch = list(commit_hashes)[start:end]
        
        process = Process(
            target=parse_diffusion_features,
            args=(i, repo_path, branch, commit_batch)
        )
        processes.append(process)
        process.start()

    start_time = time.time()

    for process in processes:
        process.join()

    end_time = time.time()
    print(f"Overall processing time: {end_time - start_time}")

    # 汇总各进程的结果
    features = []
    for _, feat in RES.items():
        features.extend(feat)

    return features

def save_diffusion_features(diffusion_features, path=f"./{suffix_file}/diffusion_features{suffix_num}.csv"):
    """
    将扩散特征保存到CSV文件。
    """
    with open(path, 'w') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow([
            "commit_hash", "ns", "nd", "entropy", "fileschanged"
        ])
        for row in diffusion_features:
            writer.writerow(row)

if __name__ == "__main__":
    PARSER = ArgumentParser(
        description="Utility to extract diffusion features from a repository based on commit_hash from a CSV file."
    )

    PARSER.add_argument(
        "--repository",
        "-r",
        type=str,
        default=f"/home/WangZiyang/szz/{suffix_repo}",
        help="Path to local git repository."
    )
    PARSER.add_argument(
        "--branch",
        "-b",
        type=str,
        default=f"refs/heads/{suffix_branch}",
        help="Branch to use."
    )
    PARSER.add_argument(
        "--csv_file",
        "-c",
        type=str,
        default=f"./{suffix_file}/commit_id{suffix_num}.csv",
        help="Path to the CSV file containing commit_hash column."
    )

    ARGS = PARSER.parse_args()
    REPOPATH = ARGS.repository
    BRANCH = ARGS.branch
    CSV_FILE = ARGS.csv_file  # 获取CSV文件路径
    
    if not os.path.exists(REPOPATH):
        print("The repository path does not exist!")
        sys.exit(1)

    DIFFUSION_FEATURES = get_diffusion_features(REPOPATH, BRANCH, CSV_FILE)
    save_diffusion_features(DIFFUSION_FEATURES)

