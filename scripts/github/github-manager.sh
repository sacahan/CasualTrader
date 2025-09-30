#!/bin/bash
# GitHub Integration Manager for SpecPilot
# Manages Milestones and Issues based on Epic and Task files
# Usage: ./github-manager.sh <operation> [options...]

set -e

SCRIPT_DIR="$(dirname "$0")"
PROJECT_ROOT="$(git rev-parse --show-toplevel)"
SPECS_DIR="$PROJECT_ROOT/specs"
GITHUB_SERVER_URL="https://github.com"
GITHUB_REPOSITORY="$(git config --get remote.origin.url | sed -E 's#.*github.com[:/](.*)\.git#\1#')"

# Source logging utilities
source "$PROJECT_ROOT/scripts/common/logging.sh"

# Error trap to log failures
trap 'log_script_end "github-manager.sh" "false"' ERR

# Log script start
log_script_start "github-manager.sh" "$*"

# Color output functions
red() { echo -e "\033[31m$1\033[0m"; }
green() { echo -e "\033[32m$1\033[0m"; }
yellow() { echo -e "\033[33m$1\033[0m"; }
blue() { echo -e "\033[34m$1\033[0m"; }

# Get label information (description|color)
get_label_info() {
  local label="$1"
  case "$label" in
    # Status labels
    "status:new") echo "Task is newly created|f0f8fe" ;;
    "status:ready") echo "Task is ready to start|7057ff" ;;
    "status:in_progress") echo "Task is currently being worked on|006b75" ;;
    "status:review") echo "Task is under review|ff9500" ;;
    "status:done") echo "Task is completed|0e8a16" ;;
    "status:blocked") echo "Task is blocked|d93f0b" ;;

    # Priority labels
    "priority:low") echo "Low priority task|c2e0c6" ;;
    "priority:medium") echo "Medium priority task|fbca04" ;;
    "priority:high") echo "High priority task|ff9500" ;;
    "priority:critical") echo "Critical priority task|d93f0b" ;;

    # Type labels
    "type:task") echo "Individual development task|0075ca" ;;
    "type:epic") echo "Epic or feature group|5319e7" ;;
    "type:bug") echo "Bug fix|d73a4a" ;;
    "type:feature") echo "New feature|a2eeef" ;;

    # Complexity labels
    "complexity:low") echo "Low complexity task|c5f015" ;;
    "complexity:medium") echo "Medium complexity task|fbca04" ;;
    "complexity:high") echo "High complexity task|ff6600" ;;

    # Agent type labels
    "agent:frontend") echo "Frontend development|1d76db" ;;
    "agent:backend") echo "Backend development|0052cc" ;;
    "agent:backend-expert") echo "Backend expert development|0052cc" ;;
    "agent:frontend-expert") echo "Frontend expert development|1d76db" ;;
    "agent:fullstack") echo "Full-stack development|5319e7" ;;
    "agent:testing") echo "Testing and QA|006b75" ;;

    *) echo "" ;;
  esac
}

# Ensure required labels exist
ensure_labels_exist() {
  local required_labels=("$@")
  local labels_created=false

  for label in "${required_labels[@]}"; do
    # Skip empty labels
    if [ -z "$label" ]; then
      continue
    fi

    # Check if label exists
    if ! gh label list --json name --jq '.[].name' | grep -q "^${label}$"; then
      # Label doesn't exist, create it
      local label_info=$(get_label_info "$label")
      if [ -n "$label_info" ]; then
        IFS='|' read -ra info_parts <<<"$label_info"
        local description="${info_parts[0]}"
        local color="${info_parts[1]}"

        if gh label create "$label" --description "$description" --color "$color" >/dev/null 2>&1; then
          if [ "$labels_created" = false ]; then
            blue "Creating missing GitHub labels..."
            labels_created=true
          fi
          echo "  ✅ Created label: $label"
        else
          yellow "  ⚠️ Could not create label: $label"
        fi
      else
        yellow "  ⚠️ Unknown label definition: $label"
      fi
    fi
  done

  if [ "$labels_created" = true ]; then
    echo ""
  fi
}

