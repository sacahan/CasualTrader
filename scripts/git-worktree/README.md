# Git Worktree Management Scripts

This directory contains scripts for managing Git worktrees to enable isolated development environments for each task. Git worktrees allow multiple working trees to be attached to the same repository, enabling parallel development without interference.

## 📁 File Structure

```txt
scripts/git-worktree/
├── README.md              # This documentation
├── create-worktree.sh     # Create new worktree for task development
├── list-worktrees.sh      # List all active worktrees
├── sync-worktree.sh       # Synchronize worktree with main branch
└── cleanup-worktree.sh    # Remove completed worktrees
```

## 🎯 Purpose

Git worktrees provide:

- **Isolation**: Each task develops in its own workspace
- **Safety**: Main branch remains untouched during development
- **Parallel Development**: Multiple tasks can be worked on simultaneously
- **Clean History**: Clear separation between features
- **Continuity**: AI agents can resume work accurately

## 🚀 Quick Start

### Basic Workflow

```bash
# 1. Create worktree for a task
./scripts/git-worktree/create-worktree.sh task-001

# 2. Switch to the worktree directory
cd workspaces/task-001

# 3. Develop your task (all work happens here)
# - Create/modify files
# - Run tests
# - Make commits

# 4. When done, return to main project
cd ../..

# 5. Clean up the worktree (after PR is merged)
./scripts/git-worktree/cleanup-worktree.sh task-001
```

### Debug Logging

```bash
# Enable detailed logging for worktree operations
export SPECPILOT_DEBUG=true
./scripts/git-worktree/create-worktree.sh task-001

# Monitor worktree operations
tail -f .specpilot-debug.log
```

## 📖 Script Documentation

### create-worktree.sh

Creates a new Git worktree for task development.

```bash
# Usage
./scripts/git-worktree/create-worktree.sh <task-id>

# Example
./scripts/git-worktree/create-worktree.sh task-001

# This creates:
# - Branch: task-001-feature
# - Directory: workspaces/task-001/
# - Clean environment based on main branch
```

**Features:**

- Automatic branch name generation (`task-{id}-feature`)
- Clean workspace setup
- Validation of task-id format
- Error handling for existing worktrees

### list-worktrees.sh

Lists all active worktrees and their status.

```bash
# Usage
./scripts/git-worktree/list-worktrees.sh

# Output shows:
# - Worktree path
# - Associated branch
# - Current status
```

**Information Displayed:**

- Active worktree directories
- Branch associations
- Working directory status
- Commit information

### sync-worktree.sh

Synchronizes a worktree with the latest changes from main branch.

```bash
# Usage
./scripts/git-worktree/sync-worktree.sh <task-id>

# Example
./scripts/git-worktree/sync-worktree.sh task-001
```

**Operations Performed:**

- Fetches latest changes from remote
- Merges main branch changes into task branch
- Resolves any conflicts (with user guidance)
- Updates worktree to latest state

### cleanup-worktree.sh

Removes completed worktrees and cleans up branches.

```bash
# Usage
./scripts/git-worktree/cleanup-worktree.sh <task-id>

# Example
./scripts/git-worktree/cleanup-worktree.sh task-001
```

**Cleanup Operations:**

- Removes worktree directory
- Deletes associated feature branch
- Cleans up Git references
- Validates safe removal

## 🏗️ Directory Structure Created

When you create a worktree for `task-001`, the structure becomes:

```txt
Project Root/
├── .git/                     # Main Git repository
├── src/                      # Main project files (main branch)
├── specs/                    # SpecPilot specifications
├── scripts/                  # Development scripts
│
└── workspaces/               # Worktree workspace directory
    └── task-001/             # Task-specific development environment
        ├── .git              # Git worktree metadata (symlink)
        ├── src/              # Task development happens here
        ├── specs/            # Updated specs during development
        └── scripts/          # Available scripts in worktree
```

## 🔄 Integration with SpecPilot Workflow

### Automatic Integration

The main SpecPilot workflow script (`specpilot-workflow.sh`) automatically uses these worktree tools:

```bash
# Main workflow automatically:
# 1. Creates worktree
# 2. Switches to worktree directory
# 3. Manages development lifecycle
# 4. Handles cleanup after completion

./scripts/specpilot-workflow.sh start-task task-001
```

### Manual Management

For fine-grained control, use worktree scripts directly:

```bash
# Create development environment
./scripts/git-worktree/create-worktree.sh task-001
cd workspaces/task-001

# Check status during development
cd ../..
./scripts/git-worktree/list-worktrees.sh

# Sync with latest changes
./scripts/git-worktree/sync-worktree.sh task-001

# Clean up when done
./scripts/git-worktree/cleanup-worktree.sh task-001
```

