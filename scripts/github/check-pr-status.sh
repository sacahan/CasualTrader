#!/bin/bash
# GitHub Pull Request Status Check Script
# Usage: ./check-pr-status.sh <task-id>

set -e

TASK_ID="$1"
BRANCH_NAME="${TASK_ID}-feature"

if [ -z "$TASK_ID" ]; then
    echo "Error: Task ID is required"
    echo "Usage: $0 <task-id>"
    exit 1
fi

# Check if gh CLI is installed
if ! command -v gh &> /dev/null; then
    echo "Error: GitHub CLI (gh) is not installed"
    echo "Please install it from https://cli.github.com/"
    exit 1
fi

echo "Checking PR status for task: $TASK_ID"
echo "Branch: $BRANCH_NAME"
echo "=================================="

# Check if PR exists for this branch
PR_URL=$(gh pr list --head "$BRANCH_NAME" --json url --jq '.[0].url' 2>/dev/null || echo "")

if [ -z "$PR_URL" ]; then
    echo "No pull request found for branch $BRANCH_NAME"
    echo ""
    echo "To create a PR, use: ./create-pr.sh $TASK_ID"
    exit 0
fi

echo "Pull Request found: $PR_URL"
echo ""

# Show PR details
gh pr view "$BRANCH_NAME" --json title,state,reviewDecision,mergeable,statusCheckRollup \
    --template '{{.title}}
Status: {{.state}}
Review Decision: {{.reviewDecision}}
Mergeable: {{.mergeable}}

Status Checks:
{{range .statusCheckRollup}}  {{.state}}: {{.context}}
{{end}}'

echo ""
echo "Use 'gh pr view $BRANCH_NAME' for detailed view"