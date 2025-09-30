# GitHub Integration Scripts

This directory contains all SpecPilot GitHub integration scripts for managing milestones, issues, and pull requests with seamless synchronization between SpecPilot specifications and GitHub project management.

## 📁 File Structure

```txt
scripts/github/
├── README.md                 # This documentation
├── github-manager.sh         # Main GitHub integration manager
├── setup-labels.sh          # GitHub labels configuration script
├── check-or-create-repo.sh   # Check or create GitHub repository
├── check-pr-status.sh       # Check pull request status
├── create-pr.sh             # Create pull request
└── merge-pr.sh              # Merge pull request
```

## 🚀 Quick Start

### 1. Initial Setup

```bash
# Setup GitHub labels (one-time setup)
./scripts/github/setup-labels.sh
```

### 2. Basic Usage

```bash
# Sync all epics and tasks to GitHub
./scripts/github/github-manager.sh sync-all

# Sync specific epic
./scripts/github/github-manager.sh sync-epic epic-001

# Sync specific task
./scripts/github/github-manager.sh sync-task task-001
```

### 3. Status Checking

```bash
# View project status
./scripts/github/github-manager.sh project-status

# Check GitHub configuration
./scripts/github/github-manager.sh check-github-config
```

### 4. Debug Logging

```bash
# Enable detailed logging for troubleshooting
export SPECPILOT_DEBUG=true
./scripts/github/github-manager.sh sync-all

# Check operation logs
tail -f .specpilot-debug.log
```

## 🏷️ Label System

After running `setup-labels.sh`, the system automatically creates the following labels:

### Status Labels

- `status:new` - Newly created task
- `status:ready` - Ready to start (deprecated - use dynamic analysis)
- `status:in-progress` - Currently in development
- `status:review` - Under review
- `status:done` - Completed
- `status:blocked` - Blocked

### Priority Labels

- `priority:low` - Low priority
- `priority:medium` - Medium priority
- `priority:high` - High priority
- `priority:critical` - Critical priority

### Type Labels

- `type:task` - Development task
- `type:epic` - Epic or feature group
- `type:bug` - Bug fix
- `type:feature` - New feature

### Complexity Labels

- `complexity:low` - Low complexity
- `complexity:medium` - Medium complexity
- `complexity:high` - High complexity

### Estimate Labels

- `estimate:1h`, `estimate:2h`, `estimate:5h`
- `estimate:1d`, `estimate:2d`, `estimate:3d`
- `estimate:1w`

### Agent Type Labels

- `agent:frontend` - Frontend development
- `agent:backend` - Backend development
- `agent:fullstack` - Full-stack development
- `agent:testing` - Testing and QA

## 📋 Task Development Workflow

### Starting Task Development

1. **Update task status**:

    ```bash
    # Edit specs/tasks/task-001.md
    # Change status: new to status: in_progress
    ```

2. **Sync to GitHub**:

    ```bash
    ./scripts/github/github-manager.sh sync-task task-001
    ```

### Completing a Task

1. **Update task status**:

    ```bash
    # Edit specs/tasks/task-001.md
    # Change status: in_progress to status: done
    ```

2. **Sync to GitHub**:

    ```bash
    ./scripts/github/github-manager.sh sync-task task-001
    # This automatically closes the corresponding GitHub issue
    ```

## 🔧 github-manager.sh Command Reference

### Milestone Operations

```bash
./scripts/github/github-manager.sh create-milestone <epic-id>
./scripts/github/github-manager.sh update-milestone <epic-id>
```

### Issue Operations

```bash
./scripts/github/github-manager.sh create-issue <task-id>
./scripts/github/github-manager.sh update-issue <task-id>
```

### Sync Operations

```bash
./scripts/github/github-manager.sh sync-epic <epic-id>
./scripts/github/github-manager.sh sync-task <task-id>
./scripts/github/github-manager.sh sync-all
```

### Status Operations

```bash
./scripts/github/github-manager.sh check-github-config
./scripts/github/github-manager.sh project-status
```

## 🔄 Synchronization Logic

### How Sync Works

The GitHub integration uses intelligent synchronization:

**For Milestones:**

- **Check Existence**: Uses milestone title to find existing milestones
- **If Exists**: Updates description, progress, and status
- **If Missing**: Creates new milestone from epic data
- **Progress Calculation**: Automatically calculates completion percentage

**For Issues:**

- **Check Existence**: Uses issue title pattern to find existing issues
- **If Exists**: Updates content, labels, and status
- **If Missing**: Creates new issue from task data
- **Auto-Close**: Closes issues when tasks are marked as done

### Idempotent Operations

All sync operations are safe to run multiple times:

- ✅ No duplicate creation
- 🔄 Content stays updated
- 📊 Progress automatically recalculated
- 🏷️ Labels synchronized with task metadata

## 📊 Integration Features

### Automatic Milestone Management

