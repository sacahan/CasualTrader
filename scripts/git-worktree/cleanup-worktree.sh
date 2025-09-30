#!/bin/bash
# Git Worktree Cleanup Script
# Usage: ./cleanup-worktree.sh <task-id> [--keep-branch]

# Disable strict error handling to allow graceful cleanup
# set -e

TASK_ID="$1"
KEEP_BRANCH="$2"
PROJECT_ROOT="$(git rev-parse --show-toplevel)"
WORKSPACE_DIR="$PROJECT_ROOT/workspaces/${TASK_ID}"
BRANCH_NAME="${TASK_ID}-feature"

# Source logging utilities
source "$PROJECT_ROOT/scripts/common/logging.sh"

# Error trap to log failures (modified for graceful cleanup)
cleanup_on_exit() {
  local exit_code=$?
  if [ $exit_code -ne 0 ]; then
    echo "Cleanup encountered issues but continuing..."
    log_script_end "cleanup-worktree.sh" "false"
  fi
}
trap cleanup_on_exit EXIT

# Log script start
log_script_start "cleanup-worktree.sh" "$*"

if [ -z "$TASK_ID" ]; then
  echo "Error: Task ID is required"
  echo "Usage: $0 <task-id> [--keep-branch]"
  log_error "cleanup-worktree: Task ID is required"
  exit 1
fi

log_operation "cleanup-worktree" "task_id=$TASK_ID, keep_branch=$KEEP_BRANCH"

# Check if we're in a git repository
if ! git rev-parse --git-dir >/dev/null 2>&1; then
  echo "Error: Not in a git repository"
  exit 1
fi

# Enhanced worktree cleanup with error handling
cleanup_worktree() {
  if [ ! -d "$WORKSPACE_DIR" ]; then
    echo "Warning: Workspace directory $WORKSPACE_DIR does not exist"
    return 0
  fi

  echo "Removing worktree at $WORKSPACE_DIR..."

  # First attempt: standard worktree removal
  if git worktree remove "$WORKSPACE_DIR" --force 2>/dev/null; then
    echo "Worktree removed successfully!"
    return 0
  fi

  # Second attempt: handle conflicts and retry
  echo "Standard removal failed, attempting conflict resolution..."

  # Clean up any conflicting checkouts
  git worktree prune 2>/dev/null || true

  # Try again with force
  if git worktree remove "$WORKSPACE_DIR" --force 2>/dev/null; then
    echo "Worktree removed successfully after conflict resolution!"
    return 0
  fi

  # Third attempt: manual cleanup
  echo "Git worktree removal failed, performing manual cleanup..."

  # Remove directory manually
  if [ -d "$WORKSPACE_DIR" ]; then
    rm -rf "$WORKSPACE_DIR" 2>/dev/null || {
      echo "Warning: Could not remove directory $WORKSPACE_DIR manually"
      echo "You may need to remove it manually: rm -rf $WORKSPACE_DIR"
    }
  fi

  # Clean up worktree references
  git worktree prune 2>/dev/null || true

  echo "Manual cleanup completed"
  return 0
}

cleanup_worktree

# Enhanced branch cleanup with error handling
cleanup_branch() {
  if [ "$KEEP_BRANCH" = "--keep-branch" ]; then
    echo "Keeping branch $BRANCH_NAME as requested"
    return 0
  fi

  if ! git show-ref --verify --quiet "refs/heads/$BRANCH_NAME"; then
    echo "Branch $BRANCH_NAME does not exist"
    return 0
  fi

  echo "Removing branch $BRANCH_NAME..."

  # Check if branch is currently checked out anywhere
  local current_branch=$(git branch --show-current 2>/dev/null || echo "")
  if [ "$current_branch" = "$BRANCH_NAME" ]; then
    echo "Cannot remove branch $BRANCH_NAME - currently checked out"
    echo "Switching to main branch..."
    if git checkout main 2>/dev/null; then
      echo "Switched to main branch"
    else
      echo "Warning: Could not switch to main branch, skipping branch removal"
      return 0
    fi
  fi

  # Check for worktree conflicts
  if git worktree list | grep -q "$BRANCH_NAME" 2>/dev/null; then
    echo "Warning: Branch $BRANCH_NAME still referenced in worktree, cleaning up..."
    git worktree prune 2>/dev/null || true
  fi

  # Attempt branch removal
  if git branch -D "$BRANCH_NAME" 2>/dev/null; then
    echo "Branch removed successfully!"
  else
    echo "Warning: Could not remove branch $BRANCH_NAME"
    echo "This might be because it's merged or has uncommitted changes"

    # Try force removal one more time
    if git branch -D "$BRANCH_NAME" --force 2>/dev/null; then
      echo "Branch force-removed successfully!"
    else
      echo "Branch removal failed - you may need to remove it manually later"
      echo "Command: git branch -D $BRANCH_NAME"
    fi
  fi
}

cleanup_branch

echo "Cleanup completed!"

log_script_end "cleanup-worktree.sh" "true"
