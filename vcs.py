import os
import sys
import json
import hashlib
from datetime import datetime
import shutil
import uuid
import click

@click.group()
@click.version_option("0.1.0")
def cli():
    """mini-vcs: A simple version control system."""
    pass


VCS_DIR = ".vcs"
COMMITS_DIR = os.path.join(VCS_DIR, "commits")
INDEX_FILE = os.path.join(VCS_DIR, "index.json")
LOG_FILE = os.path.join(VCS_DIR, "log.json")
BRANCHES_DIR = os.path.join(VCS_DIR, "branches")  # <-- Add this
HEAD_FILE = os.path.join(VCS_DIR, "HEAD")

def ensure_repo():
    if not os.path.exists(VCS_DIR):
        print("Error: No VCS repository found. Run `vcs init` first.")
        sys.exit(1)

def init():
    if os.path.exists(VCS_DIR):
        print("Repository already initialized.")
        return

    os.makedirs(VCS_DIR)
    os.makedirs(COMMITS_DIR)
    os.makedirs(BRANCHES_DIR)

    with open(HEAD_FILE, "w") as f:
        f.write("ref: refs/heads/main")

    # Create the main branch pointing to an empty state
    with open(os.path.join(BRANCHES_DIR, "main"), "w") as f:
        f.write("")

    with open(INDEX_FILE, "w") as f:
        json.dump([], f)

    print("Initialized empty VCS repository with main branch.")


def get_file_hash(filepath):
    hasher = hashlib.sha256()
    with open(filepath, 'rb') as f:
        buf = f.read()
        hasher.update(buf)
    return hasher.hexdigest()

def add(path):
    if not os.path.exists(path):
        print(f"Path '{path}' not found.")
        return

    with open(INDEX_FILE, "r") as f:
        index = json.load(f)

    already_staged = {entry["filename"] for entry in index}

    files_to_add = []

    if os.path.isfile(path):
        files_to_add.append(path)
    else:
        for root, _, files in os.walk(path):
            if ".vcs" in root:
                continue  # Skip internal repo data
            for f in files:
                full_path = os.path.join(root, f)
                rel_path = os.path.relpath(full_path)
                if rel_path not in already_staged:
                    files_to_add.append(rel_path)

    if not files_to_add:
        print("No new files to stage.")
        return

    for filepath in files_to_add:
        file_hash = get_file_hash(filepath)
        index.append({
            "filename": filepath,
            "hash": file_hash
        })
        print(f"Added '{filepath}' to staging area.")

    with open(INDEX_FILE, "w") as f:
        json.dump(index, f, indent=2)

def get_current_branch():
    if not os.path.exists(HEAD_FILE):
        return None
    with open(HEAD_FILE) as f:
        ref = f.read().strip()
    if ref.startswith("ref: "):
        return ref[5:]
    return None  # Detached HEAD

def update_branch_head(commit_id):
    ref = get_current_branch()
    if ref:
        ref_path = os.path.join(VCS_DIR, ref)
        with open(ref_path, "w") as f:
            f.write(commit_id)
    else:
        # Detached HEAD – update HEAD directly
        with open(HEAD_FILE, "w") as f:
            f.write(commit_id)

def commit(message):
    ensure_repo()

    with open(INDEX_FILE, "r") as f:
        index = json.load(f)

    if not index:
        print("Nothing to commit.")
        return

    commit_id = str(uuid.uuid4())[:8]
    commit_dir = os.path.join(COMMITS_DIR, commit_id)
    os.makedirs(commit_dir)

    for entry in index:
        src = entry["filename"]
        dest = os.path.join(commit_dir, os.path.basename(src))
        shutil.copy2(src, dest)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Load the correct branch log
    branch = get_current_branch()
    branch_log_file = os.path.join(BRANCHES_DIR, f"{branch}.json")

    if os.path.exists(branch_log_file):
        with open(branch_log_file, "r") as f:
            log = json.load(f)
    else:
        log = []

    log_entry = {
        "id": commit_id,
        "message": message,
        "timestamp": timestamp,
        "files": [entry["filename"] for entry in index]
    }

    log.append(log_entry)

    with open(branch_log_file, "w") as f:
        json.dump(log, f, indent=2)

    # Clear staging area
    with open(INDEX_FILE, "w") as f:
        json.dump([], f)

    print(f"Committed as {commit_id}: {message}")


