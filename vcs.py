import os
import sys
import json
import hashlib
from datetime import datetime
import shutil
import uuid


VCS_DIR = ".vcs"
COMMITS_DIR = os.path.join(VCS_DIR, "commits")
INDEX_FILE = os.path.join(VCS_DIR, "index.json")
LOG_FILE = os.path.join(VCS_DIR, "log.json")


def init():
    if os.path.exists(VCS_DIR):
        print("Repository already initialized.")
        return

    os.makedirs(COMMITS_DIR)

    with open(INDEX_FILE, "w") as f:
        json.dump([], f)

    with open(LOG_FILE, "w") as f:
        json.dump([], f)

    print("Initialized empty VCS repository in .vcs/")

def get_file_hash(filepath):
    hasher = hashlib.sha256()
    with open(filepath, 'rb') as f:
        buf = f.read()
        hasher.update(buf)
    return hasher.hexdigest()

def add(filename):
    if not os.path.exists(filename):
        print(f"File '{filename}' not found.")
        return

    with open(INDEX_FILE, "r") as f:
        index = json.load(f)

    # Check if already staged
    for entry in index:
        if entry["filename"] == filename:
            print(f"File '{filename}' is already staged.")
            return

    file_hash = get_file_hash(filename)

    index.append({
        "filename": filename,
        "hash": file_hash
    })

    with open(INDEX_FILE, "w") as f:
        json.dump(index, f, indent=2)

    print(f"Added '{filename}' to staging area.")

def commit(message):
    with open(INDEX_FILE, "r") as f:
        index = json.load(f)

    if not index:
        print("Nothing to commit.")
        return

    commit_id = str(uuid.uuid4())[:8]  # Short unique ID
    commit_dir = os.path.join(COMMITS_DIR, commit_id)
    os.makedirs(commit_dir)

    for entry in index:
        src = entry["filename"]
        dest = os.path.join(commit_dir, os.path.basename(src))
        shutil.copy2(src, dest)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(LOG_FILE, "r") as f:
        log = json.load(f)

    log_entry = {
        "id": commit_id,
        "message": message,
        "timestamp": timestamp,
        "files": [entry["filename"] for entry in index]
    }

    log.append(log_entry)

    with open(LOG_FILE, "w") as f:
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

def checkout(commit_id, filename):
    commit_path = os.path.join(COMMITS_DIR, commit_id)
    file_path = os.path.join(commit_path, filename)

    if not os.path.exists(file_path):
        print(f"File '{filename}' not found in commit '{commit_id}'.")
        return

    shutil.copy2(file_path, filename)
    print(f"Restored '{filename}' from commit {commit_id}.")

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
        if len(sys.argv) < 4:
            print("Usage: python vcs.py checkout <commit-id> <filename>")
            return
        checkout(sys.argv[2], sys.argv[3])
    else:
        print(f"Unknown command: {command}")


if __name__ == "__main__":
    main()
