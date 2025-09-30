#!/bin/bash
# Git Worktree Creation Script
# Usage: ./create-worktree.sh <task-id> [base-branch]

set -e

TASK_ID="$1"
BASE_BRANCH="${2:-main}"
PROJECT_ROOT="$(git rev-parse --show-toplevel)"
WORKSPACE_DIR="$PROJECT_ROOT/workspaces/${TASK_ID}"
BRANCH_NAME="${TASK_ID}-feature"

# Source logging utilities
source "$PROJECT_ROOT/scripts/common/logging.sh"

# 如果腳本執行過程中發生錯誤（ERR），就會呼叫 log_script_end 來記錄腳本結束並標記為失敗。
trap 'log_script_end "create-worktree.sh" "false"' ERR

# Log script start
log_script_start "create-worktree.sh" "$*"

if [ -z "$TASK_ID" ]; then
  echo "Error: Task ID is required"
  echo "Usage: $0 <task-id> [base-branch]"
  log_error "create-worktree: Task ID is required"
  exit 1
fi

log_operation "create-worktree" "task_id=$TASK_ID, base_branch=$BASE_BRANCH, workspace_dir=$WORKSPACE_DIR"

# Check if we're in a git repository
if ! git rev-parse --git-dir >/dev/null 2>&1; then
  echo "Error: Not in a git repository"
  log_error "create-worktree: Not in a git repository"
  exit 1
fi

# Check if workspace directory already exists
if [ -d "$WORKSPACE_DIR" ]; then
  echo "Error: Workspace directory $WORKSPACE_DIR already exists"
  log_error "create-worktree: Workspace directory already exists: $WORKSPACE_DIR"
  exit 1
fi

# Check for uncommitted changes
if ! git diff-index --quiet HEAD --; then
  echo "Committing current changes to avoid conflicts..."
  git add .
  git commit -m "WIP: Auto-commit before creating worktree for $TASK_ID"
fi

# Ensure we're on the base branch and it's up to date
echo "Updating $BASE_BRANCH..."
git checkout "$BASE_BRANCH" # Ensure we're on the base branch
# Fetch latest changes from remote
git pull origin --rebase "$BASE_BRANCH" # Update base branch

# Create worktree with new branch (this creates both the branch and worktree)
echo "Creating worktree and branch $BRANCH_NAME at $WORKSPACE_DIR..."
git worktree add -b "$BRANCH_NAME" "$WORKSPACE_DIR" "$BASE_BRANCH"

# Push the new branch to remote from the worktree
echo "Setting up remote tracking..."
cd "$WORKSPACE_DIR"
git push -u origin "$BRANCH_NAME"
cd - >/dev/null

echo "Worktree created successfully!"
echo "To start working:"
echo "  cd $WORKSPACE_DIR"
echo ""
echo "When finished, use cleanup-worktree.sh to clean up."

log_script_end "create-worktree.sh" "true"
