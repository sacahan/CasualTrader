#!/bin/bash
# PR Content Generation Script
# Usage: ./generate-pr-content.sh <task-id>

set -e

# Set locale for UTF-8 support
export LC_ALL=en_US.UTF-8
export LANG=en_US.UTF-8

TASK_ID="$1"
PROJECT_ROOT="$(git rev-parse --show-toplevel)"
SCRIPT_DIR="$PROJECT_ROOT/scripts"
BRANCH_NAME="${TASK_ID}-feature"

if [ -z "$TASK_ID" ]; then
	echo "Error: Task ID is required"
	echo "Usage: $0 <task-id>"
	exit 1
fi

# Color output functions
green() { echo -e "\033[32m$1\033[0m"; }
blue() { echo -e "\033[34m$1\033[0m"; }
yellow() { echo -e "\033[33m$1\033[0m"; }

# Extract task information
extract_task_info() {
	local task_file="$PROJECT_ROOT/specs/tasks/$TASK_ID.md"

	if [ ! -f "$task_file" ]; then
		echo "Error: Task file not found: $task_file"
		exit 1
	fi

	# Extract task overview (first paragraph after # Task Overview)
	TASK_OVERVIEW=$(awk '
        /^# Task Overview$/ { found=1; next }
        found && /^$/ { getline; if ($0 ~ /^#/) exit; overview=$0; next }
        found && overview && /^$/ { exit }
        found && overview { overview=overview" "$0 }
        END { print overview }
    ' "$task_file")

	# Extract Implementation Scope
	IMPL_SCOPE=$(awk '
        /^## Implementation Scope$/ { found=1; next }
        found && /^##/ { exit }
        found && /^-/ { print $0 }
    ' "$task_file")

	# Extract Acceptance Criteria
	ACCEPTANCE_CRITERIA=$(awk '
        /^## Acceptance Criteria$/ { found=1; next }
        found && /^##/ { exit }
        found && /^-/ { print $0 }
    ' "$task_file")

	# Extract Technical Requirements
	TECH_REQUIREMENTS=$(awk '
        /^## Technical Requirements$/ { found=1; next }
        found && /^##/ { exit }
        found && /^-/ && !/\*\*Depends On\*\*/ && !/\*\*Blocks\*\*/ { print $0 }
    ' "$task_file")

	# Extract epic information
	EPIC_ID=$(awk '/^epic:/ {print $2}' "$task_file")

	# Check if there's implementation progress section
	if grep -q "^## 📋 Implementation Progress" "$task_file"; then
		IMPL_PROGRESS=$(awk '
            /^## 📋 Implementation Progress$/ { found=1; next }
            found && /^##/ && !/^### / { exit }
            found { print $0 }
        ' "$task_file")
	fi
}

# Get commit information from feature branch
get_commit_info() {
	# Check if feature branch exists
	if ! git show-ref --verify --quiet "refs/heads/$BRANCH_NAME"; then
		yellow "Warning: Feature branch $BRANCH_NAME not found"
		COMMIT_MESSAGES=""
		FILE_CHANGES=""
		return
	fi

	# Get commit messages (excluding merge commits and status update commits)
	COMMIT_MESSAGES=$(git log main.."$BRANCH_NAME" --oneline --no-merges --grep="Generated with SpecPilot" --invert-grep 2>/dev/null || echo "")

	# Get changed files categorized
	local changed_files
	changed_files=$(git diff --name-only main..."$BRANCH_NAME" 2>/dev/null || echo "")

	# Simply store all changed files without categorization
	FILE_CHANGES="$changed_files"
}

# Generate PR title
generate_pr_title() {
	if [ -n "$TASK_OVERVIEW" ]; then
		# Clean up the overview for title - use a safer approach
		local title_content
		title_content=$(echo "$TASK_OVERVIEW" | head -c 60)
		# Remove trailing punctuation using parameter expansion instead of sed
		title_content=${title_content%。}
		title_content=${title_content%.}
		PR_TITLE="feat($TASK_ID): $title_content"
	else
		PR_TITLE="feat($TASK_ID): implement task requirements"
	fi
}

# Generate PR description
generate_pr_description() {
	cat >/tmp/pr-description.md <<EOF
## Summary

$TASK_OVERVIEW

## Changes

### 🚀 Core Features
EOF

	# Add implementation scope
	if [ -n "$IMPL_SCOPE" ]; then
		echo "$IMPL_SCOPE" >>/tmp/pr-description.md
	else
		echo "- Implemented task requirements as specified" >>/tmp/pr-description.md
	fi

	# Add file changes section
	if [ -n "$FILE_CHANGES" ]; then
		cat >>/tmp/pr-description.md <<EOF

### 📁 Files Modified
EOF
		echo "$FILE_CHANGES" | sed 's/^/- /' >>/tmp/pr-description.md
	fi

	# Add testing section
	cat >>/tmp/pr-description.md <<EOF

## Testing

### ✅ Acceptance Criteria Met
EOF

	if [ -n "$ACCEPTANCE_CRITERIA" ]; then
		echo "$ACCEPTANCE_CRITERIA" >>/tmp/pr-description.md
	else
		echo "- All task requirements completed as specified" >>/tmp/pr-description.md
	fi

	# Add implementation progress if available
	if [ -n "$IMPL_PROGRESS" ]; then
		cat >>/tmp/pr-description.md <<EOF

### 🧪 Implementation Evidence
$IMPL_PROGRESS
EOF
	fi

	# Add technical notes
	if [ -n "$TECH_REQUIREMENTS" ]; then
		cat >>/tmp/pr-description.md <<EOF

## Technical Notes
$TECH_REQUIREMENTS
EOF
	fi

	# Add commit history
	if [ -n "$COMMIT_MESSAGES" ]; then
		cat >>/tmp/pr-description.md <<EOF

## Commit History
\`\`\`
$COMMIT_MESSAGES
\`\`\`
EOF
	fi

	# Add related information
	cat >>/tmp/pr-description.md <<EOF

## Related
- **Task**: \`specs/tasks/$TASK_ID.md\`
EOF

	if [ -n "$EPIC_ID" ]; then
		echo "- **Epic**: \`specs/epics/$EPIC_ID.md\`" >>/tmp/pr-description.md
	fi

	cat >>/tmp/pr-description.md <<EOF
- **SpecPilot Workflow**: Automated task management and status tracking

---
*🤖 Generated automatically by SpecPilot workflow automation*
EOF

	PR_DESCRIPTION=$(cat /tmp/pr-description.md)
	rm -f /tmp/pr-description.md
}

# Main execution
main() {
	blue "🔍 Extracting task information..."
	extract_task_info

	blue "📝 Analyzing commit history and file changes..."
	get_commit_info

	blue "🎯 Generating PR title..."
	generate_pr_title

	blue "📄 Generating PR description..."
	generate_pr_description

	# Output results for the calling script
	echo "PR_TITLE=$PR_TITLE"
	echo "PR_DESCRIPTION_FILE=/tmp/pr-description-${TASK_ID}.md"

	# Save description to file for the create-pr.sh script
	echo "$PR_DESCRIPTION" >"/tmp/pr-description-${TASK_ID}.md"

	green "✅ PR content generated successfully!"
	echo ""
	echo "Title: $PR_TITLE"
	echo "Description saved to: /tmp/pr-description-${TASK_ID}.md"
}

# Run main function
main "$@"
