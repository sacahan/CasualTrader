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

# Check if PR exists and is ready to merge
PR_JSON=$(gh pr view "$BRANCH_NAME" --json state,mergeable 2>/dev/null || echo "")

if [ -z "$PR_JSON" ]; then
	echo "Error: No pull request found for branch $BRANCH_NAME"
	exit 1
fi

# Extract state and mergeable status separately to handle different data types
STATE=$(echo "$PR_JSON" | jq -r '.state')
MERGEABLE=$(echo "$PR_JSON" | jq -r '.mergeable // "UNKNOWN"')

if [ "$STATE" != "OPEN" ]; then
	echo "Error: Pull request is not open (current state: $STATE)"
	exit 1
fi

if [ "$MERGEABLE" != "MERGEABLE" ]; then
	echo "Error: Pull request is not mergeable (status: $MERGEABLE)"
	echo "Please resolve conflicts and ensure all checks pass"
	exit 1
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