def show_log():
    if not os.path.exists(LOG_FILE):
        print("No commit history found.")
        return

    with open(LOG_FILE, "r") as f:
        log = json.load(f)

    if not log:
        print("No commits yet.")
        return

    for entry in reversed(log):  # Show latest first
        print(f"\nCommit: {entry['id']}")
        print(f"Date: {entry['timestamp']}")
        print(f"Message: {entry['message']}")
        print("Files:")
        for file in entry['files']:
            print(f"  - {file}")

def status():
    with open(INDEX_FILE, "r") as f:
        index = json.load(f)

    if not index:
        print("No files staged.")
        return

    print("Staged files:")
    for entry in index:
        filename = entry["filename"]
        staged_hash = entry["hash"]

        if not os.path.exists(filename):
            print(f"  - {filename} (deleted)")
            continue

        current_hash = get_file_hash(filename)

        if current_hash != staged_hash:
            print(f"  - {filename} (modified)")
        else:
            print(f"  - {filename} (unchanged)")

def remove(filename):
    with open(INDEX_FILE, "r") as f:
        index = json.load(f)

    new_index = [entry for entry in index if entry["filename"] != filename]

    if len(new_index) == len(index):
        print(f"File '{filename}' is not staged.")
    else:
        with open(INDEX_FILE, "w") as f:
            json.dump(new_index, f, indent=2)
        print(f"Removed '{filename}' from staging area.")

def diff(filename):
    with open(INDEX_FILE, "r") as f:
        index = json.load(f)

    staged_entry = next((e for e in index if e["filename"] == filename), None)
    if not staged_entry:
        print(f"File '{filename}' is not staged.")
        return

    staged_path = filename
    if not os.path.exists(staged_path):
        print(f"File '{filename}' is missing in working directory.")
        return

    with open(filename, "r") as f:
        current_lines = f.readlines()

    commit_dir = None
    with open(LOG_FILE, "r") as f:
        for commit in reversed(json.load(f)):
            if filename in commit['files']:
                commit_dir = os.path.join(COMMITS_DIR, commit["id"])
                break

    if not commit_dir or not os.path.exists(os.path.join(commit_dir, filename)):
        print("No committed version to diff against.")
        return

    with open(os.path.join(commit_dir, filename), "r") as f:
        previous_lines = f.readlines()

    print(f"--- Committed: {filename}")
    print(f"+++ Working:   {filename}")
    for i, (old, new) in enumerate(zip(previous_lines, current_lines)):
        if old != new:
            print(f"- {old.strip()}")
            print(f"+ {new.strip()}")

    if len(current_lines) > len(previous_lines):
        for line in current_lines[len(previous_lines):]:
            print(f"+ {line.strip()}")
    elif len(previous_lines) > len(current_lines):
        for line in previous_lines[len(current_lines):]:
            print(f"- {line.strip()}")

def checkout(commit_id, filename=None):
    commit_path = os.path.join(COMMITS_DIR, commit_id)

    if not os.path.exists(commit_path):
        print(f"Commit '{commit_id}' not found.")
        return

    if filename:
        file_path = os.path.join(commit_path, filename)
        if not os.path.exists(file_path):
            print(f"File '{filename}' not found in commit '{commit_id}'.")
            return

        # Only create directory if needed
        dir_name = os.path.dirname(filename)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)

        shutil.copy2(file_path, filename)
        print(f"Restored '{filename}' from commit {commit_id}.")
    else:
        # Restore all files in the commit
        for root, _, files in os.walk(commit_path):
            for file in files:
                rel_dir = os.path.relpath(root, commit_path)
                target_dir = '.' if rel_dir == '.' else rel_dir
                os.makedirs(target_dir, exist_ok=True)

                src = os.path.join(root, file)
                dest = os.path.join(target_dir, file)
                shutil.copy2(src, dest)
                print(f"Restored '{dest}' from commit {commit_id}.")


