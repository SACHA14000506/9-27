import csv
import json
import sys
import time
import pygit2
import pandas as pd
from argparse import ArgumentParser
from datetime import datetime
from numpy import floor
from pygit2 import Repository, GIT_SORT_TOPOLOGICAL, GIT_SORT_REVERSE
from tqdm import tqdm

# 全局后缀变量
suffix_num = "0" 
suffix_repo = "pytorch" 
suffix_branch = "main"

def set_to_list(obj):
    if isinstance(obj, set):
        return list(obj)
    if isinstance(obj, float):
        return str('%.15g' % obj)
    if isinstance(obj, bytes):
        return obj.decode('utf-8', errors='ignore')
    if isinstance(obj, tuple):
        return list(obj)
    if isinstance(obj, pygit2.Oid):
        return str(obj)
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

def get_files_in_tree(tree, repo):
    files = set()
    for entry in tree:
        if entry.type == "blob":
            blob = repo[entry.id]
            if not blob.is_binary:
                if entry.name.endswith("java"):
                    files.add((str(entry.id), entry.name))
        elif entry.type == "tree":
            sub_tree = repo[entry.id]
            sub_files = get_files_in_tree(repo[sub_tree], repo)
            files.update(sub_files)
    return files

def get_diffing_files(commit, parent, repo):
    diff = repo.diff(parent, commit)
    patches = [p for p in diff]
    files = set()
    for patch in patches:
        if patch.delta.is_binary:
            continue
        nfile = patch.delta.new_file
        files.add((str(nfile.id), nfile.path, patch.delta.status))
    return files

def save_experience_features_graph(repo_path, branch, graph_path):
    repo = Repository(repo_path)
    head = repo.references.get(branch)
    commits = list(repo.walk(head.target, GIT_SORT_TOPOLOGICAL | GIT_SORT_REVERSE))
    current_commit = repo.head.target

    start_time = time.time()
    current_commit = repo.get(str(current_commit))
    files = get_files_in_tree(current_commit.tree, repo)

    all_authors = {}
    author = current_commit.committer.name
    all_authors[author] = {}
    all_authors[author]['lastcommit'] = str(current_commit.id)
    all_authors[author][str(current_commit.id)] = {}
    all_authors[author][str(current_commit.id)]['prevcommit'] = ""
    all_authors[author][str(current_commit.id)]["exp"] = 1
    all_authors[author][str(current_commit.id)]["rexp"] = [[len(files), 1]]
    all_authors[author][str(current_commit.id)]["sexp"] = {}

    for i, commit in enumerate(tqdm(commits[1:])):
        files = get_diffing_files(commit, commits[i], repo)
        author = commit.committer.name
        commit_id_str = str(commit.id)

        if author not in all_authors:
            all_authors[author] = {}
            all_authors[author]['lastcommit'] = commit_id_str
            all_authors[author][commit_id_str] = {}
            all_authors[author][commit_id_str]['prevcommit'] = ""
            all_authors[author][commit_id_str]["exp"] = 1
            all_authors[author][commit_id_str]["rexp"] = [[len(files), 1.0]]
            all_authors[author][commit_id_str]["sexp"] = {}
        else:
            last_commit = str(all_authors[author]["lastcommit"])
            all_authors[author]["lastcommit"] = commit_id_str
            all_authors[author][commit_id_str] = {}
            all_authors[author][commit_id_str]['prevcommit'] = last_commit
            all_authors[author][commit_id_str]['exp'] = 1 + all_authors[author][last_commit]['exp']

            date_current = datetime.fromtimestamp(commit.commit_time)
            date_last = datetime.fromtimestamp(repo.get(last_commit).commit_time)
            diffing_years = abs(floor(float((date_current - date_last).days) / 365))

            overall = all_authors[author][last_commit]['rexp']
            all_authors[author][commit_id_str]['rexp'] = [[len(files), 1.0]] + [[e[0], e[1] + diffing_years] for e in overall]

    with open(graph_path, 'w') as output:
        json.dump(all_authors, output, default=set_to_list)

    end_time = time.time()
    print("Done")
    print(f"Overall processing time {end_time - start_time}")

def load_experience_features_graph(path="./results/author_graph.json"):
    file_graph = {}
    with open(path, 'r') as inp:
        file_graph = json.load(inp, parse_float=lambda x: float(x))
    return file_graph

def get_commit_hashes(csv_path):
    df = pd.read_csv(csv_path)
    commit_hashes = df['commit_hash'].tolist()
    return commit_hashes

def get_experience_features_for_commit_hashes(graph, repo_path, commit_hashes):
    repo = Repository(repo_path)
    features = []

    for commit_hash in commit_hashes:
        try:
            commit = repo.get(commit_hash)
            author = commit.committer.name
            commit_id_str = str(commit.id)

            exp = graph[author][commit_id_str]['exp']
            rexp = graph[author][commit_id_str]['rexp']
            rrexp = sum([float(float(e[0]) / (float(e[1]) + 1)) for e in rexp])

            commit_feat = [commit_id_str, str(float(exp)), str(float(rrexp)), str(float(0))]
            features.append(commit_feat)
        except KeyError:
            print(f"Commit {commit_hash} not found in the graph.")
    
    return features

def save_experience_features(history_features, path):
    with open(path, 'w') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["commit_hash", "exp", "rexp", "sexp"])
        for row in history_features:
            if row:
                writer.writerow([row[0], row[1], row[2], row[3]])

if __name__ == "__main__":
    PARSER = ArgumentParser(description="Utility to extract code churns from a repository or a single commit.")

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
        help="Which branch to use."
    )
    PARSER.add_argument(
        "--save-graph",
        "-sg",
        action="store_true",
        help="Generate a new graph for a repository."
    )
    PARSER.add_argument(
        "--graph-path",
        "-gp",
        type=str,
        default="./results/author_graph.json",
        help="The path to where the graph is stored."
    )
    PARSER.add_argument(
        "--output",
        "-o",
        type=str,
        default=f"./results/exp{suffix_num}.csv",
        help="The path where the output is written."
    )
    PARSER.add_argument(
        "--commit-id-csv",
        "-c",
        type=str,
        default=f"./commit_id{suffix_num}.csv",
        help="Path to the commit_id.csv file."
    )

    ARGS = PARSER.parse_args()
    REPO_PATH = ARGS.repository
    BRANCH = ARGS.branch
    SAVE_GRAPH = ARGS.save_graph
    GRAPH_PATH = ARGS.graph_path
    OUTPUT = ARGS.output
    COMMIT_ID_CSV_PATH = ARGS.commit_id_csv

    if SAVE_GRAPH:
        save_experience_features_graph(REPO_PATH, BRANCH, GRAPH_PATH)
    
    GRAPH = load_experience_features_graph(GRAPH_PATH)
    COMMIT_HASHES = get_commit_hashes(COMMIT_ID_CSV_PATH)
    EXPERIENCE_FEATURES = get_experience_features_for_commit_hashes(GRAPH, REPO_PATH, COMMIT_HASHES)
    save_experience_features(EXPERIENCE_FEATURES, OUTPUT)

