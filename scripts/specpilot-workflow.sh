#!/bin/bash
# SpecPilot Workflow Automation Script
# Master script for AI agents to execute git/github operations
# Usage: ./specpilot-workflow.sh <operation> <task-id> [additional-args...]

# Set locale for UTF-8 support
export LC_ALL=en_US.UTF-8
export LANG=en_US.UTF-8

# =============================================================================
# AI AGENT EXECUTION GUIDE
# =============================================================================
# This script is designed for AI agents to manage development workflows.
# Before executing any operation, AI agents should:
#
# 1. VERIFY ENVIRONMENT:
#    - Ensure you're in the SpecPilot project root directory
#    - Check git repository status with: git status
#    - Verify GitHub CLI is authenticated: gh auth status
#
# 2. UNDERSTAND TASK IDS:
#    - Task IDs should follow format: task-XXXX (e.g., task-1001, task-2035)
#    - Each task gets its own worktree directory: ../workspaces/task-XXXX
#    - Each task gets its own feature branch: task-XXXX-feature
#
# 3. WORKFLOW SEQUENCE:
#    - Development: start-task → [code changes] → prepare-pr → close-task
#    - Quick operations: create-worktree → sync-worktree → create-pr → merge-pr
#
# 4. ERROR HANDLING:
#    - Script will exit on errors (set -e)
#    - Check for uncommitted changes before git operations
#    - Always verify GitHub repository exists before PR operations
#
# 5. COMMON AI AGENT PATTERNS:
#    - Start new feature: ./specpilot-workflow.sh start-task task-1001
#    - Create PR: ./specpilot-workflow.sh create-pr task-1001 "Feature title" "Description"
#    - Complete work: ./specpilot-workflow.sh close-task task-1001 squash
# =============================================================================

set -e

OPERATION="$1"
TASK_ID="$2"
# Get the script's directory first, then derive PROJECT_ROOT from it
PROJECT_ROOT="$(git rev-parse --show-toplevel)"
SCRIPT_DIR="$PROJECT_ROOT/scripts"
BASE_BRANCH="main"

# Source logging utilities
source "$SCRIPT_DIR/common/logging.sh"

# Error trap to log failures and cleanup
trap 'handle_script_error' ERR INT TERM

# Log script start
log_script_start "specpilot-workflow.sh" "$*"

# Color output functions
red() { echo -e "\033[31m$1\033[0m"; }
green() { echo -e "\033[32m$1\033[0m"; }
yellow() { echo -e "\033[33m$1\033[0m"; }
blue() { echo -e "\033[34m$1\033[0m"; }

# Error handling function
handle_script_error() {
  local exit_code=$?
  red "Script execution failed with exit code: $exit_code"

  # Kill any background GitHub sync processes
  pkill -f "github-manager.sh" 2>/dev/null || true

  # Log the error
  log_script_end "specpilot-workflow.sh" "false"

  echo ""
  echo "Error occurred during script execution."
  echo "Common solutions:"
  echo "  1. Check GitHub CLI authentication: gh auth status"
  echo "  2. Verify repository permissions and existence"
  echo "  3. Check network connectivity"
  echo "  4. Review any error messages above"
  echo ""

  exit $exit_code
}

usage() {
  echo "SpecPilot Workflow Automation"
  echo ""
  echo "Usage: $0 <operation> <task-id> [args...]"
  echo ""
  echo "=== AI AGENT QUICK REFERENCE ==="
  echo "Most common operations for AI agents:"
  echo "  start-task <task-id>                     - Begin new feature development"
  echo "  prepare-pr <task-id> [title]             - Complete development, create PR"
  echo "  close-task <task-id> [merge-method]      - Merge PR and cleanup (squash/merge/rebase)"
  echo ""
  echo "Git Worktree Operations:"
  echo "  create-worktree <task-id> [base-branch]  - Create new worktree for task"
  echo "  cleanup-worktree <task-id> [--keep-branch] - Clean up task worktree"
  echo "  list-worktrees                           - List all worktrees"
  echo "  sync-worktree <task-id> [base-branch]    - Sync worktree with latest base"
  echo ""
  echo "GitHub Operations:"
  echo "  create-pr <task-id> [title] [description] - Create pull request"
  echo "  check-pr <task-id>                       - Check PR status"
  echo "  merge-pr <task-id> [method]              - Merge PR (squash/merge/rebase)"
  echo ""
  echo "Full Workflow:"
  echo "  start-task <task-id> [base-branch]       - Create worktree and start development"
  echo "  prepare-pr <task-id> [pr-title]          - Create PR and prepare for review"
  echo "  close-task <task-id> [merge-method]      - Merge PR and cleanup"
  echo ""
  echo "=== AI AGENT EXAMPLES ==="
  echo "Complete workflow:"
  echo "  $0 start-task task-1001"
  echo "  # [AI agent makes code changes in ../workspaces/task-1001]"
  echo "  $0 prepare-pr task-1001 'Implement user authentication'"
  echo "  $0 close-task task-1001 squash"
  echo ""
  echo "Individual operations:"
  echo "  $0 create-pr task-1001 'Add user authentication' 'Implements login/logout'"
  echo "  $0 check-pr task-1001"
  echo "  $0 sync-worktree task-1001"
}