def ensure_branch_dir():
    branches_dir = os.path.join(VCS_DIR, "branches")
    if not os.path.exists(branches_dir):
        os.makedirs(branches_dir)

def get_current_branch():
    head_file = os.path.join(VCS_DIR, "HEAD")
    if os.path.exists(head_file):
        with open(head_file, 'r') as f:
            return f.read().strip()
    return "main"  # default branch


def create_branch(branch_name):
    ensure_repo()
    ensure_branch_dir()

    branches_dir = os.path.join(VCS_DIR, "branches")
    new_branch_log = os.path.join(branches_dir, f"{branch_name}.json")

    if os.path.exists(new_branch_log):
        print(f"Branch '{branch_name}' already exists.")
        return

    current_branch = get_current_branch()
    current_log = os.path.join(branches_dir, f"{current_branch}.json")

    if not os.path.exists(current_log):
        # Create from global log.json fallback
        shutil.copy(LOG_FILE, new_branch_log)
    else:
        shutil.copy(current_log, new_branch_log)

    print(f"Created branch '{branch_name}'.")

def clear_working_directory():
    ignored_dirs = {".vcs", ".git", ".idea", ".venv", "__pycache__"}

    for root, dirs, files in os.walk(".", topdown=True):
        # Skip ignored directories
        dirs[:] = [d for d in dirs if d not in ignored_dirs and not d.startswith(".")]

        for file in files:
            path = os.path.join(root, file)
            # Skip files in ignored directories
            if any(part in ignored_dirs for part in path.split(os.sep)):
                continue
            if os.path.isfile(path):
                os.remove(path)

def checkout_branch(branch_name):
    ensure_repo()
    ensure_branch_dir()

    branches_dir = os.path.join(VCS_DIR, "branches")
    branch_log = os.path.join(branches_dir, f"{branch_name}.json")

    if not os.path.exists(branch_log):
        print(f"Branch '{branch_name}' does not exist.")
        return

    # Step 1: Update HEAD
    with open(os.path.join(VCS_DIR, "HEAD"), 'w') as f:
        f.write(branch_name)

    # Step 2: Clear working directory (optional safety)
    clear_working_directory()

    # Step 3: Load latest commit of target branch
    with open(branch_log, "r") as f:
        log = json.load(f)

    if not log:
        print(f"Switched to branch '{branch_name}' (no commits yet).")
        return

    latest_commit = log[-1]
    commit_id = latest_commit["id"]
    commit_dir = os.path.join(COMMITS_DIR, commit_id)

    # Step 4: Restore each file from commit to working directory
    for filename in latest_commit["files"]:
        src = os.path.join(commit_dir, os.path.basename(filename))
        shutil.copy2(src, filename)

    print(f"Switched to branch '{branch_name}'. Restored commit {commit_id}.")


def list_branches():
    ensure_repo()
    ensure_branch_dir()

    branches_dir = os.path.join(VCS_DIR, "branches")
    current = get_current_branch()

    branches = [f[:-5] for f in os.listdir(branches_dir) if f.endswith(".json")]
    branches.sort()

    print("Branches:")
    for b in branches:
        if b == current:
            print(f"* {b} (current)")
        else:
            print(f"  {b}")

def add_file(filename):
    ensure_repo()

    if not os.path.exists(filename):
        print(f"Error: {filename} does not exist.")
        return

    # Load index
    if os.path.exists(INDEX_FILE):
        with open(INDEX_FILE, 'r') as f:
            index = json.load(f)
    else:
        index = []

    # Add file if not already present
    if filename not in index:
        index.append(filename)
        with open(INDEX_FILE, 'w') as f:
            json.dump(index, f)

