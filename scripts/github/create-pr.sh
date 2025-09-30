#!/bin/bash
# GitHub Pull Request Creation Script
# Usage: ./create-pr.sh <task-id> [title] [description]

set -e

TASK_ID="$1"
PR_TITLE="$2"
PR_DESCRIPTION="$3"
BRANCH_NAME="${TASK_ID}-feature"

if [ -z "$TASK_ID" ]; then
  echo "Error: Task ID is required"
  echo "Usage: $0 <task-id> [title] [description]"
  exit 1
fi

# Check if we're in a git repository
if ! git rev-parse --git-dir >/dev/null 2>&1; then
  echo "Error: Not in a git repository"
  exit 1
fi

# Check if gh CLI is installed
if ! command -v gh &>/dev/null; then
  echo "Error: GitHub CLI (gh) is not installed"
  echo "Please install it from https://cli.github.com/"
  exit 1
fi

# Check if branch exists
if ! git show-ref --verify --quiet "refs/heads/$BRANCH_NAME"; then
  echo "Error: Branch $BRANCH_NAME does not exist"
  exit 1
fi

# Set default title and description if not provided
if [ -z "$PR_TITLE" ]; then
  PR_TITLE="feat: implement $TASK_ID"
fi

if [ -z "$PR_DESCRIPTION" ]; then
  PR_DESCRIPTION="Implements task $TASK_ID

## Changes
- TODO: Add specific changes made

## Testing
- TODO: Add testing details

## Notes
- Generated from SpecPilot task: $TASK_ID"
elif [[ "$PR_DESCRIPTION" == @* ]]; then
  # If description starts with @, treat it as a file path
  PR_DESC_FILE="${PR_DESCRIPTION#@}"
  if [ -f "$PR_DESC_FILE" ]; then
    echo "Reading PR description from file: $PR_DESC_FILE"
    PR_DESCRIPTION=$(cat "$PR_DESC_FILE")
  else
    echo "Warning: PR description file not found: $PR_DESC_FILE"
    echo "Using fallback description..."
    PR_DESCRIPTION="Implements task $TASK_ID

## Changes
- TODO: Add specific changes made

## Testing
- TODO: Add testing details

## Notes
- Generated from SpecPilot task: $TASK_ID"
  fi
fi

# Push branch to remote
echo "Pushing branch $BRANCH_NAME to remote..."
git push -u origin "$BRANCH_NAME"

# Create pull request
echo "Creating pull request..."
gh pr create \
  --title "$PR_TITLE" \
  --body "$PR_DESCRIPTION" \
  --head "$BRANCH_NAME" \
  --base main

echo "Pull request created successfully!"
echo "View it with: gh pr view $BRANCH_NAME"