usage() {
  echo "GitHub Integration Manager for SpecPilot"
  echo ""
  echo "Usage: $0 <operation> [options...]"
  echo ""
  echo "=== Milestone Operations ==="
  echo "  create-milestone <epic-id>           - Create GitHub Milestone from Epic"
  echo "  update-milestone <epic-id>           - Update Milestone with Epic progress"
  echo "  close-milestone <epic-id>            - Close completed Milestone"
  echo "  list-milestones                      - List all Milestones"
  echo ""
  echo "=== Issue Operations ==="
  echo "  create-issue <task-id>               - Create GitHub Issue from Task"
  echo "  update-issue <task-id>               - Update Issue with Task status"
  echo "  close-issue <task-id>                - Close completed Issue"
  echo "  list-issues [milestone-number]       - List Issues (optionally filtered by Milestone)"
  echo ""
  echo "=== Sync Operations ==="
  echo "  sync-epic <epic-id>                  - Sync Epic with its Milestone and related Issues"
  echo "  sync-task <task-id>                  - Sync Task with its Issue"
  echo "  sync-all                             - Sync all Epics and Tasks with GitHub"
  echo ""
  echo "=== Status Operations ==="
  echo "  check-github-config                  - Verify GitHub CLI authentication"
  echo "  project-status                       - Show project status with GitHub integration"
  echo ""
  echo "Examples:"
  echo "  $0 create-milestone epic-001"
  echo "  $0 create-issue task-001"
  echo "  $0 sync-epic epic-001"
  echo "  $0 sync-all"
}

check_dependencies() {
  # Check if we're in a git repository
  if ! git rev-parse --git-dir >/dev/null 2>&1; then
    red "Error: Not in a git repository"
    exit 1
  fi

  # Check GitHub CLI
  if ! command -v gh &>/dev/null; then
    red "Error: GitHub CLI (gh) is not installed"
    echo "Install with: brew install gh"
    exit 1
  fi

  # Check GitHub authentication
  if ! gh auth status &>/dev/null; then
    red "Error: GitHub CLI is not authenticated"
    echo "Authenticate with: gh auth login"
    exit 1
  fi

  # Check specs directory
  if [ ! -d "$SPECS_DIR" ]; then
    red "Error: Specs directory not found at $SPECS_DIR"
    exit 1
  fi
}

parse_epic_file() {
  local epic_file="$1"
  local epic_id="$2"

  if [ ! -f "$epic_file" ]; then
    red "Error: Epic file not found: $epic_file"
    exit 1
  fi

  # Extract epic ID and status from YAML frontmatter
  EPIC_ID=$(awk '/^id:/ {sub(/^id: */, ""); print; exit}' "$epic_file")
  EPIC_STATUS=$(awk '/^status:/ {sub(/^status: */, ""); print; exit}' "$epic_file")

  # Extract title from first level-1 heading (# ) line
  EPIC_TITLE=$(awk '/^# / {sub(/^# /, ""); print; exit}' "$epic_file")

  # Get content after first level-1 heading (# )
  EPIC_DESCRIPTION=$(awk '/^# / {flag=1; next} flag' "$epic_file")
  EPIC_FILE="$epic_file"

  # If title is empty, use epic ID as fallback
  if [ -z "$EPIC_TITLE" ] || [ "$EPIC_TITLE" = "" ]; then
    EPIC_TITLE="Epic $epic_id"
  fi
}

