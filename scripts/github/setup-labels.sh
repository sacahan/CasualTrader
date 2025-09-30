#!/bin/bash
# GitHub Labels Setup for SpecPilot
# Creates standardized labels for task and epic management
#
# NOTE: This script is optional. Labels are automatically created
# on-demand by github-manager.sh when creating issues/milestones.
# You can run this script if you want to pre-create all labels.

set -e

# Color output functions
red() { echo -e "\033[31m$1\033[0m"; }
green() { echo -e "\033[32m$1\033[0m"; }
yellow() { echo -e "\033[33m$1\033[0m"; }
blue() { echo -e "\033[34m$1\033[0m"; }

blue "Setting up GitHub labels for SpecPilot..."

# Task Status Labels
gh label create "status:new" --description "Task is newly created" --color "f0f8fe" --force
gh label create "status:ready" --description "Task is ready to start" --color "7057ff" --force
gh label create "status:in_progress" --description "Task is currently being worked on" --color "006b75" --force
gh label create "status:review" --description "Task is under review" --color "ff9500" --force
gh label create "status:done" --description "Task is completed" --color "0e8a16" --force
gh label create "status:blocked" --description "Task is blocked" --color "d93f0b" --force

# Priority Labels
gh label create "priority:low" --description "Low priority task" --color "c2e0c6" --force
gh label create "priority:medium" --description "Medium priority task" --color "fbca04" --force
gh label create "priority:high" --description "High priority task" --color "ff9500" --force
gh label create "priority:critical" --description "Critical priority task" --color "d93f0b" --force

# Type Labels
gh label create "type:task" --description "Individual development task" --color "0075ca" --force
gh label create "type:epic" --description "Epic or feature group" --color "5319e7" --force
gh label create "type:bug" --description "Bug fix" --color "d73a4a" --force
gh label create "type:feature" --description "New feature" --color "a2eeef" --force

# Complexity Labels
gh label create "complexity:low" --description "Low complexity task" --color "c5f015" --force
gh label create "complexity:medium" --description "Medium complexity task" --color "fbca04" --force
gh label create "complexity:high" --description "High complexity task" --color "ff6600" --force

# Note: Estimates are included in issue titles/descriptions instead of labels
# This avoids the need to create dynamic labels for varying time estimates

# Agent Type Labels
gh label create "agent:frontend" --description "Frontend development" --color "1d76db" --force
gh label create "agent:backend" --description "Backend development" --color "0052cc" --force
gh label create "agent:backend-expert" --description "Backend expert development" --color "0052cc" --force
gh label create "agent:frontend-expert" --description "Frontend expert development" --color "1d76db" --force
gh label create "agent:fullstack" --description "Full-stack development" --color "5319e7" --force
gh label create "agent:testing" --description "Testing and QA" --color "006b75" --force

green "✅ All labels created successfully!"

echo ""
blue "📋 Label System Overview:"
echo "Status: new → ready → in_progress → review → done"
echo "Priority: low, medium, high, critical"
echo "Type: task, epic, bug, feature"
echo "Complexity: low, medium, high"
echo "Estimates: Included in issue titles/descriptions"
echo "Agents: frontend, backend, backend-expert, frontend-expert, fullstack, testing"