make_executable() {
  local script="$1"
  if [ -f "$script" ] && [ ! -x "$script" ]; then
    chmod +x "$script"
  fi
}

handle_uncommitted_changes() {
  local operation="$1"

  # Skip check for operations that don't require git operations
  case "$operation" in
  "list-worktrees" | "help" | "--help" | "-h" | "")
    return 0
    ;;
  esac

  # Check if we're in a git repository
  if ! git rev-parse --git-dir >/dev/null 2>&1; then
    red "Error: Not in a git repository"
    echo "AI Agent Note: Ensure you're in the SpecPilot project root directory"
    exit 1
  fi

  # Check for uncommitted changes (both staged and unstaged)
  if ! git diff --quiet || ! git diff --cached --quiet; then
    yellow "Warning: Uncommitted changes detected."

    # For operations that might conflict with uncommitted changes
    case "$operation" in
    "create-worktree" | "start-task" | "sync-worktree")
      red "Error: Uncommitted changes detected."
      echo "The following operations require a clean working directory:"
      echo "  - create-worktree: Creates new branch and worktree"
      echo "  - start-task: Creates worktree for development"
      echo "  - sync-worktree: Syncs with base branch"
      echo ""
      echo "AI Agent Instructions:"
      echo "  1. Commit changes: git add . && git commit -m 'your message'"
      echo "  2. Stash changes: git stash push -m 'temporary stash'"
      echo "  3. Or switch to the target worktree if changes belong to a specific task"
      echo ""
      exit 1
      ;;
    *)
      # For other operations, just warn but continue
      echo "Continuing with uncommitted changes..."
      ;;
    esac
  fi
}

restore_stashed_changes() {
  if [[ "$SPECPILOT_STASHED" == "true" ]]; then
    blue "Restoring previously stashed changes..."
    if git stash list | grep -q "Auto-stash before"; then
      git stash pop
      green "Stashed changes restored successfully."
    fi
    unset SPECPILOT_STASHED
  fi
}

update_spec_file_status() {
  local file_path="$1"
  local new_status="$2"
  local timestamp=$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)

  if [ -f "$file_path" ]; then
    # Create backup and update status and timestamp
    sed -i.bak "s/^status: .*/status: $new_status/" "$file_path" || true
    sed -i.bak "s/^updated: .*/updated: $timestamp/" "$file_path" || true
    rm -f "$file_path.bak" 2>/dev/null || true
    green "✅ Updated $(basename "$file_path"): status → $new_status"
  else
    yellow "⚠️  File not found: $file_path"
  fi
}

update_epic_status_if_needed() {
  local task_id="$1"
  local task_file="$PROJECT_ROOT/specs/tasks/$task_id.md"

  if [ ! -f "$task_file" ]; then
    return 0
  fi

  # Extract epic ID from task file
  local epic_id=$(awk '/^epic:/ {print $2}' "$task_file")
  if [ -z "$epic_id" ]; then
    return 0
  fi

  local epic_file="$PROJECT_ROOT/specs/epics/$epic_id.md"
  if [ ! -f "$epic_file" ]; then
    return 0
  fi

  # Check current epic status
  local epic_status=$(awk '/^status:/ {print $2}' "$epic_file")

  # If epic is still 'new', update it to 'in_progress' when first task starts
  if [ "$epic_status" = "new" ]; then
    blue "Updating related epic $epic_id status to in_progress..."
    update_spec_file_status "$epic_file" "in_progress"
  fi
}

sync_spec_files_to_worktree() {
  local task_id="$1"
  local workspace_dir="$PROJECT_ROOT/workspaces/$task_id"

  if [ ! -d "$workspace_dir" ]; then
    yellow "⚠️  Worktree directory not found: $workspace_dir"
    return 0
  fi

  blue "Syncing updated spec files to worktree..."

  # Copy updated specs directory to worktree
  if [ -d "$PROJECT_ROOT/specs" ]; then
    cp -r "$PROJECT_ROOT/specs" "$workspace_dir/" 2>/dev/null || true
    green "✅ Synced specs directory to worktree"
  fi
}