parse_task_file() {
  local task_file="$1"
  local task_id="$2"

  if [ ! -f "$task_file" ]; then
    red "Error: Task file not found: $task_file"
    exit 1
  fi

  # Extract task information from YAML frontmatter
  TASK_ID=$(awk '/^id:/ {sub(/^id: */, ""); print; exit}' "$task_file")
  TASK_STATUS=$(awk '/^status:/ {sub(/^status: */, ""); print; exit}' "$task_file")
  TASK_EPIC=$(awk '/^epic:/ {sub(/^epic: */, ""); print; exit}' "$task_file")
  TASK_PRIORITY=$(awk '/^priority:/ {sub(/^priority: */, ""); print; exit}' "$task_file")
  TASK_ESTIMATE=$(awk '/^estimate:/ {sub(/^estimate: *"?/, ""); sub(/"? *$/, ""); print; exit}' "$task_file")

  # Extract first paragraph after first level-1 heading (# ) as title
  # Find the line after "# Task Overview" and extract the description paragraph
  TASK_TITLE=$(awk '
    /^# Task Overview/ { found = 1; next }
    found && /^$/ { next }
    found && /^##/ { exit }
    found && /^[^#]/ && NF > 0 {
      # Collect all lines of the paragraph
      para = $0
      while (getline > 0 && !/^$/ && !/^#/) {
        para = para " " $0
      }
      print para
      exit
    }
  ' "$task_file")

  # Clean up any extra whitespace
  TASK_TITLE=$(echo "$TASK_TITLE" | sed 's/[[:space:]]\+/ /g; s/^[[:space:]]*//; s/[[:space:]]*$//')

  # Truncate title if too long (keep it under 80 characters for GitHub issue title)
  if [ ${#TASK_TITLE} -gt 80 ]; then
    TASK_TITLE="${TASK_TITLE:0:77}..."
  fi

  # Extract additional metadata from ai_hints if available
  local ai_hints_line=$(awk '/^ai_hints:/ {print; exit}' "$task_file")
  TASK_COMPLEXITY=$(echo "$ai_hints_line" | sed -n 's/.*"complexity":"\([^"]*\)".*/\1/p')
  TASK_AGENT=$(echo "$ai_hints_line" | sed -n 's/.*"agent":"\([^"]*\)".*/\1/p')

  # Get content after first level-1 heading (# )
  TASK_DESCRIPTION=$(awk '/^# / {flag=1; next} flag' "$task_file")
  TASK_FILE="$task_file"

  # If title is empty, use task ID as fallback
  if [ -z "$TASK_TITLE" ] || [ "$TASK_TITLE" = "" ]; then
    TASK_TITLE="Task $task_id"
  fi
}

get_milestone_number() {
  local epic_title="$1"

  # Search for existing milestone by title
  local milestone_number=$(gh api repos/:owner/:repo/milestones --jq ".[] | select(.title == \"$epic_title\") | .number" | head -1)
  echo "$milestone_number"
}

get_issue_number() {
  local task_title="$1"
  local task_id="$2"

  # First try to search by task ID in title (more reliable) - include both open and closed issues
  local issue_number=$(gh issue list --state all --json number,title --jq ".[] | select(.title | contains(\"[$task_id]\")) | .number" | head -1)

  # If not found, try searching by full title - include both open and closed issues
  if [ -z "$issue_number" ]; then
    issue_number=$(gh issue list --state all --search "\"$task_title\" in:title" --json number --jq '.[0].number // empty')
  fi

  echo "$issue_number"
}

create_milestone() {
  local epic_id="$1"
  local epic_file="$SPECS_DIR/epics/$epic_id.md"

  blue "Creating milestone for epic: $epic_id"

  # Parse epic file
  parse_epic_file "$epic_file" "$epic_id"

  # Check if milestone already exists
  local existing_milestone=$(get_milestone_number "$EPIC_TITLE")
  if [ -n "$existing_milestone" ]; then
    yellow "Milestone already exists: #$existing_milestone - $EPIC_TITLE"
    return 0
  fi

  # Create milestone
  local milestone_body="Auto-synced from \`specs/epics/$epic_id.md\`

## Epic Information
- **Status**: $EPIC_STATUS
- **File**: [\`specs/epics/$epic_id.md\`]($GITHUB_SERVER_URL/$GITHUB_REPOSITORY/blob/main/specs/epics/$epic_id.md)

## Epic Description
$EPIC_DESCRIPTION

---
*This milestone is automatically managed by SpecPilot.*"

  local milestone_number=$(gh api repos/:owner/:repo/milestones \
    --method POST \
    --field title="$EPIC_TITLE" \
    --field description="$milestone_body" \
    --field state="open" \
    --jq '.number')

  green "✅ Created milestone #$milestone_number: $EPIC_TITLE"
  echo "milestone_number=$milestone_number"
}

update_milestone() {
  local epic_id="$1"
  local epic_file="$SPECS_DIR/epics/$epic_id.md"

  blue "Updating milestone for epic: $epic_id"

  # Parse epic file
  parse_epic_file "$epic_file" "$epic_id"

  # Get milestone number
  local milestone_number=$(get_milestone_number "$EPIC_TITLE")
  if [ -z "$milestone_number" ]; then
    yellow "Milestone not found for epic: $epic_id. Creating new milestone..."
    create_milestone "$epic_id"
    return $?
  fi

  # Calculate progress by counting related tasks
  local total_tasks=$(find "$SPECS_DIR/tasks" -name "task-*.md" -exec grep -l "epic: $epic_id" {} \; | wc -l)
  local completed_tasks=$(find "$SPECS_DIR/tasks" -name "task-*.md" -exec sh -c 'grep -l "epic: '$epic_id'" "$1" && grep -l "status: done" "$1"' _ {} \; | sort | uniq -d | wc -l)

  local progress_percent=0
  if [ "$total_tasks" -gt 0 ]; then
    progress_percent=$((completed_tasks * 100 / total_tasks))
  fi

  # Update milestone description with progress
  local milestone_body="Auto-synced from \`specs/epics/$epic_id.md\`

## Epic Information
- **Status**: $EPIC_STATUS
- **Progress**: $progress_percent% complete ($completed_tasks/$total_tasks tasks done)
- **File**: [\`specs/epics/$epic_id.md\`]($GITHUB_SERVER_URL/$GITHUB_REPOSITORY/blob/main/specs/epics/$epic_id.md)

## Epic Description
$EPIC_DESCRIPTION

---
*This milestone is automatically managed by SpecPilot.*"

  # Determine milestone state based on epic status
  local milestone_state="open"
  if [ "$EPIC_STATUS" = "done" ]; then
    milestone_state="closed"
  fi

  gh api repos/:owner/:repo/milestones/$milestone_number \
    --method PATCH \
    --field description="$milestone_body" \
    --field state="$milestone_state" >/dev/null

  green "✅ Updated milestone #$milestone_number: $EPIC_TITLE ($progress_percent% complete)"
}

create_issue() {
  local task_id="$1"
  local task_file="$SPECS_DIR/tasks/$task_id.md"

  blue "Creating issue for task: $task_id"

  # Parse task file
  parse_task_file "$task_file" "$task_id"

  # Format issue title with task ID
  local issue_title="[$task_id] $TASK_TITLE"

  # Check if issue already exists
  local existing_issue=$(get_issue_number "$issue_title" "$task_id")
  if [ -n "$existing_issue" ]; then
    yellow "Issue already exists: #$existing_issue - $issue_title"
    return 0
  fi

  # Get related milestone
  local epic_file="$SPECS_DIR/epics/$TASK_EPIC.md"
  local milestone_name=""
  if [ -f "$epic_file" ]; then
    parse_epic_file "$epic_file" "$TASK_EPIC"
    milestone_name="$EPIC_TITLE"
  fi

  # Create issue body
  local issue_body="Auto-synced from \`specs/tasks/$task_id.md\`

## Task Information
- **Status**: $TASK_STATUS
- **Priority**: $TASK_PRIORITY
- **Estimate**: $TASK_ESTIMATE
- **Epic**: $TASK_EPIC
- **File**: [\`specs/tasks/$task_id.md\`]($GITHUB_SERVER_URL/$GITHUB_REPOSITORY/blob/main/specs/tasks/$task_id.md)

## Task Description
$TASK_DESCRIPTION

---
*This issue is automatically managed by SpecPilot.*"

  # Set up labels based on task metadata
  local labels="type:task,status:$TASK_STATUS,priority:$TASK_PRIORITY"

  # Add complexity label if available
  if [ -n "$TASK_COMPLEXITY" ]; then
    labels="$labels,complexity:$TASK_COMPLEXITY"
  fi

  # Note: Estimate is included in issue title/body, no need for dynamic labels

  # Add agent type label if available
  if [ -n "$TASK_AGENT" ]; then
    labels="$labels,agent:$TASK_AGENT"
  fi

  # Convert labels string to array and ensure all labels exist
  IFS=',' read -ra LABEL_ARRAY <<<"$labels"
  local filtered_labels=()
  for label in "${LABEL_ARRAY[@]}"; do
    # Trim whitespace
    label=$(echo "$label" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
    if [ -n "$label" ]; then
      filtered_labels+=("$label")
    fi
  done

  # Ensure all required labels exist before creating issue
  ensure_labels_exist "${filtered_labels[@]}"

  # Create issue
  local create_args=("--title" "$issue_title" "--body" "$issue_body")

  # Add validated labels
  for label in "${filtered_labels[@]}"; do
    create_args+=("--label" "$label")
  done

  # Add milestone if found
  if [ -n "$milestone_name" ]; then
    create_args+=("--milestone" "$milestone_name")
  fi

  # Create issue (labels are guaranteed to exist)
  if local create_output=$(gh issue create "${create_args[@]}" 2>&1); then
    # Extract issue number from URL (format: https://github.com/owner/repo/issues/NUMBER)
    local issue_number=$(echo "$create_output" | grep -o '/issues/[0-9]\+' | sed 's|/issues/||')

    if [ -n "$issue_number" ]; then
      green "✅ Created issue #$issue_number: $issue_title"
      if [ -n "$milestone_name" ]; then
        echo "   Associated with milestone: $milestone_name"
      fi
    else
      yellow "⚠️ Issue created but number extraction failed"
      echo "$create_output"
    fi
  else
    red "❌ Failed to create issue: $create_output"
    return 1
  fi
}

update_issue() {
  local task_id="$1"
  local task_file="$SPECS_DIR/tasks/$task_id.md"

  blue "Updating issue for task: $task_id"

  # Parse task file
  parse_task_file "$task_file" "$task_id"

  # Format issue title
  local issue_title="[$task_id] $TASK_TITLE"

  # Get issue number
  local issue_number=$(get_issue_number "$issue_title" "$task_id")
  if [ -z "$issue_number" ]; then
    # Don't create new issues for tasks that are already done
    if [ "$TASK_STATUS" = "done" ]; then
      yellow "⚠️ Task $task_id is done but no issue found. Skipping issue creation for completed task."
      return 0
    fi
    yellow "Issue not found for task: $task_id. Creating new issue..."
    create_issue "$task_id"
    return $?
  fi

  # Update issue based on task status
  local issue_state="open"
  if [ "$TASK_STATUS" = "done" ]; then
    issue_state="closed"
  fi

  # Update issue body
  local issue_body="Auto-synced from \`specs/tasks/$task_id.md\`

## Task Information
- **Status**: $TASK_STATUS
- **Priority**: $TASK_PRIORITY
- **Estimate**: $TASK_ESTIMATE
- **Epic**: $TASK_EPIC
- **File**: [\`specs/tasks/$task_id.md\`]($GITHUB_SERVER_URL/$GITHUB_REPOSITORY/blob/main/specs/tasks/$task_id.md)

## Task Description
$TASK_DESCRIPTION

---
*This issue is automatically managed by SpecPilot.*"

  # Update labels based on task metadata
  local github_status=$(echo "$TASK_STATUS" | sed 's/-/_/g')
  local labels="type:task,status:$github_status,priority:$TASK_PRIORITY"

  # Add complexity label if available
  if [ -n "$TASK_COMPLEXITY" ]; then
    labels="$labels,complexity:$TASK_COMPLEXITY"
  fi

  # Note: Estimate is included in issue title/body, no need for dynamic labels

  # Add agent type label if available
  if [ -n "$TASK_AGENT" ]; then
    labels="$labels,agent:$TASK_AGENT"
  fi

  # Convert labels string to array and ensure all labels exist
  IFS=',' read -ra LABEL_ARRAY <<<"$labels"
  local filtered_labels=()
  for label in "${LABEL_ARRAY[@]}"; do
    # Trim whitespace
    label=$(echo "$label" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
    if [ -n "$label" ]; then
      filtered_labels+=("$label")
    fi
  done

  # Ensure all required labels exist before updating issue
  ensure_labels_exist "${filtered_labels[@]}"

  # Update issue (note: this replaces all labels, not adds)
  gh issue edit "$issue_number" \
    --body "$issue_body"

  # Remove old status labels first to avoid conflicts
  local current_labels=$(gh issue view "$issue_number" --json labels --jq '.labels[].name' | tr '\n' ',' | sed 's/,$//')
  if [ -n "$current_labels" ]; then
    # Remove old status labels
    echo "$current_labels" | tr ',' '\n' | grep '^status:' | while read old_status_label; do
      if [ -n "$old_status_label" ]; then
        gh issue edit "$issue_number" --remove-label "$old_status_label" >/dev/null 2>&1 || true
      fi
    done
  fi

  # Update labels using individual add-label commands (labels are guaranteed to exist)
  for label in "${filtered_labels[@]}"; do
    gh issue edit "$issue_number" --add-label "$label" >/dev/null 2>&1 || true
  done

  # Close issue if task is done
  if [ "$TASK_STATUS" = "done" ]; then
    gh issue close "$issue_number"
    green "✅ Closed issue #$issue_number: $issue_title"
  else
    green "✅ Updated issue #$issue_number: $issue_title"
  fi
}

sync_epic() {
  local epic_id="$1"

  blue "Syncing epic: $epic_id"

  # Create or update milestone
  update_milestone "$epic_id"

  # Find and sync related tasks
  local related_tasks=$(find "$SPECS_DIR/tasks" -name "task-*.md" -exec grep -l "epic: $epic_id" {} \; | xargs -I {} basename {} .md)

  for task_id in $related_tasks; do
    update_issue "$task_id"
  done

  green "✅ Synced epic $epic_id with all related tasks"
}

sync_task() {
  local task_id="$1"

  blue "Syncing task: $task_id"

  # Update issue
  if ! update_issue "$task_id"; then
    red "❌ Failed to update issue for task: $task_id"
    return 1
  fi

  # Update related epic milestone
  local task_file="$SPECS_DIR/tasks/$task_id.md"
  if ! parse_task_file "$task_file" "$task_id"; then
    red "❌ Failed to parse task file: $task_file"
    return 1
  fi

  if [ -n "$TASK_EPIC" ]; then
    if ! update_milestone "$TASK_EPIC"; then
      yellow "⚠️ Failed to update milestone for epic: $TASK_EPIC"
    fi
  fi

  green "✅ Synced task $task_id and related epic"
}

sync_all() {
  blue "Syncing all epics and tasks with GitHub..."

  # Sync all epics
  for epic_file in "$SPECS_DIR/epics"/epic-*.md; do
    if [ -f "$epic_file" ]; then
      local epic_id=$(basename "$epic_file" .md)
      sync_epic "$epic_id"
    fi
  done

  green "✅ Synced all epics and tasks with GitHub"
}

check_github_config() {
  blue "Checking GitHub configuration..."

  echo "Git repository: $(git config --get remote.origin.url || echo 'No origin configured')"
  echo "GitHub CLI version: $(gh --version | head -1)"
  echo "GitHub authentication: $(gh auth status 2>&1 | head -1)"
  echo "Current repository: $(gh repo view --json name,owner --jq '.owner.login + "/" + .name' 2>/dev/null || echo 'Repository not found')"

  green "✅ GitHub configuration check completed"
}

project_status() {
  blue "SpecPilot Project Status with GitHub Integration"

  local total_epics=$(find "$SPECS_DIR/epics" -name "epic-*.md" | wc -l)
  local total_tasks=$(find "$SPECS_DIR/tasks" -name "task-*.md" | wc -l)
  local completed_tasks=$(grep -l "status: done" "$SPECS_DIR/tasks"/task-*.md 2>/dev/null | wc -l)

  echo "📊 Project Overview:"
  echo "   Epics: $total_epics"
  echo "   Tasks: $total_tasks"
  echo "   Completed: $completed_tasks"
  echo "   Progress: $((completed_tasks * 100 / total_tasks))%"

  echo ""
  echo "🎯 GitHub Integration Status:"

  # Check milestones
  local github_milestones=$(gh api repos/:owner/:repo/milestones --jq 'length' 2>/dev/null || echo "0")
  echo "   Milestones: $github_milestones"

  # Check issues
  local github_issues=$(gh issue list --json number --jq 'length' 2>/dev/null || echo "0")
  echo "   Issues: $github_issues"

  green "✅ Project status check completed"
}

# Main execution
OPERATION="$1"

case "$OPERATION" in
  "create-milestone")
    check_dependencies
    if [ -z "$2" ]; then
      red "Error: Epic ID is required"
      log_error "create-milestone: Epic ID is required"
      exit 1
    fi
    log_operation "create-milestone" "epic_id=$2"
    create_milestone "$2"
    ;;

  "update-milestone")
    check_dependencies
    if [ -z "$2" ]; then
      red "Error: Epic ID is required"
      exit 1
    fi
    update_milestone "$2"
    ;;

  "create-issue")
    check_dependencies
    if [ -z "$2" ]; then
      red "Error: Task ID is required"
      exit 1
    fi
    create_issue "$2"
    ;;

  "update-issue")
    check_dependencies
    if [ -z "$2" ]; then
      red "Error: Task ID is required"
      exit 1
    fi
    update_issue "$2"
    ;;

  "sync-epic")
    check_dependencies
    if [ -z "$2" ]; then
      red "Error: Epic ID is required"
      exit 1
    fi
    sync_epic "$2"
    ;;

  "sync-task")
    check_dependencies
    if [ -z "$2" ]; then
      red "Error: Task ID is required"
      exit 1
    fi
    sync_task "$2"
    ;;

  "sync-all")
    check_dependencies
    log_operation "sync-all" ""
    sync_all
    ;;

  "check-github-config")
    check_dependencies
    log_operation "check-github-config" ""
    check_github_config
    ;;

  "project-status")
    check_dependencies
    log_operation "project-status" ""
    project_status
    ;;

  "help" | "--help" | "-h" | "")
    usage
    ;;

  *)
    red "Error: Unknown operation '$OPERATION'"
    log_error "Unknown operation: $OPERATION"
    echo ""
    usage
    log_script_end "github-manager.sh" "false"
    exit 1
    ;;
esac

# Log successful completion
log_script_end "github-manager.sh" "true"