def merge_branch(branch_name):
    ensure_repo()
    ensure_branch_dir()

    current = get_current_branch()
    if branch_name == current:
        print("Cannot merge a branch into itself.")
        return

    branches_dir = os.path.join(VCS_DIR, "branches")
    target_log_file = os.path.join(branches_dir, f"{branch_name}.json")
    current_log_file = os.path.join(branches_dir, f"{current}.json")

    if not os.path.exists(target_log_file):
        print(f"Branch '{branch_name}' does not exist.")
        return

    with open(target_log_file, 'r') as f:
        target_log = json.load(f)
    with open(current_log_file, 'r') as f:
        current_log = json.load(f)

    if not target_log:
        print(f"No commits found in branch '{branch_name}'.")
        return

    # Get latest commit from target
    latest_commit = target_log[-1]
    merged_files = []
    conflicts = []

    for file in latest_commit["files"]:
        target_file_path = os.path.join(VCS_DIR, "commits", latest_commit["id"], file)

        if not os.path.exists(file):
            shutil.copy(target_file_path, file)
            merged_files.append(file)
        else:
            # Conflict detection: compare with current branch version
            with open(file, 'r') as f:
                working_content = f.read()
            with open(target_file_path, 'r') as f:
                incoming_content = f.read()

            if working_content.strip() != incoming_content.strip():
                # Save conflicted version
                conflict_file = f"{file}.conflict"
                with open(conflict_file, 'w') as f:
                    f.write("======= Incoming =======\n")
                    f.write(incoming_content)
                    f.write("\n======= Current =======\n")
                    f.write(working_content)
                conflicts.append(file)
            else:
                # Same content, skip
                pass

    # Commit merged files (if no conflict)
    if conflicts:
        print("\nMerge completed with conflicts:")
        for c in conflicts:
            print(f" - {c} => {c}.conflict")
        print("Please resolve conflicts manually and then commit.")
    else:
        if merged_files:
            for f in merged_files:
                add_file(f)
            commit(f"Merged from branch '{branch_name}'")
        else:
            print("Nothing to merge. Already up to date.")


def main():
    if len(sys.argv) < 2:
        print("Usage: python vcs.py <command>")
        return

    command = sys.argv[1]

    if command == "init":
        init()
    elif command == "add":
        if len(sys.argv) < 3:
            print("Usage: python vcs.py add <filename>")
            return
        add(sys.argv[2])
    elif command == "commit":
        if len(sys.argv) < 3:
            print("Usage: python vcs.py commit <message>")
            return
        commit(" ".join(sys.argv[2:]))
    elif command == "log":
        show_log()
    elif command == "status":
        status()
    elif command == "remove":
        if len(sys.argv) < 3:
            print("Usage: python vcs.py remove <filename>")
            return
        remove(sys.argv[2])
    elif command == "diff":
        if len(sys.argv) < 3:
            print("Usage: python vcs.py diff <filename>")
            return
        diff(sys.argv[2])
    elif command == "checkout":
        if len(sys.argv) < 3:
            print("Usage: python vcs.py checkout <commit-id> [<filename>]")
            return
        commit_id = sys.argv[2]
        filename = sys.argv[3] if len(sys.argv) >= 4 else None
        checkout(commit_id, filename)
    elif command == "branch" and len(sys.argv) == 3:
        branch_name = sys.argv[2]
        create_branch(branch_name)
    elif command == "checkout-branch" and len(sys.argv) == 3:
        checkout_branch(sys.argv[2])
    elif command == "list-branches":
        list_branches()
    elif command == "merge" and len(sys.argv) == 3:
        merge_branch(sys.argv[2])
    else:
        print(f"Unknown command: {command}")


if __name__ == "__main__":
    main()
