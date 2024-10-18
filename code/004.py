import csv
import json
import time
from argparse import ArgumentParser
from pygit2 import Repository, GIT_SORT_TOPOLOGICAL, GIT_SORT_REVERSE
from tqdm import tqdm
import pandas as pd


# 全局后缀变量
suffix_num = "1" 
suffix_repo = "z3" 
suffix_branch = "master"
suffix_file = "z3_data"

def set_to_list(obj):
    """
    Helper function to convert a set to a list for JSON serialization.
    """
    if isinstance(obj, set):
        return list(obj)
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def get_files_in_tree(tree, repo):
    """
    Extract the hex of all files and their name.
    """
    files = set()
    for entry in tree:
        if entry.type == "tree":
            sub_files = [(f[0], "{}/{}".format(entry.name, f[1]))
                         for f in get_files_in_tree(repo[entry.id], repo)]
            files.update(sub_files)
        else:
            blob = repo[entry.id]
            if blob.type == "blob":  # Check if it's a blob (file)
                if entry.name.endswith(".java"):  # Adjust file extension if needed
                    files.add((blob.id, entry.name))
    return files


def get_diffing_files(commit, parent, repo):
    """
    Get the files that diffed between two commits.
    """
    diff = repo.diff(parent, commit)
    patches = [p for p in diff]
    files = set()

    for patch in patches:
        if patch.delta.is_binary:
            continue
        nfile = patch.delta.new_file
        files.add((nfile.id, nfile.path, patch.delta.status))

    return files


def save_history_features_graph(repo_path, branch, graph_path):
    """
    Track the number of developers that have worked in a repository and save the
    results in a graph which could be used for later use.
    """
    repo = Repository(repo_path)
    head = repo.references.get(branch)

    commits = list(repo.walk(head.target, GIT_SORT_TOPOLOGICAL | GIT_SORT_REVERSE))
    current_commit = repo.head.target

    all_files = {}
    current_commit = repo.get(str(current_commit))
    files = get_files_in_tree(current_commit.tree, repo)

    for (_, name) in tqdm(files):
        all_files[name] = {}
        all_files[name]['lastcommit'] = str(current_commit.id)
        all_files[name][str(current_commit.id)] = {}
        all_files[name][str(current_commit.id)]['prevcommit'] = ""
        all_files[name][str(current_commit.id)]['authors'] = [current_commit.committer.name]

    for i, commit in enumerate(tqdm(commits[1:])):
        files = get_diffing_files(commit, commits[i], repo)
        for (_, name, _) in files:
            if name not in all_files:
                all_files[name] = {}

            last_commit = ""
            if 'lastcommit' not in all_files[name]:
                all_files[name]['lastcommit'] = str(commit.id)
            else:
                last_commit = all_files[name]['lastcommit']

            all_files[name][str(commit.id)] = {}
            all_files[name][str(commit.id)]['prevcommit'] = last_commit

            authors = set([commit.committer.name])
            

            if last_commit:
            # 检查 'authors' 键是否存在
                if 'authors' in all_files[name][last_commit]:
                    authors.update(all_files[name][last_commit]['authors'])
                else:
                    all_files[name][last_commit]['authors'] = set()
                    authors.update(all_files[name][last_commit]['authors'])
            all_files[name][str(commit.id)]['authors'] = authors

            all_files[name]['lastcommit'] = str(commit.id)

    with open(graph_path, 'w') as output:
        json.dump(all_files, output, default=set_to_list)


def load_history_features_graph(path):
    """
    Load the history features from a JSON file.
    """
    file_graph = {}
    with open(path, 'r') as inp:
        file_graph = json.load(inp)
    return file_graph


def get_history_features_for_commits(graph, repo_path, branch, commit_hashes):
    """
    Function that extracts the history features for specified commit hashes.
    They are the total number of authors, the total age, and the total
    number of unique changes.
    """
    repo = Repository(repo_path)
    head = repo.references.get(branch)

    commits = list(repo.walk(head.target, GIT_SORT_TOPOLOGICAL | GIT_SORT_REVERSE))
    commit_map = {str(commit.id): commit for commit in commits}

    features = []

    for commit_hash in tqdm(commit_hashes):
        if commit_hash not in commit_map:
            print(f"Commit {commit_hash} not found in the repository.")
            continue

        commit = commit_map[commit_hash]
        parent = commit.parents[0] if commit.parents else None

        if not parent:
            # If no parent, it's the initial commit
            features.append([commit_hash, 1.0, 0.0, 0.0])
            continue

        files = get_diffing_files(commit, parent, repo)

        total_number_of_authors = set()
        total_age = []
        total_unique_changes = set()

        for (_, name, _) in files:
            if name not in graph or commit_hash not in graph[name]:
                continue

            sub_graph = graph[name][commit_hash]
            total_number_of_authors.update(sub_graph['authors'])

            prev_commit = sub_graph['prevcommit']
            if prev_commit:
                total_unique_changes.add(prev_commit)

                prev_commit_obj = repo.get(prev_commit)
                total_age.append(commit.commit_time - prev_commit_obj.commit_time)

        total_age = float(sum(total_age)) / len(total_age) if total_age else 0

        commit_feat = [commit_hash, float(len(total_number_of_authors)), float(total_age), float(len(total_unique_changes))]
        features.append(commit_feat)

    return features


def save_history_features(history_features, path):
    """
    Function to save the history features as a CSV file.
    """
    with open(path, 'w') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["commit_hash", "ndev", "age", "nuc"])
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
        default=f"./{suffix_file}/file_graph.json",
        help="The path to where the graph is stored."
    )
    PARSER.add_argument(
        "--output",
        "-o",
        type=str,
        default=f"./{suffix_file}/history{suffix_num}.csv",
        help="The path where the output is written."
    )
    PARSER.add_argument(
        "--commit-file",
        "-c",
        type=str,
        default=f"./{suffix_file}/commit_id{suffix_num}.csv",
        help="Path to the commit_id.csv file."
    )

    ARGS = PARSER.parse_args()
    REPO_PATH = ARGS.repository
    BRANCH = ARGS.branch
    SAVE_GRAPH = ARGS.save_graph
    GRAPH_PATH = ARGS.graph_path
    COMMIT_FILE = ARGS.commit_file
    OUTPUT = ARGS.output

    if SAVE_GRAPH:
        save_history_features_graph(REPO_PATH, BRANCH, GRAPH_PATH)

    # Load commit hashes from CSV file
    commit_data = pd.read_csv(COMMIT_FILE)
    commit_hashes = commit_data['commit_hash'].tolist()

    # Load the history graph
    GRAPH = load_history_features_graph(GRAPH_PATH)

    # Extract features for the specified commit hashes
    HISTORY_FEATURES = get_history_features_for_commits(GRAPH, REPO_PATH, BRANCH, commit_hashes)

    # Save the history features to a CSV file
    save_history_features(HISTORY_FEATURES, OUTPUT)
