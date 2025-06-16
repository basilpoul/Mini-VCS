#!/bin/bash

# Test script for the installed VCS module in an external directory

# Exit if any command fails
set -e

# Use a clean directory for testing
TEST_DIR="vcs_test_env"
rm -rf "$TEST_DIR"
mkdir "$TEST_DIR"
cd "$TEST_DIR" || exit 1

echo "🔧 Running VCS tests in: $(pwd)"

run_cmd() {
    echo "▶️  python -m vcs $*"
    python -m vcs "$@"
    echo
}

# 1. Initialize repo
run_cmd init

# 2. Create and commit a file
echo "first version" > file1.txt
run_cmd add file1.txt
run_cmd commit "Initial commit"

# 3. Modify the file and commit again
echo "second version" > file1.txt
run_cmd add file1.txt
run_cmd commit "Second commit"

# 4. Show log and status
run_cmd log
run_cmd status

# 5. Create and switch to a new branch
run_cmd branch dev
run_cmd checkout-branch dev

# 6. Add a new file in dev branch
echo "dev content" > dev.txt
run_cmd add dev.txt
run_cmd commit "Dev branch work"

# 7. List all branches
run_cmd list-branches

# 8. Switch back to main
run_cmd checkout-branch main

# 9. Merge dev into main
run_cmd merge dev

# 10. Simulate merge conflict
echo "main side" > conflict.txt
run_cmd add conflict.txt
run_cmd commit "Main creates conflict"
run_cmd checkout-branch dev
echo "dev side" > conflict.txt
run_cmd add conflict.txt
run_cmd commit "Dev creates conflict"
run_cmd checkout-branch main
run_cmd merge dev  # should create conflict.txt.conflict

# 11. Checkout file from previous commit
LAST_COMMIT=$(python -m vcs log | grep -Eo '^[a-f0-9]{8}' | tail -n 1)
echo "📦 Last commit: $LAST_COMMIT"
run_cmd checkout "$LAST_COMMIT" file1.txt

# 12. Test diff functionality
echo "added new line" >> file1.txt
run_cmd add file1.txt
run_cmd diff file1.txt

echo "✅ All tests completed successfully."
