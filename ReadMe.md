# mini-vcs

A simple Python-based version control system that supports:

- `init` – initialize a repository  
- `add <file>` – stage a file  
- `remove <file>` – unstage a file  
- `commit "<msg>"` – commit staged changes  
- `log` – view commit history  
- `status` – view changes vs staged state  
- `diff <file>` – show file differences from last commit  
- `checkout <id> <file>` – restore a file from a previous commit  

---

## 🚀 Installation (Local)

From the folder containing `setup.py`, run:

```bash
pip install .

🧪 Full Example Workflow

vcs init
echo "Initial notes" > notes.txt
vcs add notes.txt
vcs commit "Initial commit"

echo "More content" >> notes.txt
vcs status
vcs diff notes.txt
vcs commit "Updated notes"
vcs log

vcs checkout <commit-id> notes.txt


#🔧 To Uninstall

pip uninstall mini-vcs
