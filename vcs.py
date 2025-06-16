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
BRANCHES_DIR = os.path.join(VCS_DIR, "branches")
HEAD_FILE = os.path.join(VCS_DIR, "HEAD")
LOGS_DIR = os.path.join(VCS_DIR, "logs")


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
    os.makedirs(LOGS_DIR)

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
    ensure_repo()

    if not os.path.exists(path):
        print(f"Path '{path}' not found.")
        return

    # Load existing index
    if os.path.exists(INDEX_FILE):
        with open(INDEX_FILE, "r") as f:
            index = json.load(f)
    else:
        index = []

    # Create a lookup for fast comparison
    staged_map = {entry["filename"]: entry["hash"] for entry in index}
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
                files_to_add.append(rel_path)

    updated = False

    for filepath in files_to_add:
        if not os.path.exists(filepath):
            continue

        file_hash = get_file_hash(filepath)

        if filepath in staged_map:
            if staged_map[filepath] == file_hash:
                continue  # Skip unchanged files
            else:
                # Update hash for modified file
                for entry in index:
                    if entry["filename"] == filepath:
                        entry["hash"] = file_hash
                        break
                print(f"Updated '{filepath}' in staging area.")
        else:
            # New file
            index.append({
                "filename": filepath,
                "hash": file_hash
            })
            print(f"Added '{filepath}' to staging area.")

        updated = True

    if updated:
        with open(INDEX_FILE, "w") as f:
            json.dump(index, f, indent=2)
    else:
        print("No new or changed files to stage.")

def get_current_branch_name():
    if not os.path.exists(HEAD_FILE):
        return None
    with open(HEAD_FILE, "r") as f:
        ref = f.read().strip()
    if ref.startswith("ref: "):
        # Example: "ref: refs/heads/main" → return "main"
        return ref.split("/")[-1]
    return None  # Detached HEAD or commit ID directly


def update_branch_head(commit_id):
    branch_name = get_current_branch_name()
    if branch_name:
        ref_path = os.path.join(VCS_DIR, "refs", "heads", branch_name)
        with open(ref_path, "w") as f:
            f.write(commit_id)
    else:
        # Detached HEAD
        with open(HEAD_FILE, "w") as f:
            f.write(commit_id)


def commit(message):
    ensure_repo()

    if not os.path.exists(INDEX_FILE):
        print("No index file found.")
        return

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
        dest = os.path.join(commit_dir, src)  # preserve relative path
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        shutil.copy2(src, dest)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    branch_name = get_current_branch_name()
    current_commit_id = get_current_commit_id()

    # Update branch reference to new commit ID
    branch_file = os.path.join(BRANCHES_DIR, branch_name)
    with open(branch_file, "w") as f:
        f.write(commit_id)

    # Update branch-specific log
    branch_log_file = os.path.join(LOGS_DIR, f"{branch_name}.json")
    if os.path.exists(branch_log_file):
        with open(branch_log_file, "r") as f:
            log = json.load(f)
    else:
        log = []

    log_entry = {
        "id": commit_id,
        "message": message,
        "timestamp": timestamp,
        "parent": current_commit_id,  # good for merges, history traversal
        "files": [entry["filename"] for entry in index]
    }

    log.append(log_entry)

    with open(branch_log_file, "w") as f:
        json.dump(log, f, indent=2)

    # Clear the staging area
    with open(INDEX_FILE, "w") as f:
        json.dump([], f)

    print(f"Committed as {commit_id}: {message}")


def get_current_commit_id():
    if not os.path.exists(HEAD_FILE):
        return None

    with open(HEAD_FILE, 'r') as f:
        ref_line = f.read().strip()

    if ref_line.startswith("ref: "):
        branch_name = ref_line.replace("ref: refs/heads/", "")
        branch_file = os.path.join(BRANCHES_DIR, branch_name)
        if os.path.exists(branch_file):
            with open(branch_file, "r") as f:
                return f.read().strip()
    else:
        # Detached HEAD (direct commit checkout)
        return ref_line

    return None