## ⚠️ Important Guidelines

### Development Rules

1. **Always work in worktree**: Never develop tasks in main project directory
2. **One task per worktree**: Each task gets its own isolated environment
3. **Regular commits**: Commit frequently to save progress
4. **Sync regularly**: Keep worktree updated with main branch changes

### Safety Practices

```bash
# Always verify you're in the right directory
pwd  # Should show: .../workspaces/task-001

# Check branch before making changes
git branch  # Should show: * task-001-feature

# Verify worktree status
git status  # Should show clean working directory initially
```

### Common Patterns

```bash
# Start new task development
./scripts/git-worktree/create-worktree.sh task-002
cd workspaces/task-002

# Save progress during development
git add .
git commit -m "wip: implement user authentication API"

# Sync with latest main branch changes
cd ../..
./scripts/git-worktree/sync-worktree.sh task-002
cd workspaces/task-002

# Final commit and push
git add .
git commit -m "feat: complete user authentication API"
git push -u origin task-002-feature
```

## 🔧 Configuration

### Prerequisites

```bash
# Git version 2.5+ required for worktree support
git --version

# Verify worktree support
git worktree --help
```

### Environment Setup

```bash
# Ensure clean repository state
git status  # Should be clean

# Verify remote repository connection
git remote -v

# Check available branches
git branch -a
```

## 🔍 Debug and Logging

### Unified Logging System

All git-worktree scripts include comprehensive logging to `.specpilot-debug.log`:

```bash
# Enable debug mode
export SPECPILOT_DEBUG=true

# Run any worktree operation with logging
./scripts/git-worktree/create-worktree.sh task-001

# View detailed logs
cat .specpilot-debug.log
```

### Log Information Tracked

The logging system captures:

- **Script Execution**: Start/end timestamps with success/failure status
- **Operations**: Each Git command and worktree operation
- **Parameters**: Task IDs, branch names, directory paths
- **Errors**: Detailed error messages with context
- **Git Output**: Important Git command results

### Monitoring Worktree Operations

```bash
# Real-time log monitoring
tail -f .specpilot-debug.log

# Filter worktree-specific operations
grep "worktree" .specpilot-debug.log

# Check for errors
grep "ERROR" .specpilot-debug.log

# View script execution history
grep "SCRIPT_" .specpilot-debug.log | tail -10
```

### Example Debug Session

```bash
# Enable debugging
export SPECPILOT_DEBUG=true

# Create worktree with full logging
./scripts/git-worktree/create-worktree.sh task-debug-001

# Check what happened
echo "=== Creation Log ==="
grep "create-worktree" .specpilot-debug.log | tail -5

# List worktrees with logging
./scripts/git-worktree/list-worktrees.sh

# View list operation log
echo "=== List Log ==="
grep "list-worktrees" .specpilot-debug.log | tail -3
```

## 🐛 Troubleshooting

### Common Issues

**Worktree already exists:**

```bash
# Check existing worktrees
./scripts/git-worktree/list-worktrees.sh

# Clean up if needed
./scripts/git-worktree/cleanup-worktree.sh task-001

# Debug with logging enabled
export SPECPILOT_DEBUG=true
./scripts/git-worktree/create-worktree.sh task-001
grep "ERROR.*already exists" .specpilot-debug.log
```

**Branch conflicts:**

```bash
# Check branch status
git branch -a

# Delete problematic branch
git branch -D task-001-feature
git push origin --delete task-001-feature
```

**Sync conflicts:**

```bash
# Manual conflict resolution
cd workspaces/task-001
git status  # Shows conflict files
# Edit files to resolve conflicts
git add .
git commit -m "resolve merge conflicts"

# Debug sync issues with logging
export SPECPILOT_DEBUG=true
cd ../..
./scripts/git-worktree/sync-worktree.sh task-001
grep "sync-worktree" .specpilot-debug.log
```

## 📊 Benefits

| Aspect               | Traditional           | Git Worktree                 |
| -------------------- | --------------------- | ---------------------------- |
| **Development**      | Single workspace      | Multiple isolated workspaces |
| **Branch Switching** | Stash/commit required | Instant switching            |
| **Parallel Work**    | Limited               | Full parallel development    |
| **Safety**           | Risk of conflicts     | Complete isolation           |
| **AI Continuity**    | Context loss possible | Perfect context preservation |
| **Debug Logging**    | Manual tracking       | Unified automatic logging    |

## 🔗 Related Resources

- [Git Worktree Official Documentation](https://git-scm.com/docs/git-worktree)
- [Pro Git Book - Worktrees](https://git-scm.com/book/en/v2/Git-Tools-Worktrees)
- [SpecPilot Workflow Documentation](../README.md)
