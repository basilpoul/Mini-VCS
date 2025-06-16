# 🗃️ mini-vcs

A simple, Git-like **Version Control System (VCS)** built from scratch using Python.  
This project supports basic features like file tracking, commits, branches, merges, conflict resolution, and more — all from the command line.

---

## 📦 Features

- ✅ Initialize a new repository
- ✅ Add files to staging area
- ✅ Commit changes with messages
- ✅ View commit history
- ✅ Create and switch between branches
- ✅ Merge branches with automatic or manual conflict resolution
- ✅ Check file differences
- ✅ Restore files from last commit

---

## 🚀 Getting Started

### ✅ Requirements
- Python 3.6+
- OS: Windows/Linux/Mac

---

## 🛠 Installation

Clone or download this repository. Then place `vcs.py` in a folder and use it as a **Python module**.

```bash
# Install as a module
# From directory containing setup.py run
pip install  .
```

Ensure the folder structure:
```
/your-project
│
├── vcs.py
├── testFiless.sh         # Optional: Test script
```

---

## 🧪 Usage

### 1. Initialize a repository
```bash
vcs init
```

Creates a `.vcs/` directory with required subdirectories and sets up the main branch.

---

### 2. Add files to staging
```bash
vcs add <filename>
```

Example:
```bash
vcs add file1.txt
```

---

### 3. Commit changes
```bash
vcs commit "Your commit message"
```

---

### 4. View commit log
```bash
vcs log
```

Displays the history of commits on the current branch.

---

### 5. View status
```bash
vcs status
```

Shows files staged for commit.

---

### 6. Branching

#### Create a new branch
```bash
vcs branch <branch_name>
```

#### List all branches
```bash
vcs list-branches
```

#### Switch to a branch
```bash
vcs checkout-branch <branch_name>
```

---

### 7. Merge branches

From the main branch, run:
```bash
vcs merge <source_branch>
```

- If files differ, a `filename.conflict` file is created for manual resolution.
- You can manually resolve it and commit again.

---

### 8. Show file diff
```bash
vcs diff <filename>
```

Compares current file with last committed version.

---

### 9. Restore file from last commit
```bash
vcs checkout <filename>
```

Restores a file from the most recent commit in current branch.

---

### 10. Uninstall
```bash
pip uninstall mini-vcs
```

.
Uninstalls the package
---

## 🧩 Directory Structure

```
.vcs/
├── commits/         # Stores all committed file snapshots
├── index.json       # Tracks staged files
├── HEAD             # Points to current branch
├── branches/        # Stores current commit per branch
├── logs/            # Commit history per branch
└── refs/heads/      # All branch pointers
```

---

## 🧪 Test Script

The `testFiless.sh` script demonstrates a full workflow including:

- init
- add, commit
- branching
- switching
- merging
- handling conflicts

```bash
./testFiless.sh
```

---

## ⚠️ Notes

- Currently does not support remote repos (push/pull)
- Merge conflicts must be resolved manually (auto-merging not supported)
- Does not track directories; only files are supported

---

## 📚 Example Workflow

```bash
python -m vcs init
echo "Hello" > file1.txt
python -m vcs add file1.txt
python -m vcs commit "Initial commit"
python -m vcs branch dev
python -m vcs checkout-branch dev
echo "Dev work" > dev.txt
python -m vcs add dev.txt
python -m vcs commit "Dev commit"
python -m vcs checkout-branch main
python -m vcs merge dev
```

---

## 📌 Future Improvements

- Add `.vcsignore` file support
- Enable undo/reset
- Add tagging and release versions
- CLI interface with `argparse` or `click`
- Interactive conflict resolution

---

## 👨‍💻 Author

Made with ❤️ for learning purposes.

> Inspired by Git but simplified to build conceptual clarity.

---

## 📝 License

This project is open-source and available under the MIT License.