def show_log():
    ensure_repo()

    branch_name = get_current_branch_name()
    current_commit_id = get_current_commit_id()
    branch_log_file = os.path.join(LOGS_DIR, f"{branch_name}.json")

    if not os.path.exists(branch_log_file):
        print("No commit history found.")
        return

    with open(branch_log_file, "r") as f:
        log_entries = json.load(f)

    if not log_entries:
        print("No commit history found.")
        return

    print(f"== Commit history for branch '{branch_name}' ==")
    print(f"HEAD -> {current_commit_id}")
    print()

    for entry in reversed(log_entries):
        pointer = " (HEAD)" if entry["id"] == current_commit_id else ""
        print(f"Commit ID: {entry['id']}{pointer}")
        print(f"Timestamp: {entry['timestamp']}")
        print(f"Message: {entry['message']}")
        print(f"Files: {', '.join(entry['files'])}")
        print("-" * 40)


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
    ensure_repo()

    if not os.path.exists(INDEX_FILE):
        print("Staging area is already empty.")
        return

    with open(INDEX_FILE, "r") as f:
        index = json.load(f)

    # If user passed 'remove .' or 'remove ./', clear all
    if os.path.normpath(filename) == ".":
        if not index:
            print("Staging area is already empty.")
        else:
            with open(INDEX_FILE, "w") as f:
                json.dump([], f, indent=2)
            print("Cleared all files from staging area.")
        return

    # Otherwise, remove a specific file
    new_index = [entry for entry in index if entry["filename"] != filename]

    if len(new_index) == len(index):
        print(f"File '{filename}' is not staged.")
    else:
        with open(INDEX_FILE, "w") as f:
            json.dump(new_index, f, indent=2)
        print(f"Removed '{filename}' from staging area.")


def diff(filename):
    ensure_repo()

    filename = os.path.normpath(filename)

    if not os.path.exists(INDEX_FILE):
        print("No index found. Nothing is staged.")
        return

    with open(INDEX_FILE, "r") as f:
        index = json.load(f)

    if not any(os.path.normpath(entry["filename"]) == filename for entry in index):
        print(f"File '{filename}' is not staged.")
        return

    if not os.path.exists(filename):
        print(f"File '{filename}' is missing in working directory.")
        return

    with open(filename, "r") as f:
        current_lines = f.readlines()

    # Use current branch's latest commit instead of global log
    commit_id = get_current_commit_id()
    if not commit_id:
        print("No committed version to diff against.")
        return

    commit_dir = os.path.join(COMMITS_DIR, commit_id)
    committed_file_path = os.path.join(commit_dir, filename)

    if not os.path.exists(committed_file_path):
        print("No committed version to diff against.")
        return

    with open(committed_file_path, "r") as f:
        previous_lines = f.readlines()

    print(f"--- Committed: {filename}")
    print(f"+++ Working:   {filename}")

    for old, new in zip(previous_lines, current_lines):
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

def create_branch(branch_name):
    ensure_repo()
    current_branch = get_current_branch_name()
    current_commit_file = os.path.join(VCS_DIR, "refs", "heads", current_branch)

    if not os.path.exists(current_commit_file):
        print(f"Error: Current branch '{current_branch}' is invalid.")
        return

    # Create .vcs/refs/heads directory if it doesn't exist
    heads_dir = os.path.join(VCS_DIR, "refs", "heads")
    os.makedirs(heads_dir, exist_ok=True)

    # Get the latest commit of current branch
    with open(current_commit_file, "r") as f:
        commit_id = f.read().strip()

    new_branch_file = os.path.join(heads_dir, branch_name)
    with open(new_branch_file, "w") as f:
        f.write(commit_id)

    # Copy or initialize the branch log
    old_branch_log = os.path.join(LOGS_DIR, f"{current_branch}.json")
    new_branch_log = os.path.join(LOGS_DIR, f"{branch_name}.json")

    if os.path.exists(old_branch_log):
        shutil.copy(old_branch_log, new_branch_log)
    else:
        with open(new_branch_log, "w") as f:
            json.dump([], f)

    print(f"Created branch '{branch_name}' from '{current_branch}'")



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

    branch_ref = os.path.join(VCS_DIR, "refs", "heads", branch_name)
    branch_log = os.path.join(LOGS_DIR, f"{branch_name}.json")

    if not os.path.exists(branch_ref) or not os.path.exists(branch_log):
        print(f"Branch '{branch_name}' does not exist.")
        return

    # Step 1: Update HEAD to point to the branch ref
    with open(HEAD_FILE, 'w') as f:
        f.write(f"ref: refs/heads/{branch_name}")

    # Step 2: Clear working directory (optional but recommended)
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
        src = os.path.join(commit_dir, filename)
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        shutil.copy2(src, filename)

    with open(INDEX_FILE, "w") as f:
        json.dump([], f)

    print(f"Switched to branch '{branch_name}'. Restored commit {commit_id}.")


