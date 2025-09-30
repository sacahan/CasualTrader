#!/bin/bash
# Git Worktree List Script
# Usage: ./list-worktrees.sh

set -e

PROJECT_ROOT="$(git rev-parse --show-toplevel)"

# Source logging utilities
source "$PROJECT_ROOT/scripts/common/logging.sh"

# Error trap to log failures
trap 'log_script_end "list-worktrees.sh" "false"' ERR

# Log script start
log_script_start "list-worktrees.sh" "$*"
log_operation "list-worktrees" ""

# Check if we're in a git repository
if ! git rev-parse --git-dir >/dev/null 2>&1; then
  echo "Error: Not in a git repository"
  exit 1
fi

echo "Current git worktrees:"
echo "====================="
git worktree list

echo ""
echo "Worktree status:"
echo "================"

# Check for any task-related worktrees
TASK_WORKTREES=$(git worktree list | grep -E "(task-|epic-)" || true)

if [ -n "$TASK_WORKTREES" ]; then
  echo "Active task/epic worktrees found:"
  echo "$TASK_WORKTREES"
else
  echo "No active task/epic worktrees found"
fi

log_script_end "list-worktrees.sh" "true"
