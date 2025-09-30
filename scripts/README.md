# Scripts Directory

This directory contains all automation scripts for the SpecPilot project, organized by functionality to support the SpecPilot development workflow.

## 📁 Directory Structure

```txt
scripts/
├── README.md                   # This documentation
├── common/                     # Shared utilities
│   └── logging.sh             # Unified logging system
├── github/                     # GitHub integration tools
│   ├── README.md              # GitHub tools documentation
│   ├── github-manager.sh      # Main GitHub integration manager
│   ├── setup-labels.sh        # GitHub labels configuration
│   └── ... (other GitHub tools)
├── git-worktree/              # Git worktree management tools
│   ├── README.md              # Git worktree documentation
│   └── ... (worktree scripts)
└── specpilot-workflow.sh       # Main SpecPilot workflow orchestrator
```

## 🎯 Core Components

### 0. Shared Utilities (`common/`)

Unified logging and utility functions used across all scripts.

**Key Features:**

- Consistent logging to `.specpilot-debug.log`
- Script execution tracking with start/end timestamps
- Error handling and operation logging
- Compatible with `src/tools/` logging system

### 1. GitHub Integration (`github/`)

Complete GitHub integration suite for managing milestones, issues, and pull requests.

**Key Features:**

- Automatic milestone creation from epics
- Issue management synchronized with tasks
- Label management system
- Status synchronization between SpecPilot and GitHub

**Quick Start:**

```bash
# Setup (one-time)
./scripts/github/setup-labels.sh

# Daily usage
./scripts/github/github-manager.sh sync-all
```

### 2. Git Worktree Management (`git-worktree/`)

Git worktree tools for isolated development environments per task.

**Key Features:**

- Isolated development branches
- Clean workspace management
- Parallel development support
- Automatic cleanup and synchronization

### 3. SpecPilot Workflow (`specpilot-workflow.sh`)

Main orchestrator script that coordinates all development workflow components.

**Key Features:**

- Task lifecycle management
- Branch creation and management
- Integration with GitHub tools
- Worktree coordination

## 📋 SpecPilot Workflow Operations

The `specpilot-workflow.sh` script provides comprehensive task lifecycle management through the following operations:

### Core Workflow Operations

#### `start-task <task-id>`

**Purpose:** Initialize development environment for a new task

**Operations performed:**

1. Update task status: `new` → `in_progress` in main branch
2. Update related epic status to `in_progress` (if epic was `new`)
3. Commit status updates to main branch with standardized message
4. Create isolated worktree environment via `create-worktree.sh`
5. Sync updated spec files to worktree directory
6. Sync with GitHub Issues and Milestones (conditional)
7. Restore any stashed changes

**Output:** Ready development environment in `workspaces/<task-id>`

#### `prepare-pr <task-id> [title] [description]`

**Purpose:** Complete development and prepare for code review

**Operations performed:**

1. Commit and push worktree changes (if executed from worktree directory)
    - Add all changes with `git add .`
    - Commit with standardized message format
    - Push to feature branch `<task-id>-feature`
2. Update task status: `in_progress` → `review` in main branch
3. Check and update epic completion status
4. Commit status updates to main branch
5. Sync updated spec files to worktree
6. Verify GitHub repository exists
7. Create pull request via `create-pr.sh`
8. Sync with GitHub Issues and Milestones (conditional)

**Output:** Pull request created, task ready for review

#### `close-task <task-id> [merge-method]`

**Purpose:** Finalize task completion and cleanup

**Operations performed:**

1. Update task status: `review` → `done` in main branch
2. Check and update epic completion status (mark epic as `done` if all tasks complete)
3. Commit final status updates to main branch
4. Merge pull request via `merge-pr.sh`
5. Sync updated spec files to worktree
6. Sync with GitHub to close Issues and update Milestones (conditional)
7. Clean up worktree environment via `cleanup-worktree.sh`

**Output:** Task completed, PR merged, environment cleaned

### Git Worktree Operations

#### `create-worktree <task-id> [base-branch]`

**Purpose:** Create isolated development environment

**Operations performed:**

1. Validate task ID parameter
2. Execute `git-worktree/create-worktree.sh` with task ID and base branch
3. Log operation details

#### `cleanup-worktree <task-id> [--keep-branch]`

**Purpose:** Remove worktree and optionally clean up branch

**Operations performed:**

1. Validate task ID parameter
2. Execute `git-worktree/cleanup-worktree.sh` with cleanup options
3. Log operation details

#### `sync-worktree <task-id> [base-branch]`

**Purpose:** Synchronize worktree with latest base branch changes

**Operations performed:**

1. Validate task ID parameter
2. Execute `git-worktree/sync-worktree.sh` with sync parameters
3. Log operation details

#### `list-worktrees`

**Purpose:** Display all active worktrees

**Operations performed:**

1. Execute `git-worktree/list-worktrees.sh`
2. Display worktree status and locations

### GitHub Operations

#### `create-pr <task-id> [title] [description]`

**Purpose:** Create pull request for task

**Operations performed:**

1. Validate task ID parameter
2. Verify GitHub repository exists via `check-or-create-repo.sh`
3. Execute `github/create-pr.sh` with PR details
4. Log operation details

