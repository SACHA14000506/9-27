import csv
import os
import sys
import time

from argparse import ArgumentParser
from multiprocessing import Process, Manager, cpu_count
from pygit2 import Repository, GIT_SORT_REVERSE, GIT_SORT_TOPOLOGICAL
from tqdm import tqdm

# 全局后缀变量
suffix_repo = "pytorch" 
suffix_branch = "main"
MANAGER = Manager()
RES = MANAGER.dict()

# Global variables
MANAGER = Manager()
RES = MANAGER.dict()

def extract_commit_hashes(pid, repo_path, branch, batch_start, batch_end):
    """
    Function that extracts commit hashes for a set of commits
    and stores them in the RES dict.
    """
    repo = Repository(repo_path)
    head = repo.references.get(branch)
    commits = list(repo.walk(head.target, GIT_SORT_TOPOLOGICAL | GIT_SORT_REVERSE))

    commits = commits[batch_start:batch_end]

    commit_hashes = [str(commit.id) for commit in commits]
    RES[pid] = commit_hashes

def get_all_commit_hashes(repo_path, branch):
    """
    General function for extracting commit hashes. It uses multiprocessing
    to speed up the process.
    """
    repo = Repository(repo_path)
    head = repo.references.get(branch)
    commits = list(repo.walk(head.target, GIT_SORT_TOPOLOGICAL | GIT_SORT_REVERSE))

    # Check how many processes that could be spawned
    cpus = cpu_count()
    print(f"Using {cpus} CPUs...")

    # Equally split the commit set into equally sized parts.
    quote, remainder = divmod(len(commits), cpus)

    processes = [
        Process(
            target=extract_commit_hashes,
            args=(i, repo_path, branch, i * quote + min(i, remainder),
                  (i + 1) * quote + min(i + 1, remainder))) for i in range(cpus)
    ]

    for process in processes:
        process.start()

    start_time = time.time()
    for process in processes:
        process.join()
    end_time = time.time()

    print("Done")
    print(f"Overall processing time {end_time - start_time} seconds.")

    # Assemble the results
    all_commit_hashes = []
    for _, commit_hashes in RES.items():
        all_commit_hashes.extend(commit_hashes)

    return all_commit_hashes

def save_commit_hashes(commit_hashes, path="all_id.csv"):
    """
    Saves the commit hashes to a CSV file.
    """
    with open(path, 'w') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["commit_hash"])

        for commit_hash in commit_hashes:
            writer.writerow([commit_hash])

if __name__ == "__main__":
    PARSER = ArgumentParser(description="Utility to extract commit hashes from a repository.")

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

    ARGS = PARSER.parse_args()
    REPOPATH = ARGS.repository
    BRANCH = ARGS.branch

    if not os.path.exists(REPOPATH):
        print("The repository path does not exist!")
        sys.exit(1)

    # 获取所有 commit_hash
    all_commit_hashes = get_all_commit_hashes(REPOPATH, BRANCH)

    # 保存所有 commit_hash 到 CSV
    save_commit_hashes(all_commit_hashes)

    print(f"All commit hashes saved to all_id.csv.")