- **Creation**: Epics automatically become GitHub milestones
- **Progress**: Real-time calculation based on task completion
- **Status**: Milestone state follows epic status
- **Description**: Rich milestone descriptions with epic details

### Smart Issue Handling

- **Labels**: Automatic labeling based on task metadata
- **Status**: Issue state synchronized with task status
- **Content**: Rich issue bodies with task specifications
- **Milestone Association**: Issues automatically linked to epic milestones

### Metadata Extraction

- **From YAML**: Status, priority, estimates from frontmatter
- **From Content**: Complexity, recommended agents from task body
- **From Structure**: Epic relationships and dependencies

## 🛠️ Setup Requirements

### Prerequisites

```bash
# GitHub CLI installation
brew install gh

# GitHub authentication
gh auth login

# Repository access verification
gh repo view
```

### Environment Verification

```bash
# Check GitHub CLI status
gh auth status

# Verify repository connection
git config --get remote.origin.url

# Test GitHub API access
gh api user
```

## 💡 Best Practices

### Synchronization Strategy

1. **Regular Sync**: Sync changes after updating task/epic status
2. **Batch Operations**: Use `sync-all` for comprehensive updates
3. **Status Verification**: Check project status before major changes
4. **Label Consistency**: Let the system manage labels automatically

### Workflow Integration

```bash
# Typical development cycle
# 1. Update SpecPilot task status
vim specs/tasks/task-001.md

# 2. Sync to GitHub
./scripts/github/github-manager.sh sync-task task-001

# 3. Verify synchronization
gh issue view <issue-number>
```

### Error Handling

- **API Limits**: Scripts handle GitHub API rate limits
- **Network Issues**: Automatic retry for transient failures
- **Validation**: Pre-flight checks for required data
- **Safe Defaults**: Graceful degradation when data is missing

## 🔧 Customization

### Label Customization

Modify `setup-labels.sh` to add custom labels:

```bash
# Add custom labels
gh label create "custom:label" --description "Custom description" --color "ff0000" --force
```

### Integration Hooks

The system supports custom hooks for:

- Pre-sync validation
- Post-sync notifications
- Custom label logic
- Integration with external tools

## 🐛 Troubleshooting

### Common Issues

**Authentication Problems:**

```bash
# Re-authenticate with GitHub
gh auth login

# Check authentication status
gh auth status

# Refresh authentication tokens
gh auth refresh
```

**Label Errors:**

```bash
# Recreate all labels
./scripts/github/setup-labels.sh

# Check existing labels
gh label list
```

**Sync Failures:**

```bash
# Check repository status
gh repo view

# Verify file permissions
ls -la specs/tasks/

# Check network connectivity
ping github.com

# Enable debug logging for detailed error information
export SPECPILOT_DEBUG=true
./scripts/github/github-manager.sh sync-task task-001
cat .specpilot-debug.log | grep ERROR
```

## 🔍 Debug and Logging

### Unified Logging System

All GitHub scripts now include comprehensive logging to `.specpilot-debug.log`:

```bash
# Enable debug mode
export SPECPILOT_DEBUG=true

# Run any GitHub operation
./scripts/github/github-manager.sh sync-all

# View detailed logs
cat .specpilot-debug.log
```

### Log Levels and Information

The logging system tracks:

- **Script Start/End**: Execution timestamps and success/failure status
- **Operations**: Each GitHub API call and its parameters
- **Errors**: Detailed error messages with context
- **API Responses**: GitHub API response summaries

### Monitoring GitHub Operations

```bash
# Real-time log monitoring
tail -f .specpilot-debug.log

# Filter specific operations
grep "github-manager" .specpilot-debug.log

# Check for errors only
grep "ERROR" .specpilot-debug.log

# View recent GitHub API calls
grep "OPERATION" .specpilot-debug.log | tail -10
```

### Custom Log File Location

```bash
# Use custom log file
export SPECPILOT_DEBUG_FILE="/path/to/custom.log"
./scripts/github/github-manager.sh sync-all
```

## 📈 Advanced Features

### Batch Processing

```bash
# Process all epics in sequence
for epic in specs/epics/epic-*.md; do
  epic_id=$(basename "$epic" .md)
  ./scripts/github/github-manager.sh sync-epic "$epic_id"
done
```

### Status Monitoring

```bash
# Monitor project progress
watch -n 30 './scripts/github/github-manager.sh project-status'

# Check GitHub integration health
./scripts/github/github-manager.sh check-github-config
```

### API Integration

```bash
# Direct GitHub API access for custom operations
gh api repos/:owner/:repo/milestones
gh api repos/:owner/:repo/issues --jq '.[] | {number, title, state}'
```

## 🔗 Related Resources

- [GitHub CLI Manual](https://cli.github.com/manual/)
- [GitHub API Documentation](https://docs.github.com/en/rest)
- [SpecPilot Documentation](https://github.com/sacahan/SpecPilot)
- [Git Worktree Integration](../git-worktree/README.md)