#### `check-pr <task-id>`

**Purpose:** Check pull request status

**Operations performed:**

1. Validate task ID parameter
2. Execute `github/check-pr-status.sh`
3. Display PR status information

#### `merge-pr <task-id> [method]`

**Purpose:** Merge pull request with specified method

**Operations performed:**

1. Validate task ID parameter
2. Execute `github/merge-pr.sh` with merge method
3. Log merge operation

### Utility Operations

#### `help` | `--help` | `-h` | (empty)

**Purpose:** Display comprehensive usage information

**Operations performed:**

1. Display usage syntax and examples
2. Show AI agent quick reference
3. List all available operations with descriptions
4. Provide workflow examples

### Error Handling Features

All operations include:

- Parameter validation with clear error messages
- Comprehensive error trapping and logging
- GitHub CLI authentication verification
- Git repository state validation
- Uncommitted changes detection and handling
- Operation logging to `.specpilot-debug.log`
- Graceful cleanup on script interruption

## 🚀 Getting Started

### Prerequisites

```bash
# Required tools
brew install gh          # GitHub CLI
git --version           # Git (2.5+)
```

### Basic Workflow

```bash
# 1. Initialize GitHub integration
./scripts/github/setup-labels.sh

# 2. Sync project to GitHub
./scripts/github/github-manager.sh sync-all

# 3. Start development on a task
./scripts/specpilot-workflow.sh start-task task-001

# 4. Update task status and sync
./scripts/github/github-manager.sh sync-task task-001
```

## 📖 Detailed Documentation

### GitHub Integration

See [github/README.md](github/README.md) for comprehensive GitHub integration documentation including:

- Label system configuration
- Milestone and issue management
- Status synchronization workflows
- API integration details

### Git Worktree Management

See [git-worktree/README.md](git-worktree/README.md) for git worktree documentation including:

- Worktree creation and management
- Branch isolation strategies
- Cleanup and maintenance procedures

## 🔧 Script Conventions

### Naming Conventions

- **Kebab-case**: All script files use kebab-case naming
- **Descriptive**: Names clearly indicate functionality
- **Organized**: Scripts grouped by functional area

### Usage Patterns

```bash
# All scripts support --help
./scripts/github/github-manager.sh --help

# Consistent parameter patterns
./scripts/github/github-manager.sh <operation> <target>
./scripts/git-worktree/create-worktree.sh <task-id>
```

### Error Handling

- All scripts include comprehensive error checking
- Clear error messages with suggested solutions
- Safe defaults and validation
- Automatic logging of errors and failures

### Debug Logging

- All scripts log execution details to `.specpilot-debug.log`
- Enable debug mode: `export SPECPILOT_DEBUG=true`
- Custom log file: `export SPECPILOT_DEBUG_FILE=/path/to/logfile`
- Unified logging format with timestamps and operation tracking

## 🛠️ Development Guidelines

### Adding New Scripts

1. Place in appropriate subdirectory
2. Follow naming conventions
3. Include comprehensive help text
4. Add error handling and validation
5. **Include logging integration**: Source `common/logging.sh`
6. Update relevant README.md

### Script Structure

```bash
#!/bin/bash
# Script description and purpose

set -e  # Exit on error

PROJECT_ROOT="$(git rev-parse --show-toplevel)"

# Source logging utilities
source "$PROJECT_ROOT/scripts/common/logging.sh"

# Error trap to log failures
trap 'log_script_end "script-name.sh" "false"' ERR

# Log script start
log_script_start "script-name.sh" "$*"

# Color output functions
# Parameter validation with log_error for failures
# Main functionality with log_operation for key operations
# Error handling

# Log successful completion
log_script_end "script-name.sh" "true"
```

## 📊 Integration Matrix

| Component    | GitHub        | Git Worktree    | SpecPilot     | Logging       |
| ------------ | ------------- | --------------- | ------------- | ------------- |
| **Tasks**    | ✅ Issues     | ✅ Branches     | ✅ Files      | ✅ Operations |
| **Epics**    | ✅ Milestones | ➖ N/A          | ✅ Files      | ✅ Operations |
| **Status**   | ✅ Labels     | ✅ Branch State | ✅ YAML       | ✅ Tracked    |
| **Progress** | ✅ Automated  | ✅ Tracked      | ✅ Calculated | ✅ Logged     |
| **Debug**    | ➖ CLI Output | ➖ Git Output   | ✅ Debug Mode | ✅ Unified    |

## 🔗 Related Resources

- [SpecPilot Documentation](https://github.com/sacahan/SpecPilot)
- [GitHub CLI Manual](https://cli.github.com/manual/)
- [Git Worktree Documentation](https://git-scm.com/docs/git-worktree)

## 💡 Best Practices

1. **Regular Synchronization**: Sync changes frequently to maintain consistency
2. **Atomic Operations**: Use specific sync commands for targeted updates
3. **Status Verification**: Check project status before major operations
4. **Clean Workflows**: Use worktree isolation for all development tasks
5. **Debug Logging**: Enable `SPECPILOT_DEBUG=true` when troubleshooting issues
6. **Log Monitoring**: Check `.specpilot-debug.log` for detailed operation history