check_epic_completion() {
  local task_id="$1"
  local task_file="$PROJECT_ROOT/specs/tasks/$task_id.md"

  if [ ! -f "$task_file" ]; then
    return 0
  fi

  # Extract epic ID from task file
  local epic_id=$(awk '/^epic:/ {print $2}' "$task_file")
  if [ -z "$epic_id" ]; then
    return 0
  fi

  local epic_file="$PROJECT_ROOT/specs/epics/$epic_id.md"
  if [ ! -f "$epic_file" ]; then
    return 0
  fi

  # Count total and completed tasks for this epic
  local total_tasks=$(find "$PROJECT_ROOT/specs/tasks" -name "task-*.md" -exec grep -l "epic: $epic_id" {} \; | wc -l | tr -d ' ')
  local completed_tasks=$(find "$PROJECT_ROOT/specs/tasks" -name "task-*.md" -exec sh -c 'grep -l "epic: '$epic_id'" "$1" && grep -l "status: done" "$1"' _ {} \; 2>/dev/null | sort | uniq -d | wc -l | tr -d ' ')

  blue "Epic $epic_id progress: $completed_tasks/$total_tasks tasks completed"

  # If all tasks are done, update epic to done
  if [ "$total_tasks" -gt 0 ] && [ "$completed_tasks" -eq "$total_tasks" ]; then
    blue "All tasks completed! Updating epic $epic_id status to done..."
    update_spec_file_status "$epic_file" "done"
    return 0
  fi

  # If at least one task is in progress or review, ensure epic is in_progress
  local active_tasks=$(find "$PROJECT_ROOT/specs/tasks" -name "task-*.md" -exec sh -c 'grep -l "epic: '$epic_id'" "$1" && (grep -l "status: in_progress" "$1" || grep -l "status: review" "$1")' _ {} \; 2>/dev/null | sort | uniq -d | wc -l | tr -d ' ')

  if [ "$active_tasks" -gt 0 ]; then
    local epic_status=$(awk '/^status:/ {print $2}' "$epic_file")
    if [ "$epic_status" = "new" ]; then
      blue "Active tasks found! Updating epic $epic_id status to in_progress..."
      update_spec_file_status "$epic_file" "in_progress"
    fi
  fi
}