def list_branches():
    ensure_repo()

    branches = sorted(
        [b for b in os.listdir(BRANCHES_DIR) if not b.startswith('.')]
    )
    current = get_current_branch_name()

    if not branches:
        print("No branches found.")
        return

    print("Branches:")
    for branch in branches:
        if branch == current:
            print(f"* {branch} (current)")
        else:
            print(f"  {branch}")

    if current is None:
        print("(HEAD detached at commit)")



def add_file(filename):
    ensure_repo()

    filename = os.path.normpath(filename)

    if not os.path.exists(filename):
        print(f"Error: {filename} does not exist.")
        return

    # Load existing index
    if os.path.exists(INDEX_FILE):
        with open(INDEX_FILE, 'r') as f:
            index = json.load(f)
    else:
        index = []

    file_hash = get_file_hash(filename)
    staged_map = {
        os.path.normpath(entry["filename"]): entry["hash"]
        for entry in index
    }

    updated = False

    if filename in staged_map:
        if staged_map[filename] == file_hash:
            print(f"No changes in '{filename}'")
            return
        else:
            # Update hash for modified file
            for entry in index:
                if entry["filename"] == filename:
                    entry["hash"] = file_hash
                    break
            print(f"Updated '{filename}' in staging area.")
            updated = True
    else:
        index.append({
            "filename": filename,
            "hash": file_hash
        })
        print(f"Added '{filename}' to staging area.")
        updated = True

    if updated:
        with open(INDEX_FILE, 'w') as f:
            json.dump(index, f, indent=2)


def merge_branch(branch_name):
    ensure_repo()
    ensure_branch_dir()

    current_branch = get_current_branch_name()
    if branch_name == current_branch:
        print("Cannot merge a branch into itself.")
        return

    # Resolve log paths
    target_log_file = os.path.join(LOGS_DIR, f"{branch_name}.json")
    current_log_file = os.path.join(LOGS_DIR, f"{current_branch}.json")

    if not os.path.exists(target_log_file):
        print(f"Branch '{branch_name}' does not exist or has no commits.")
        return

    # Load logs
    with open(target_log_file, 'r') as f:
        target_log = json.load(f)
    with open(current_log_file, 'r') as f:
        current_log = json.load(f)

    if not target_log:
        print(f"No commits in branch '{branch_name}' to merge.")
        return

    latest_commit = target_log[-1]
    merged_files = []
    conflicts = []

    for file in latest_commit["files"]:
        commit_file_path = os.path.join(COMMITS_DIR, latest_commit["id"], file)

        if not os.path.exists(commit_file_path):
            continue  # skip missing files in the commit (optional safety)

        os.makedirs(os.path.dirname(file), exist_ok=True)

        if not os.path.exists(file):
            shutil.copy2(commit_file_path, file)
            merged_files.append(file)
        else:
            with open(file, 'r') as f:
                working_content = f.read()
            with open(commit_file_path, 'r') as f:
                incoming_content = f.read()

            if working_content.strip() == incoming_content.strip():
                continue  # no conflict, skip
            else:
                conflict_file = f"{file}.conflict"
                with open(conflict_file, 'w') as f:
                    f.write(f"======= Incoming from branch '{branch_name}' =======\n")
                    f.write(incoming_content)
                    f.write(f"\n======= Current branch '{current_branch}' =======\n")
                    f.write(working_content)
                conflicts.append(file)

    if conflicts:
        print("\n⚠️ Merge completed with conflicts:")
        for f in conflicts:
            print(f" - {f} => {f}.conflict")
        print("Please resolve conflicts and commit manually.")
    else:
        for f in merged_files:
            add_file(f)
        commit(f"Merged branch '{branch_name}' into '{current_branch}'")
        print(f"✔ Merge complete: {len(merged_files)} files merged and committed.")


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
