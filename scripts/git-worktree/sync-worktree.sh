#!/bin/bash
# Git Worktree Sync Script
# Usage: ./sync-worktree.sh <task-id> [base-branch]

set -e

TASK_ID="$1"
BASE_BRANCH="${2:-main}"
PROJECT_ROOT="$(git rev-parse --show-toplevel)"
WORKSPACE_DIR="$PROJECT_ROOT/workspaces/${TASK_ID}"
BRANCH_NAME="${TASK_ID}-feature"

# Source logging utilities
source "$PROJECT_ROOT/scripts/common/logging.sh"

# Error trap to log failures
trap 'log_script_end "sync-worktree.sh" "false"' ERR

# Log script start
log_script_start "sync-worktree.sh" "$*"

if [ -z "$TASK_ID" ]; then
  echo "Error: Task ID is required"
  echo "Usage: $0 <task-id> [base-branch]"
  log_error "sync-worktree: Task ID is required"
  exit 1
fi

log_operation "sync-worktree" "task_id=$TASK_ID, base_branch=$BASE_BRANCH"

# Check if we're in a git repository
if ! git rev-parse --git-dir >/dev/null 2>&1; then
  echo "Error: Not in a git repository"
  exit 1
fi

# Check if workspace directory exists
if [ ! -d "$WORKSPACE_DIR" ]; then
  echo "Error: Workspace directory $WORKSPACE_DIR does not exist"
  echo "Use create-worktree.sh to create it first"
  exit 1
fi

# Check if workspace has uncommitted changes
echo "Checking workspace status..."
cd "$WORKSPACE_DIR"
if [ -n "$(git status --porcelain)" ]; then
  echo "Warning: Workspace has uncommitted changes:"
  git status --short
  echo ""
  echo "Please commit or stash your changes before syncing"
  exit 1
fi

cd "$ORIGINAL_DIR"
echo "Syncing worktree with latest $BASE_BRANCH..."

# Save current directory
ORIGINAL_DIR=$(pwd)

# Update main branch
echo "Pulling latest changes from $BASE_BRANCH branch..."
if ! git checkout "$BASE_BRANCH"; then
  echo "Error: Failed to checkout $BASE_BRANCH branch"
  exit 1
fi

if ! git pull origin "$BASE_BRANCH"; then
  echo "Error: Failed to pull latest changes from origin/$BASE_BRANCH"
  exit 1
fi

# Switch to workspace and rebase onto latest changes
cd "$WORKSPACE_DIR" # Auto switch to ${TASK_ID}-feature branch
CURRENT_BRANCH=$(git branch --show-current)
echo "Current branch in worktree: $CURRENT_BRANCH"

if [ "$CURRENT_BRANCH" != "$BRANCH_NAME" ]; then
  echo "Warning: Expected branch $BRANCH_NAME, but found $CURRENT_BRANCH"
fi

echo "Rebasing $BRANCH_NAME onto latest $BASE_BRANCH..."
if ! git rebase "$BASE_BRANCH"; then
  echo "Rebase failed. You may need to resolve conflicts manually."
  echo "Use 'git rebase --continue' after resolving conflicts"
  echo "Or 'git rebase --abort' to cancel the rebase"
  exit 1
fi

# Return to original directory
cd "$ORIGINAL_DIR"

echo "Worktree sync completed successfully!"
echo "Workspace has been rebased onto latest $BASE_BRANCH"

log_script_end "sync-worktree.sh" "true"