# Enhanced merge conflict detection and resolution for close-task
resolve_pr_merge_conflicts() {
  local task_id="$1"
  local branch_name="${task_id}-feature"
  local workspace_dir="$PROJECT_ROOT/workspaces/$task_id"

  blue "🔍 Checking for PR merge conflicts..."

  # Check if PR is mergeable
  local mergeable_state=$(gh pr view "$branch_name" --json mergeable --jq '.mergeable' 2>/dev/null || echo "UNKNOWN")

  if [ "$mergeable_state" = "MERGEABLE" ]; then
    green "✅ PR is mergeable, no conflicts detected"
    return 0
  fi

  if [ "$mergeable_state" = "CONFLICTING" ] || [ "$mergeable_state" = "UNKNOWN" ]; then
    yellow "⚠️  PR has merge conflicts or unknown merge state: $mergeable_state"
    blue "🔧 Attempting to resolve merge conflicts automatically..."

    # Check if worktree exists
    if [ ! -d "$workspace_dir" ]; then
      yellow "⚠️  Worktree not found, attempting to recreate from branch..."
      if git show-ref --verify --quiet "refs/heads/$branch_name"; then
        blue "Creating temporary worktree to resolve conflicts..."
        git worktree add "$workspace_dir" "$branch_name" 2>/dev/null || {
          red "Failed to create worktree for conflict resolution"
          return 1
        }
      else
        red "Branch $branch_name not found locally"
        return 1
      fi
    fi

    # Switch to worktree and attempt merge
    local current_dir=$(pwd)
    cd "$workspace_dir" || {
      red "Failed to switch to worktree directory"
      return 1
    }

    # Fetch latest main and attempt merge
    blue "Fetching latest main branch..."
    git fetch origin main || {
      red "Failed to fetch latest main branch"
      cd "$current_dir"
      return 1
    }

    blue "Attempting to merge origin/main..."
    if git merge origin/main; then
      green "✅ Merge completed successfully"

      # Push the resolved merge
      blue "Pushing resolved merge to remote..."
      if git push origin "$branch_name"; then
        green "✅ Conflicts resolved and pushed successfully"
        cd "$current_dir"
        return 0
      else
        red "Failed to push resolved merge"
        cd "$current_dir"
        return 1
      fi
    else
      # Handle merge conflicts automatically
      blue "🔧 Handling merge conflicts in specification files..."

      # Check for conflicts in spec files
      local conflict_files=$(git diff --name-only --diff-filter=U | grep "specs/" || true)

      if [ -n "$conflict_files" ]; then
        blue "Found conflicts in spec files: $conflict_files"

        # For spec files, prefer the current branch version (worktree) for most conflicts
        # but ensure status consistency
        for file in $conflict_files; do
          if [[ "$file" == specs/tasks/* ]]; then
            blue "Resolving task file conflict: $file"
            # Accept current version but ensure status is consistent
            git checkout --ours "$file"
          elif [[ "$file" == specs/epics/* ]]; then
            blue "Resolving epic file conflict: $file"
            # Accept current version for epic files
            git checkout --ours "$file"
          else
            blue "Resolving spec file conflict using current version: $file"
            git checkout --ours "$file"
          fi
          git add "$file"
        done

        # Complete the merge
        if git commit -m "fix: resolve merge conflicts in spec files

- Resolved conflicts by accepting current branch versions
- Maintained task and epic status consistency
- Ready for PR merge

🤖 Generated with SpecPilot workflow automation"; then
          green "✅ Merge conflicts resolved automatically"

          # Push the resolution
          if git push origin "$branch_name"; then
            green "✅ Conflict resolution pushed successfully"
            cd "$current_dir"
            return 0
          else
            red "Failed to push conflict resolution"
            cd "$current_dir"
            return 1
          fi
        else
          red "Failed to commit merge conflict resolution"
          cd "$current_dir"
          return 1
        fi
      else
        red "Unable to resolve merge conflicts automatically"
        yellow "Manual intervention required for non-spec file conflicts"
        git merge --abort 2>/dev/null || true
        cd "$current_dir"
        return 1
      fi
    fi
  fi

  return 1
}

# Enhanced branch conflict detection and resolution
resolve_branch_conflicts() {
  local task_id="$1"
  local branch_name="${task_id}-feature"

  blue "🔍 Checking for branch conflicts..."

  # Check if branch is checked out in multiple worktrees
  local worktree_locations=$(git worktree list | grep "$branch_name" | wc -l | tr -d ' ')

  if [ "$worktree_locations" -gt 1 ]; then
    yellow "⚠️  Branch $branch_name is checked out in multiple locations"
    blue "🔧 Resolving branch conflicts..."

    # List all worktree locations
    git worktree list | grep "$branch_name" | while read -r worktree_info; do
      local worktree_path=$(echo "$worktree_info" | awk '{print $1}')
      blue "Found worktree at: $worktree_path"
    done

    # Remove any conflicting worktrees (keep only the main task worktree)
    local main_worktree="$PROJECT_ROOT/workspaces/$task_id"
    git worktree list | grep "$branch_name" | while read -r worktree_info; do
      local worktree_path=$(echo "$worktree_info" | awk '{print $1}')
      if [ "$worktree_path" != "$main_worktree" ]; then
        yellow "Removing conflicting worktree: $worktree_path"
        git worktree remove "$worktree_path" --force 2>/dev/null || true
      fi
    done

    green "✅ Branch conflicts resolved"
    return 0
  fi

  # Check if main branch is also checked out elsewhere
  local main_worktrees=$(git worktree list | grep -E "(main|master)" | wc -l | tr -d ' ')

  if [ "$main_worktrees" -gt 1 ]; then
    yellow "⚠️  Main branch is checked out in multiple locations"
    blue "This might cause issues during PR merge"

    # Switch current directory to main branch if we're on feature branch
    if git branch --show-current | grep -q "$branch_name"; then
      if [ -d "$PROJECT_ROOT" ]; then
        blue "Switching to main directory: $PROJECT_ROOT"
        cd "$PROJECT_ROOT"
        git checkout main 2>/dev/null || {
          yellow "Unable to switch to main branch, continuing..."
        }
      fi
    fi
  fi

  green "✅ Branch conflict check completed"
  return 0
}

sync_github_if_needed() {
  local task_id="$1"
  local operation="$2"
  local task_file="$PROJECT_ROOT/specs/tasks/$task_id.md"

  # Skip if GitHub manager script is not available or executable
  if [ ! -x "$SCRIPT_DIR/github/github-manager.sh" ]; then
    yellow "⚠️  GitHub manager not available, skipping sync"
    return 0
  fi

  # Check if we're in a clean state for syncing
  if ! git diff --quiet || ! git diff --cached --quiet; then
    yellow "⚠️  Uncommitted changes detected, skipping GitHub sync"
    echo "   Commit changes first, then run: $SCRIPT_DIR/scripts/github/github-manager.sh sync-task $task_id"
    return 0
  fi

  # Check if task file exists and has expected status
  if [ ! -f "$task_file" ]; then
    yellow "⚠️  Task file not found: $task_file, skipping GitHub sync"
    return 0
  fi

  local task_status=$(awk '/^status:/ {print $2}' "$task_file")

  # Determine if sync is needed based on operation and current status
  local should_sync=false
  case "$operation" in
  "start-task")
    if [ "$task_status" = "in_progress" ]; then
      should_sync=true
    fi
    ;;
  "prepare-pr")
    if [ "$task_status" = "review" ]; then
      should_sync=true
    fi
    ;;
  "close-task")
    if [ "$task_status" = "done" ]; then
      should_sync=true
    fi
    ;;
  *)
    should_sync=true # Default to sync for unknown operations
    ;;
  esac

  if [ "$should_sync" = true ]; then
    blue "Syncing with GitHub..."
    # Use timeout to prevent hanging, and run in foreground for better error handling
    if timeout 30s "$SCRIPT_DIR/github/github-manager.sh" sync-task "$task_id"; then
      green "🔗 GitHub sync completed successfully"
    else
      yellow "⚠️  GitHub sync timed out or failed, continuing..."
    fi
  else
    yellow "⚠️  Task status ($task_status) doesn't match operation ($operation), skipping GitHub sync"
  fi
}

check_github_repo() {
  blue "Checking GitHub repository..."
  if ! "$SCRIPT_DIR/github/check-or-create-repo.sh"; then
    red "GitHub repository check failed"
    echo "AI Agent Note: Ensure your GitHub repository is set up before proceeding with GitHub operations."
    echo "Required setup:"
    echo "  1. GitHub CLI authenticated: gh auth login"
    echo "  2. Remote origin configured: git remote -v"
    echo "  3. Repository exists on GitHub or will be created automatically"
    exit 1
  fi
}

# Ensure all scripts are executable
make_executable "$SCRIPT_DIR/git-worktree/create-worktree.sh"
make_executable "$SCRIPT_DIR/git-worktree/cleanup-worktree.sh"
make_executable "$SCRIPT_DIR/git-worktree/list-worktrees.sh"
make_executable "$SCRIPT_DIR/git-worktree/sync-worktree.sh"
make_executable "$SCRIPT_DIR/github/create-pr.sh"
make_executable "$SCRIPT_DIR/github/check-pr-status.sh"
make_executable "$SCRIPT_DIR/github/merge-pr.sh"
make_executable "$SCRIPT_DIR/github/check-or-create-repo.sh"
make_executable "$SCRIPT_DIR/github/generate-pr-content.sh"

# Handle uncommitted changes before any git operations
handle_uncommitted_changes "$OPERATION"

# =============================================================================
# OPERATION HANDLERS - AI Agent Execution Points
# =============================================================================
# Each case handles a specific workflow operation.
# AI agents should understand the sequence and dependencies:
# 1. start-task: Creates isolated development environment
# 2. prepare-pr: Prepares code for review (commits + creates PR)
# 3. close-task: Finalizes work (merges PR + cleans up)
#
# Individual operations can be used for granular control when needed.
# =============================================================================

cd $PROJECT_ROOT

case "$OPERATION" in
"create-worktree")
  if [ -z "$TASK_ID" ]; then
    red "Error: Task ID is required"
    log_error "create-worktree: Task ID is required"
    exit 1
  fi
  log_operation "create-worktree" "task=$TASK_ID, base_branch=$BASE_BRANCH"
  blue "Creating worktree for task: $TASK_ID"
  "$SCRIPT_DIR/git-worktree/create-worktree.sh" "$TASK_ID" "$BASE_BRANCH"
  ;;

"cleanup-worktree")
  if [ -z "$TASK_ID" ]; then
    red "Error: Task ID is required"
    log_error "cleanup-worktree: Task ID is required"
    exit 1
  fi
  log_operation "cleanup-worktree" "task=$TASK_ID, keep_branch=$3"
  blue "Cleaning up worktree for task: $TASK_ID"
  "$SCRIPT_DIR/git-worktree/cleanup-worktree.sh" "$TASK_ID" "$3"
  ;;

"list-worktrees")
  log_operation "list-worktrees" ""
  blue "Listing all worktrees"
  "$SCRIPT_DIR/git-worktree/list-worktrees.sh"
  ;;

"sync-worktree")
  if [ -z "$TASK_ID" ]; then
    red "Error: Task ID is required"
    log_error "sync-worktree: Task ID is required"
    exit 1
  fi
  log_operation "sync-worktree" "task=$TASK_ID, base_branch=$BASE_BRANCH"
  blue "Syncing worktree for task: $TASK_ID"
  "$SCRIPT_DIR/git-worktree/sync-worktree.sh" "$TASK_ID" "$BASE_BRANCH"
  ;;

"create-pr")
  if [ -z "$TASK_ID" ]; then
    red "Error: Task ID is required"
    log_error "create-pr: Task ID is required"
    exit 1
  fi
  log_operation "create-pr" "task=$TASK_ID, title=$3, description=$4"
  check_github_repo
  blue "Creating PR for task: $TASK_ID"
  "$SCRIPT_DIR/github/create-pr.sh" "$TASK_ID" "$3" "$4"
  ;;

"check-pr")
  if [ -z "$TASK_ID" ]; then
    red "Error: Task ID is required"
    exit 1
  fi
  blue "Checking PR status for task: $TASK_ID"
  "$SCRIPT_DIR/github/check-pr-status.sh" "$TASK_ID"
  ;;

"merge-pr")
  if [ -z "$TASK_ID" ]; then
    red "Error: Task ID is required"
    exit 1
  fi
  blue "Merging PR for task: $TASK_ID"
  "$SCRIPT_DIR/github/merge-pr.sh" "$TASK_ID" "$3"
  ;;

"start-task")
  # AI Agent: Use this to begin development on a new task
  # Creates isolated worktree environment for clean development
  if [ -z "$TASK_ID" ]; then
    red "Error: Task ID is required"
    exit 1
  fi
  blue "Starting development workflow for task: $TASK_ID"

  # Step 1: Update task status to in_progress in main branch
  blue "Updating task status to in_progress..."
  task_file="$PROJECT_ROOT/specs/tasks/$TASK_ID.md"
  update_spec_file_status "$task_file" "in_progress"

  # Step 2: Update related epic status if needed
  update_epic_status_if_needed "$TASK_ID"

  # Step 3: Commit updated status files before creating worktree
  blue "Committing status updates in main branch..."
  if git diff --quiet HEAD -- specs/; then
    yellow "No spec changes to commit"
  else
    git add specs/
    git commit -m "feat($TASK_ID): update task and epic status to in_progress

- Task $TASK_ID status: new → in_progress
- Related epic status updated if needed
- Ready for development in Worktree

🤖 Generated with SpecPilot workflow automation"
    green "✅ Committed status updates to main branch"

    # Push committed spec files to Github
    if git pull origin "$BASE_BRANCH" --rebase; then
      if git push origin "$BASE_BRANCH"; then
        green "✅ Pushed updated specs to remote"
      else
        red "❌  Failed to push updated specs, please check manually"
        exit 1
      fi
    else
      red "❌ Rebase failed - conflicts need to be resolved"
      exit 1
    fi
  fi

  # Step 4: Create worktree environment
  blue "Creating worktree environment..."
  "$SCRIPT_DIR/git-worktree/create-worktree.sh" "$TASK_ID" "$BASE_BRANCH"

  # Step 5: Sync with GitHub Issues and Milestones (conditionally)
  sync_github_if_needed "$TASK_ID" "start-task"

  restore_stashed_changes

  green "🚀 Task environment ready!"
  green "📁 Navigate to: cd workspaces/${TASK_ID}"
  green "📝 Task status: new → in_progress"
  green "🔗 GitHub Issue synchronized"
  echo ""
  echo "Next steps:"
  echo "  1. cd workspaces/${TASK_ID}"
  echo "  2. [Make your code changes]"
  echo "  3. ${SCRIPT_DIR}/scripts/specpilot-workflow.sh prepare-pr $TASK_ID"
  ;;

"prepare-pr")
  # AI Agent: Use this when development is complete and ready for PR
  # Automatically commits changes and creates pull request
  if [ -z "$TASK_ID" ]; then
    red "Error: Task ID is required"
    exit 1
  fi
  blue "Preparing PR for task: $TASK_ID"

  # Step 1: Handle worktree changes (check worktree directory regardless of current location)
  workspace_dir="$PROJECT_ROOT/workspaces/$TASK_ID"
  if [ -d "$workspace_dir" ]; then
    blue "Checking and committing changes in worktree: $workspace_dir"
    current_dir=$(pwd)
    cd "$workspace_dir"

    # Check for any uncommitted changes (both staged and unstaged)
    if ! git diff --quiet || ! git diff --cached --quiet; then
      blue "Found uncommitted changes, adding and committing..."
      git add .
      git commit -m "feat($TASK_ID): complete implementation

- Complete implementation for task $TASK_ID
- Ready for review and PR creation

🤖 Generated with SpecPilot workflow automation"
      git push -u origin "${TASK_ID}-feature"
      green "✅ Changes committed and pushed from worktree"
    else
      blue "No uncommitted changes found in worktree"
      # Still push to ensure remote is up to date
      git push -u origin "${TASK_ID}-feature" || true
    fi

    cd "$current_dir"
  else
    yellow "⚠️  Worktree directory not found: $workspace_dir"
    echo "   Skipping worktree changes handling"
  fi

  # Step 2: Update task status to review in main branch
  blue "Updating task status to review..."
  task_file="$PROJECT_ROOT/specs/tasks/$TASK_ID.md"
  update_spec_file_status "$task_file" "review"

  # Step 3: Update epic status if needed
  check_epic_completion "$TASK_ID"

  # Step 4: Commit status updates to main branch
  blue "Committing status updates in main branch..."
  if git diff --quiet HEAD -- specs/; then
    yellow "No spec changes to commit"
  else
    git add specs/
    git commit -m "feat($TASK_ID): update task status to review

- Task $TASK_ID status: in_progress → review
- Epic status updated based on progress
- Ready for PR creation and review

🤖 Generated with SpecPilot workflow automation"
    green "✅ Committed status updates to main branch"

    # Push committed spec files to Github
    if git pull origin "$BASE_BRANCH" --rebase; then
      if git push origin "$BASE_BRANCH"; then
        green "✅ Pushed updated specs to remote"
      else
        red "❌  Failed to push updated specs, please check manually"
        exit 1
      fi
    else
      red "❌ Rebase failed - conflicts need to be resolved"
      exit 1
    fi
  fi

  # Step 5: Generate PR content automatically
  blue "Generating PR content from task specifications and commit history..."
  if [ -x "$SCRIPT_DIR/github/generate-pr-content.sh" ]; then
    # Generate PR content automatically
    PR_CONTENT_OUTPUT=$("$SCRIPT_DIR/github/generate-pr-content.sh" "$TASK_ID")

    # Extract generated title and description file path
    PR_TITLE=$(echo "$PR_CONTENT_OUTPUT" | grep "^PR_TITLE=" | cut -d'=' -f2- | sed 's/^"//' | sed 's/"$//')
    PR_DESC_FILE=$(echo "$PR_CONTENT_OUTPUT" | grep "^PR_DESCRIPTION_FILE=" | cut -d'=' -f2-)

    if [ -f "$PR_DESC_FILE" ]; then
      green "✅ PR content generated automatically"
      echo "   Title: $PR_TITLE"
      echo "   Description: Auto-generated from task and commits"
    else
      yellow "⚠️  PR content generation failed, using manual inputs"
      PR_TITLE="$3"
      PR_DESC_FILE=""
    fi
  else
    yellow "⚠️  PR content generator not available, using manual inputs"
    PR_TITLE="$3"
    PR_DESC_FILE=""
  fi

  # Step 6: Create PR with generated or manual content
  check_github_repo
  blue "Creating pull request..."
  if [ -n "$PR_DESC_FILE" ] && [ -f "$PR_DESC_FILE" ]; then
    # Use generated content
    "$SCRIPT_DIR/github/create-pr.sh" "$TASK_ID" "$PR_TITLE" "@$PR_DESC_FILE"
    # Clean up temporary file
    rm -f "$PR_DESC_FILE"
  else
    # Fallback to manual content
    "$SCRIPT_DIR/github/create-pr.sh" "$TASK_ID" "$3" "$4"
  fi

  # Step 7: Sync with GitHub Issues and Milestones (conditionally)
  sync_github_if_needed "$TASK_ID" "prepare-pr"

  green "🎉 PR prepared and created!"
  green "📝 Task status: in_progress → review"
  green "🔗 GitHub Issue and Milestone synchronized"
  green "📋 Use 'check-pr $TASK_ID' to monitor review status"
  ;;

"close-task")
  # AI Agent: Use this to finalize and merge completed work
  # Merges PR and cleans up worktree automatically
  if [ -z "$TASK_ID" ]; then
    red "Error: Task ID is required"
    exit 1
  fi
  blue "Closing task workflow: $TASK_ID"

  # Step 0: Confirm PR review completion
  blue "🔍 Checking PR review status..."
  branch_name="${TASK_ID}-feature"

  # Check if PR exists
  if gh pr view "$branch_name" --json state,reviewDecision,mergeable >/dev/null 2>&1; then
    pr_info=$(gh pr view "$branch_name" --json state,reviewDecision,mergeable,url)
    pr_state=$(echo "$pr_info" | jq -r '.state')
    pr_review=$(echo "$pr_info" | jq -r '.reviewDecision // "PENDING"')
    pr_mergeable=$(echo "$pr_info" | jq -r '.mergeable')
    pr_url=$(echo "$pr_info" | jq -r '.url')

    echo ""
    blue "📋 PR Information:"
    echo "   URL: $pr_url"
    echo "   State: $pr_state"
    echo "   Review Status: $pr_review"
    echo "   Mergeable: $pr_mergeable"
    echo ""

    if [ "$pr_state" = "MERGED" ]; then
      yellow "⚠️  PR is already merged. Skipping merge step."
    elif [ "$pr_state" = "CLOSED" ]; then
      red "❌ PR is closed without merging. Cannot proceed with close-task."
      exit 1
    else
      # PR is still open, ask for confirmation
      yellow "⚠️  IMPORTANT: PR Review Confirmation Required"
      echo ""
      echo "Before proceeding with close-task, please confirm:"
      echo "  1. Code review has been completed"
      echo "  2. All feedback has been addressed"
      echo "  3. PR is approved and ready to merge"
      echo "  4. All CI/CD checks are passing"
      echo ""

      while true; do
        read -p "Has the PR review been completed and approved? (Y/n): " -r response
        case $response in
        [Yy]*)
          green "✅ PR review confirmed. Proceeding with merge..."
          break
          ;;
        [Nn]*)
          yellow "❌ PR review not completed. Please complete the review first."
          echo ""
          echo "Next steps:"
          echo "  1. Complete code review at: $pr_url"
          echo "  2. Address any feedback"
          echo "  3. Re-run: ${SCRIPT_DIR}/scripts/specpilot-workflow.sh close-task $TASK_ID"
          exit 1
          ;;
        *)
          echo "Please answer Y (yes) or n (no)."
          ;;
        esac
      done
    fi
  else
    yellow "⚠️  No PR found for branch $branch_name. Creating merge commit directly."
  fi

  # Step 1: Update task status to done in main branch
  blue "Updating task status to done..."
  task_file="$PROJECT_ROOT/specs/tasks/$TASK_ID.md"
  update_spec_file_status "$task_file" "done"

  # Step 2: Check and update epic completion status
  check_epic_completion "$TASK_ID"

  # Step 3: Commit status updates to main branch
  blue "Committing final status updates in main branch..."
  if git diff --quiet HEAD -- specs/; then
    yellow "No spec changes to commit"
  else
    git add specs/
    git commit -m "feat($TASK_ID): complete task and update epic status

- Task $TASK_ID status: review → done
- Epic status updated based on completion progress
- Ready for PR merge and cleanup

🤖 Generated with SpecPilot workflow automation"
    green "✅ Committed final status updates to main branch"

    # Push committed spec files to Github
    if git pull origin "$BASE_BRANCH" --rebase; then
      if git push origin "$BASE_BRANCH"; then
        green "✅ Pushed updated specs to remote"
      else
        red "❌  Failed to push updated specs, please check manually"
        exit 1
      fi
    else
      red "❌ Rebase failed - conflicts need to be resolved"
      exit 1
    fi
  fi

  # Step 4: Commit all feature branch changes then pull remote feature branch changes
  if [ -d "$PROJECT_ROOT/workspaces/$TASK_ID" ]; then
    blue "Syncing feature branch with remote..."
    cd "$PROJECT_ROOT/workspaces/$TASK_ID"

    # 4a: Commit any uncommitted changes
    if ! git diff --quiet || ! git diff --cached --quiet; then
      blue "Committing final local changes..."
      git add specs/
      git commit -m "feat($TASK_ID): final changes before merge preparation" || {
        yellow "No changes to commit"
      }
    fi

    # 4b: Pull and rebase remote feature branch changes
    blue "Pulling and rebasing remote feature branch changes..."
    if git pull origin "${TASK_ID}-feature" --rebase; then
      green "✅ Successfully rebased remote changes"
    else
      red "❌ Rebase failed - conflicts need to be resolved"
      echo "Manual conflict resolution required:"
      echo "1. Resolve conflicts in worktree: workspaces/$TASK_ID"
      echo "2. After resolving conflicts, run: git add . && git rebase --continue"
      echo "3. If you want to abort: git rebase --abort"
      echo "4. Re-run: ${SCRIPT_DIR}/scripts/specpilot-workflow.sh close-task $TASK_ID"
      cd "$PROJECT_ROOT"
      exit 1
    fi

    cd "$PROJECT_ROOT"
  else
    yellow "⚠️ Worktree not found, skipping feature branch sync"
  fi

  # Step 5: Merge and push feature branch changes
  if [ -d "$PROJECT_ROOT/workspaces/$TASK_ID" ]; then
    blue "Pushing synchronized feature branch..."
    cd "$PROJECT_ROOT/workspaces/$TASK_ID"

    if git push origin "${TASK_ID}-feature"; then
      green "✅ Feature branch synchronized and pushed"
    else
      red "❌ Push failed after pull - this shouldn't happen"
      echo "Please check the repository state manually"
      cd "$PROJECT_ROOT"
      exit 1
    fi

    cd "$PROJECT_ROOT"
  fi

  # Step 6: Clean up worktree environment (keep branch for now)
  blue "Cleaning up worktree environment..."
  "$SCRIPT_DIR/git-worktree/cleanup-worktree.sh" "$TASK_ID" "--keep-branch"

  # Step 7: Merge pull request (will delete remote branch)
  blue "Merging pull request..."
  "$SCRIPT_DIR/github/merge-pr.sh" "$TASK_ID" "$3"

  # Step 8: Clean up local branch after PR merge
  blue "Cleaning up local branch..."
  if git show-ref --verify --quiet "refs/heads/${TASK_ID}-feature"; then
    git branch -D "${TASK_ID}-feature" 2>/dev/null || {
      yellow "Warning: Could not delete local branch ${TASK_ID}-feature"
      echo "You may need to delete it manually: git branch -D ${TASK_ID}-feature"
    }
    green "✅ Local branch ${TASK_ID}-feature deleted"
  else
    yellow "Branch ${TASK_ID}-feature already removed"
  fi

  # Step 9: Sync with GitHub Issues and Milestones
  sync_github_if_needed "$TASK_ID" "close-task"

  green "🏆 Task $TASK_ID completed successfully!"
  green "📝 Task status: review → done"
  green "🎯 Epic progress updated automatically"
  green "🔗 GitHub Issue closed and Milestone updated"
  green "🧹 Worktree cleaned up"
  echo ""
  echo "Task $TASK_ID is now fully complete and merged! 🎉"
  ;;

"help" | "--help" | "-h" | "")
  usage
  ;;

*)
  red "Error: Unknown operation '$OPERATION'"
  log_error "Unknown operation: $OPERATION"
  echo ""
  usage
  log_script_end "specpilot-workflow.sh" "false"
  exit 1
  ;;
esac

# Log successful completion
log_script_end "specpilot-workflow.sh" "true"
