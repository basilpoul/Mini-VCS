# 🧪 mini-vcs

A minimal, Python-based version control system that supports:

- `init` – initialize a repository
- `add <file>` – stage a file
- `remove <file>` – unstage a file
- `commit "<msg>"` – commit staged changes
- `log` – view commit history
- `status` – view current status
- `diff <file>` – see changes since last commit
- `checkout <id> <file>` – restore a file from a previous commit
- `branch <name>` – create a new branch
- `checkout-branch <name>` – switch to a branch
- `list-branches` – list all branches
- `merge <branch>` – merge a branch into current (with conflict detection)

## 🔧 Installation
From the folder containing `setup.py`, run:

```bash
pip install .
```

## ❌ Uninstall

```bash
pip uninstall mini-vcs
```

## 📘 Usage Examples

```bash
vcs init
echo "apple" > a.txt
vcs add a.txt
vcs commit "Initial commit"
vcs branch dev
vcs checkout-branch dev
echo "banana" >> a.txt
vcs add a.txt
vcs commit "Added banana"
vcs checkout-branch main
echo "orange" >> a.txt
vcs add a.txt
vcs commit "Added orange"
vcs merge dev
# resolve conflict manually
vcs add a.txt
vcs commit "Resolved conflict"
```

## 📂 Structure

```
.vcs/
├── commits/
├── index.json
├── log.json
├── HEAD
└── branches/
```