#!/bin/bash
# GitHub Pull Request Merge Script
# Usage: ./merge-pr.sh <task-id> [merge-method]

set -e

TASK_ID="$1"
MERGE_METHOD="${2:-squash}" # squash, merge, or rebase
BRANCH_NAME="${TASK_ID}-feature"

if [ -z "$TASK_ID" ]; then
	echo "Error: Task ID is required"
	echo "Usage: $0 <task-id> [merge-method]"
	echo "Merge methods: squash (default), merge, rebase"
	exit 1
fi

# Validate merge method
if [[ ! "$MERGE_METHOD" =~ ^(squash|merge|rebase)$ ]]; then
	echo "Error: Invalid merge method '$MERGE_METHOD'"
	echo "Valid options: squash, merge, rebase"
	exit 1
fi

# Check if gh CLI is installed
if ! command -v gh &>/dev/null; then
	echo "Error: GitHub CLI (gh) is not installed"
	echo "Please install it from https://cli.github.com/"
	exit 1
fi

echo "Merging PR for task: $TASK_ID"
echo "Branch: $BRANCH_NAME"
echo "Merge method: $MERGE_METHOD"
echo "=================================="

# Function to check PR status with retry mechanism
check_pr_status() {
	local max_attempts=3
	local attempt=1

	while [ $attempt -le $max_attempts ]; do
		echo "🔍 Checking PR status (attempt $attempt/$max_attempts)..."

		PR_JSON=$(gh pr view "$BRANCH_NAME" --json state,mergeable 2>/dev/null || echo "")

		if [ -z "$PR_JSON" ]; then
			echo "Error: No pull request found for branch $BRANCH_NAME"
			return 1
		fi

		STATE=$(echo "$PR_JSON" | jq -r '.state')
		MERGEABLE=$(echo "$PR_JSON" | jq -r '.mergeable // "UNKNOWN"')

		echo "   State: $STATE, Mergeable: $MERGEABLE"

		# If mergeable status is UNKNOWN, wait and retry (except on last attempt)
		if [ "$MERGEABLE" = "UNKNOWN" ] && [ $attempt -lt $max_attempts ]; then
			echo "   ⏳ Mergeable status is UNKNOWN, waiting 3 seconds before retry..."
			sleep 3
			attempt=$((attempt + 1))
		else
			break
		fi
	done

	return 0
}

# Check if PR exists and is ready to merge with retry
if ! check_pr_status; then
	exit 1
fi

if [ "$STATE" != "OPEN" ]; then
	echo "Error: Pull request is not open (current state: $STATE)"
	exit 1
fi

# Handle mergeable status
if [ "$MERGEABLE" = "MERGEABLE" ]; then
	echo "✅ PR is ready to merge"
elif [ "$MERGEABLE" = "UNKNOWN" ]; then
	echo "⚠️  Mergeable status is still UNKNOWN after retries"
	echo "This might be a temporary GitHub API issue. Attempting to merge anyway..."
	echo "If merge fails, please check for conflicts manually and retry."
elif [ "$MERGEABLE" = "CONFLICTING" ]; then
	echo "❌ Pull request has conflicts that need to be resolved"
	echo "Please resolve conflicts and push changes before merging"
	exit 1
else
	echo "⚠️  Unknown mergeable status: $MERGEABLE"
	echo "Proceeding with caution - merge may fail if there are actual issues"
fi

# Merge the PR
echo "Merging pull request..."
case "$MERGE_METHOD" in
"squash")
	gh pr merge "$BRANCH_NAME" --squash --delete-branch
	;;
"merge")
	gh pr merge "$BRANCH_NAME" --merge --delete-branch
	;;
"rebase")
	gh pr merge "$BRANCH_NAME" --rebase --delete-branch
	;;
esac

echo "Pull request merged successfully!"
echo "Branch $BRANCH_NAME has been deleted from remote"

# Optional: Clean up local worktree
echo ""
echo "To clean up local worktree, run:"
echo "  ${SCRIPT_DIR}/scripts/git-worktree/cleanup-worktree.sh $TASK_ID"
