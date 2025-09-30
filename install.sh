#!/bin/bash

# SpecPilot MCP Server One-click Installation Script
# Version: 1.0.0
# Supported Platforms: macOS, Linux (Debian/Ubuntu/RHEL/CentOS/Fedora/Arch/openSUSE), Windows (manual installation guidance)
# Supported AI Development Frameworks: Claude Code, Codex CLI, Gemini CLI, Cursor IDE, VS Code

set -euo pipefail # Exit immediately on error

# Color definitions
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Constant definitions
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(pwd)" # Current project directory
SPECPILOT_REPO="https://github.com/sacahan/SpecPilot.git"
INSTALL_DIR="$PROJECT_DIR/.specpilot" # Install under project directory
VERSION="0.5.0"
LOG_FILE="$PROJECT_DIR/.specpilot-install.log"

# Output functions
info() {
  echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$LOG_FILE"
}

success() {
  echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

warning() {
  echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
  echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

title() {
  echo -e "${PURPLE}$1${NC}"
}

progress() {
  echo -e "${CYAN}⏳ $1${NC}"
}

# Check if running as root user
check_root() {
  if [[ $EUID -eq 0 ]]; then
    error "Please do not run this script as root user."
    exit 1
  fi
}

# Detect operating system
detect_os() {
  if [[ "$OSTYPE" == "darwin"* ]]; then
    export PLATFORM="macos"
    info "Detected macOS system."
  elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    export PLATFORM="linux"
    info "Detected Linux system."
  elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]] || [[ "$(uname -s)" == MINGW* ]] || [[ "$(uname -s)" == CYGWIN* ]]; then
    export PLATFORM="windows"
    info "Detected Windows system (Git Bash/MSYS/Cygwin)."
    warning "Windows support is limited. Some features may require manual installation."
  else
    error "Unsupported operating system: $OSTYPE"
    info "This script supports macOS, Linux, and Windows (with Git Bash)."
    exit 1
  fi
}

# Check required tools
check_required_tools() {
  local tools=("curl" "git")
  local missing_tools=()

  for tool in "${tools[@]}"; do
    if ! command -v "$tool" &>/dev/null; then
      missing_tools+=("$tool")
    fi
  done

  if [[ ${#missing_tools[@]} -gt 0 ]]; then
    error "Missing required tools: ${missing_tools[*]}"

    # Provide installation guidance for missing tools
    for tool in "${missing_tools[@]}"; do
      case "$tool" in
      "curl")
        info "Install curl: Visit https://curl.se/download.html or use your package manager"
        ;;
      "git")
        info "Install git: Visit https://git-scm.com/downloads or use your package manager"
        ;;
      esac
    done

    error "Please install these tools and rerun the script."
    exit 1
  fi

  # Optional tools check with warnings
  local optional_tools=("gh" "jq")
  local missing_optional=()

  for tool in "${optional_tools[@]}"; do
    if ! command -v "$tool" &>/dev/null; then
      missing_optional+=("$tool")
    fi
  done

  if [[ ${#missing_optional[@]} -gt 0 ]]; then
    warning "Optional tools not found: ${missing_optional[*]}"
    info "These tools enhance the installation experience:"
    for tool in "${missing_optional[@]}"; do
      case "$tool" in
      "gh")
        info "  • GitHub CLI: enables GitHub integration features"
        ;;
      "jq")
        info "  • jq: enables automatic JSON configuration merging"
        info "    Without jq, manual configuration merge will be required"
        ;;
      esac
    done
  fi
}

# Check Node.js version
check_node_version() {
  if ! command -v node &>/dev/null; then
    warning "Node.js not detected, attempting to install..."
    install_nodejs
    return
  fi

  local node_version
  node_version=$(node --version | sed 's/v//')
  local required_version="16.0.0"

  if ! version_ge "$node_version" "$required_version"; then
    warning "Node.js version too low ($node_version), required >= $required_version"
    warning "Attempting to update Node.js..."
    install_nodejs
  else
    success "Node.js version meets requirements: v$node_version"
  fi
}

# Version comparison function
version_ge() {
  [ "$(printf '%s\n' "$1" "$2" | sort -V | head -n1)" = "$2" ]
}

# Install Node.js
install_nodejs() {
  if [[ "$PLATFORM" == "macos" ]]; then
    if command -v brew &>/dev/null; then
      progress "Installing Node.js using Homebrew..."
      brew install node
    else
      warning "Homebrew not found. Please install Node.js manually:"
      info "Option 1: Install Homebrew first: /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
      info "Option 2: Download Node.js from: https://nodejs.org/en/download/"
      info "Option 3: Use Node Version Manager (nvm): curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash"
      exit 1
    fi
  elif [[ "$PLATFORM" == "linux" ]]; then
    # Try to detect Linux distribution
    if command -v apt-get &>/dev/null; then
      # Debian/Ubuntu
      progress "Installing Node.js LTS on Debian/Ubuntu..."
      curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
      sudo apt-get install -y nodejs
    elif command -v yum &>/dev/null; then
      # RHEL/CentOS/Fedora
      progress "Installing Node.js LTS on RHEL/CentOS/Fedora..."
      curl -fsSL https://rpm.nodesource.com/setup_lts.x | sudo bash -
      sudo yum install -y nodejs
    elif command -v dnf &>/dev/null; then
      # Modern Fedora
      progress "Installing Node.js LTS on Fedora..."
      curl -fsSL https://rpm.nodesource.com/setup_lts.x | sudo bash -
      sudo dnf install -y nodejs
    elif command -v pacman &>/dev/null; then
      # Arch Linux
      progress "Installing Node.js on Arch Linux..."
      sudo pacman -S --noconfirm nodejs npm
    elif command -v zypper &>/dev/null; then
      # openSUSE
      progress "Installing Node.js on openSUSE..."
      sudo zypper install -y nodejs npm
    else
      warning "Unsupported Linux distribution. Please install Node.js manually:"
      info "Option 1: Download from: https://nodejs.org/en/download/"
      info "Option 2: Use Node Version Manager (nvm): curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash"
      exit 1
    fi
  elif [[ "$PLATFORM" == "windows" ]]; then
    warning "Windows detected. Please install Node.js manually:"
    info "Option 1: Download from: https://nodejs.org/en/download/"
    info "Option 2: Use Chocolatey: choco install nodejs"
    info "Option 3: Use Windows Package Manager: winget install OpenJS.NodeJS"
    info "After installation, restart your terminal and run this script again."
    exit 1
  else
    error "Unsupported platform. Please manually install Node.js >= 16.0.0."
    info "Download from: https://nodejs.org/en/download/"
    exit 1
  fi
}

# Detect package manager
detect_package_manager() {
  if command -v pnpm &>/dev/null; then
    export PKG_MANAGER="pnpm"
    info "Using package manager: pnpm"
  elif command -v npm &>/dev/null; then
    export PKG_MANAGER="npm"
    info "Using package manager: npm"
    warning "It is recommended to install pnpm for better performance: npm install -g pnpm"
  else
    error "npm or pnpm not found."
    exit 1
  fi
}

# Check Git status
check_git_status() {
  if [[ -d ".git" ]]; then
    success "Git version control detected."

    # Check for uncommitted changes (including untracked files)
    local has_changes=false
    local changes_description=""

    # Check for untracked files
    if [[ -n $(git ls-files --others --exclude-standard) ]]; then
      has_changes=true
      local untracked_count=$(git ls-files --others --exclude-standard | wc -l)
      changes_description+="$untracked_count new files"
    fi

    # Check for modified files
    if ! git diff --quiet; then
      has_changes=true
      if [[ -n "$changes_description" ]]; then changes_description+=", "; fi
      changes_description+="modified files"
    fi

    # Check for staged files
    if ! git diff --cached --quiet; then
      has_changes=true
      if [[ -n "$changes_description" ]]; then changes_description+=", "; fi
      changes_description+="staged files"
    fi

    if [[ "$has_changes" == true ]]; then
      warning "Uncommitted changes detected: $changes_description"
      echo "Options:"
      echo "  1) Continue (existing changes will be included in installation commit)"
      echo "  2) Cancel installation to handle changes manually"
      echo
      read -p "Continue with installation? [Y/n]: " -n 1 -r
      echo
      if [[ $REPLY =~ ^[Nn]$ ]]; then
        info "Installation cancelled. Please commit or stash your changes and run the script again."
        exit 1
      fi
      info "Continuing installation. Existing changes will be included in the installation commit."
    fi
  else
    warning "Git version control not detected."
    read -p "Initialize a Git repository? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
      git init
      success "Git repository initialized."
    fi
  fi
}

# Check GitHub CLI
check_github_cli() {
  if command -v gh &>/dev/null; then
    success "GitHub CLI detected."

    # Check login status
    if gh auth status &>/dev/null; then
      success "GitHub CLI is logged in."
    else
      warning "GitHub CLI is not logged in."
      read -p "Log in to GitHub CLI? (y/N): " -n 1 -r
      echo
      if [[ $REPLY =~ ^[Yy]$ ]]; then
        gh auth login
      fi
    fi
  else
    warning "GitHub CLI not detected."
    read -p "Install GitHub CLI? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
      install_github_cli
    fi
  fi
}

# Check and setup GitHub repository
check_github_repository() {
  # Only proceed if GitHub CLI is available and user is authenticated
  if ! command -v gh &>/dev/null; then
    info "GitHub CLI not available, skipping repository check."
    return 0
  fi

  if ! gh auth status &>/dev/null; then
    info "GitHub CLI not authenticated, skipping repository check."
    return 0
  fi

  progress "Checking GitHub repository setup..."

  # Get repository information
  local repo_name=$(basename "$PROJECT_DIR")
  local git_remote_url=""
  local current_user=""

  # Check if we're in a git repository and get remote URL
  if [[ -d ".git" ]]; then
    git_remote_url=$(git config --get remote.origin.url 2>/dev/null || echo "")
  fi

  # Get current GitHub user
  current_user=$(gh api user --jq '.login' 2>/dev/null || echo "")
  if [[ -z "$current_user" ]]; then
    warning "Could not determine GitHub username."
    return 0
  fi

  local repo_full_name=""
  local repo_owner=""

  # Strategy 1: If remote URL exists, extract repository info from it
  if [[ -n "$git_remote_url" ]]; then
    if [[ "$git_remote_url" =~ github\.com[:/]([^/]+)/([^/]+)(\.git)?$ ]]; then
      repo_owner="${BASH_REMATCH[1]}"
      repo_name="${BASH_REMATCH[2]}"
      # Remove .git suffix if present
      repo_name="${repo_name%.git}"
      repo_full_name="$repo_owner/$repo_name"
      info "Found existing remote: $git_remote_url"
    else
      warning "Could not parse GitHub repository from remote URL: $git_remote_url"
      # Fall back to current user strategy
      repo_owner="$current_user"
      repo_full_name="$current_user/$repo_name"
    fi
  else
    # Strategy 2: No remote configured, check if repo exists under current user
    repo_owner="$current_user"
    repo_full_name="$current_user/$repo_name"
  fi

  if [[ -z "$repo_full_name" ]]; then
    warning "Could not determine repository name, skipping GitHub repository setup."
    return 0
  fi

  info "Checking repository: $repo_full_name"

  # Check if repository exists on GitHub
  if gh repo view "$repo_full_name" >/dev/null 2>&1; then
    success "✅ GitHub repository exists: https://github.com/$repo_full_name"

    # Handle remote configuration
    if [[ -z "$git_remote_url" ]]; then
      info "🔧 No remote origin configured locally, adding remote..."
      git remote add origin "https://github.com/$repo_full_name.git"
      success "✅ Remote origin added: https://github.com/$repo_full_name.git"
    elif [[ "$git_remote_url" != *"$repo_full_name"* ]]; then
      warning "⚠️ Remote URL mismatch detected!"
      echo "Local remote: $git_remote_url"
      echo "GitHub repo: https://github.com/$repo_full_name"
      echo
      echo "Options:"
      echo "  1) Update remote to match GitHub repository"
      echo "  2) Keep existing remote (may cause workflow issues)"
      echo
      read -p "Choose option (1/2): " -n 1 -r choice
      echo
      if [[ "$choice" == "1" ]]; then
        git remote set-url origin "https://github.com/$repo_full_name.git"
        success "✅ Remote origin updated to: https://github.com/$repo_full_name.git"
      else
        warning "⚠️ Keeping existing remote. GitHub workflow features may not work correctly."
      fi
    else
      success "✅ Remote origin correctly configured."
    fi

    # Verify repository access
    if gh repo view "$repo_full_name" --json owner,name,visibility &>/dev/null; then
      local repo_info=$(gh repo view "$repo_full_name" --json owner,name,visibility)
      local visibility=$(echo "$repo_info" | jq -r '.visibility')
      info "Repository visibility: $visibility"
      success "✅ Repository access verified."
    fi

    return 0

  # Repository doesn't exist, check if repo exists under different owner
  elif [[ -n "$git_remote_url" ]] && [[ "$repo_owner" != "$current_user" ]]; then
    warning "⚠️ Repository $repo_full_name not found, but remote points to different owner."
    echo "This might be a:"
    echo "  • Fork that you don't have access to"
    echo "  • Private repository you're not a member of"
    echo "  • Repository that was moved or deleted"
    echo
    echo "Options:"
    echo "  1) Create new repository under your account ($current_user/$repo_name)"
    echo "  2) Update remote to different repository"
    echo "  3) Skip GitHub setup"
    echo
    read -p "Choose option (1/2/3): " -n 1 -r choice
    echo

    case $choice in
    1)
      create_github_repository "$current_user/$repo_name" true
      ;;
    2)
      echo "Please enter the correct repository name (owner/repo):"
      read -p "> " new_repo_name
      if [[ -n "$new_repo_name" ]] && gh repo view "$new_repo_name" >/dev/null 2>&1; then
        git remote set-url origin "https://github.com/$new_repo_name.git"
        success "✅ Remote updated to: https://github.com/$new_repo_name.git"
      else
        warning "Repository not found or invalid format."
      fi
      ;;
    3)
      info "GitHub repository setup skipped."
      ;;
    esac

  else
    # Repository doesn't exist, offer to create it
    warning "⚠️ GitHub repository does not exist: $repo_full_name"
    echo
    echo "SpecPilot workflow scripts require a GitHub repository for:"
    echo "  • Creating pull requests"
    echo "  • Managing feature branches"
    echo "  • Collaborative development workflow"
    echo
    echo "Options:"
    echo "  1) Create repository automatically (private)"
    echo "  2) Create repository automatically (public)"
    echo "  3) Skip (set up manually later)"
    echo
    read -p "Choose option (1/2/3): " -n 1 -r choice
    echo

    case $choice in
    1)
      create_github_repository "$repo_full_name" true
      ;;
    2)
      create_github_repository "$repo_full_name" false
      ;;
    3)
      info "Repository creation skipped."
      warning "Note: GitHub workflow features will require manual repository setup."
      echo "To create later, run: gh repo create $repo_full_name"
      ;;
    *)
      warning "Invalid choice, skipping repository creation."
      ;;
    esac
  fi
}

# Create GitHub repository
create_github_repository() {
  local repo_full_name="$1"
  local is_private="$2"

  progress "Creating GitHub repository: $repo_full_name"

  local visibility_flag=""
  if [[ "$is_private" == "true" ]]; then
    visibility_flag="--private"
    info "Creating private repository..."
  else
    visibility_flag="--public"
    info "Creating public repository..."
  fi

  local description="SpecPilot project: AI-driven specification and task management"

  # Create repository
  if gh repo create "$repo_full_name" $visibility_flag --description "$description"; then
    success "✅ Repository created successfully: https://github.com/$repo_full_name"

    # Set up remote if not already configured
    if ! git config --get remote.origin.url >/dev/null 2>&1; then
      info "Adding remote origin..."
      git remote add origin "https://github.com/$repo_full_name.git"
      success "Remote origin added."
    fi

    # Create initial commit if repository is empty
    if [[ -d ".git" ]]; then
      # Check if we have any commits
      if ! git rev-parse HEAD >/dev/null 2>&1; then
        info "Creating initial commit..."

        # Create a basic README if it doesn't exist
        if [[ ! -f "README.md" ]]; then
          cat >"README.md" <<EOF
# $(basename "$PROJECT_DIR")

This project uses SpecPilot for AI-driven specification and task management.

## Quick Start

\`\`\`bash
# Set environment variable
export SPECROOT="\$(pwd)"

# Initialize project structure
# (Run this from your AI development tool with SpecPilot MCP server)
\`\`\`

## SpecPilot Tools

- \`project-init\`: Initialize project structure
- \`prd-generate\`: Generate Product Requirements
- \`tsd-generate\`: Generate Technical Specifications
- \`epic-generate\`: Generate development epics
- \`task-generate\`: Generate development tasks
- \`project-status\`: Check project progress
- \`next-action\`: Get next action recommendations

## Workflow

1. **Requirements**: Use \`prd-generate\` to create product requirements
2. **Technical Design**: Use \`tsd-generate\` for technical specifications
3. **Development Planning**: Use \`epic-generate\` and \`task-generate\`
4. **Execution**: Use workflow scripts for git branching and GitHub integration

For more information, visit: https://github.com/sacahan/SpecPilot
EOF
          git add README.md
        fi

        # Add any existing files
        git add .
        git commit -m "Initial commit: Set up SpecPilot project

🤖 Generated with SpecPilot installation script
Repository created for AI-driven development workflow"

        # Push to remote
        info "Pushing initial commit..."
        git push -u origin main
        success "Initial commit pushed to GitHub."
      else
        # Repository has commits, just push current branch
        local current_branch=$(git branch --show-current)
        if [[ -n "$current_branch" ]]; then
          info "Pushing $current_branch to remote..."
          git push -u origin "$current_branch"
          success "Current branch pushed to GitHub."
        fi
      fi
    fi

    success "🎉 GitHub repository setup completed!"
    info "Repository URL: https://github.com/$repo_full_name"

  else
    error "Failed to create GitHub repository."
    warning "You can create it manually later with: gh repo create $repo_full_name"
    return 1
  fi
}

# Note: GitHub labels setup is now handled automatically by github-manager.sh
# Labels are created on-demand when first issue/milestone is created

# Install GitHub CLI
install_github_cli() {
  if [[ "$PLATFORM" == "macos" ]]; then
    if command -v brew &>/dev/null; then
      progress "Installing GitHub CLI using Homebrew..."
      brew install gh
    else
      warning "Homebrew not found. Please install GitHub CLI manually:"
      info "Option 1: Install Homebrew first, then: brew install gh"
      info "Option 2: Download from: https://github.com/cli/cli/releases"
      return 1
    fi
  elif [[ "$PLATFORM" == "linux" ]]; then
    if command -v apt-get &>/dev/null; then
      # Debian/Ubuntu
      progress "Installing GitHub CLI on Debian/Ubuntu..."
      curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
      echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list >/dev/null
      sudo apt update
      sudo apt install -y gh
    elif command -v yum &>/dev/null; then
      # RHEL/CentOS
      progress "Installing GitHub CLI on RHEL/CentOS..."
      sudo yum install -y yum-utils
      sudo yum-config-manager --add-repo https://cli.github.com/packages/rpm/gh-cli.repo
      sudo yum install -y gh
    elif command -v dnf &>/dev/null; then
      # Fedora
      progress "Installing GitHub CLI on Fedora..."
      sudo dnf install -y 'dnf-command(config-manager)'
      sudo dnf config-manager --add-repo https://cli.github.com/packages/rpm/gh-cli.repo
      sudo dnf install -y gh
    elif command -v pacman &>/dev/null; then
      # Arch Linux
      progress "Installing GitHub CLI on Arch Linux..."
      sudo pacman -S --noconfirm github-cli
    elif command -v zypper &>/dev/null; then
      # openSUSE
      progress "Installing GitHub CLI on openSUSE..."
      sudo zypper addrepo https://cli.github.com/packages/rpm/gh-cli.repo
      sudo zypper refresh
      sudo zypper install -y gh
    else
      warning "Unsupported Linux distribution. Please install GitHub CLI manually:"
      info "Download from: https://github.com/cli/cli/releases"
      return 1
    fi
  elif [[ "$PLATFORM" == "windows" ]]; then
    warning "Windows detected. Please install GitHub CLI manually:"
    info "Option 1: Download from: https://github.com/cli/cli/releases"
    info "Option 2: Use Chocolatey: choco install gh"
    info "Option 3: Use Windows Package Manager: winget install GitHub.cli"
    return 1
  else
    warning "Unsupported platform. Please install GitHub CLI manually:"
    info "Download from: https://github.com/cli/cli/releases"
    return 1
  fi
}

# Detect AI development tools
detect_ai_tools() {
  local detected_tools=()

  # Check Claude Code
  if command -v claude &>/dev/null; then
    detected_tools+=("claude")
  fi

  # Check Cursor
  if command -v cursor &>/dev/null || [[ -d "/Applications/Cursor.app" ]]; then
    detected_tools+=("cursor")
  fi

  # Check OpenAI Codex
  if command -v codex &>/dev/null || [[ -f "$HOME/.codex/config.toml" ]] || [[ -n "${OPENAI_API_KEY:-}" ]]; then
    detected_tools+=("codex")
  fi

  # Check VS Code
  if command -v code &>/dev/null || [[ -d "/Applications/Visual Studio Code.app" ]]; then
    detected_tools+=("vscode")
  fi

  # Check Gemini CLI
  if command -v gemini &>/dev/null || command -v google-cloud-cli &>/dev/null; then
    detected_tools+=("gemini")
  fi

  # Handle empty array case for set -u mode
  # Always initialize the array first as global variable
  DETECTED_AI_TOOLS=()

  if [[ ${#detected_tools[@]} -gt 0 ]]; then
    # Create array safely by iterating
    for tool in "${detected_tools[@]}"; do
      DETECTED_AI_TOOLS+=("$tool")
    done
    success "Detected AI development tools: ${detected_tools[*]}"
  else
    warning "No supported AI development tools detected."
  fi
}

# Show installation options
show_install_options() {
  title "MCP installation - Please select which AI development tool to auto-configure:"
  echo

  local options=()

  # Check for detected tools more safely
  local detected_tools_str=""
  # Ensure DETECTED_AI_TOOLS is initialized before use
  if [[ -n "${DETECTED_AI_TOOLS+x}" ]] && [[ ${#DETECTED_AI_TOOLS[@]} -gt 0 ]]; then
    detected_tools_str="${DETECTED_AI_TOOLS[*]}"
  fi

  if [[ " $detected_tools_str " =~ " claude " ]]; then
    options+=("1" "Claude Code")
  fi

  if [[ " $detected_tools_str " =~ " cursor " ]]; then
    options+=("2" "Cursor IDE")
  fi

  if [[ " $detected_tools_str " =~ " codex " ]]; then
    options+=("3" "Codex CLI")
  fi

  if [[ " $detected_tools_str " =~ " vscode " ]]; then
    options+=("4" "VS Code")
  fi

  if [[ " $detected_tools_str " =~ " gemini " ]]; then
    options+=("5" "Gemini CLI")
  fi

  options+=("6" "Manual configuration (show JSON settings)")
  options+=("0" "Install all")

  for ((i = 0; i < ${#options[@]}; i += 2)); do
    echo "  ${options[$i]}) ${options[$((i + 1))]}"
  done

  echo
  read -p "Please select (0-6): " -n 1 -r choice
  echo

  export INSTALL_CHOICE="$choice"
}

# Install SpecPilot
install_specpilot() {
  progress "Downloading SpecPilot..."

  # Backup if target directory exists
  if [[ -d "$INSTALL_DIR" ]]; then
    warning "$INSTALL_DIR directory already exists, backing up..."
    mv "$INSTALL_DIR" "${INSTALL_DIR}.backup.$(date +%Y%m%d_%H%M%S)"
  fi

  if [[ -d "./specs" ]]; then
    warning "specs/ directory already exists, backing up..."
    mv "./specs" "./specs.backup.$(date +%Y%m%d_%H%M%S)"
  fi

  if [[ -d "./workspaces" ]]; then
    warning "workspaces/ directory already exists, backing up..."
    mv "./workspaces" "./workspaces.backup.$(date +%Y%m%d_%H%M%S)"
  fi

  if [[ -d "./scripts" ]]; then
    warning "scripts/ directory already exists, backing up..."
    mv "./scripts" "./scripts.backup.$(date +%Y%m%d_%H%M%S)"
  fi

  # Clone project
  git clone "$SPECPILOT_REPO" "$INSTALL_DIR"
  cd "$INSTALL_DIR"

  progress "Installing dependencies..."
  $PKG_MANAGER install

  progress "Compiling Project..."
  $PKG_MANAGER run build

  progress "Cleaning up unnecessary files..."
  cleanup_installation

  success "SpecPilot installation completed."
}

# Clean up unnecessary files after installation
cleanup_installation() {
  # Keep only essential files and directories for MCP server runtime
  local essential_dirs=("dist" "configs" "node_modules" "scripts")
  local essential_files=("package.json")

  # No longer keep GitHub workflow files (manual management preferred)
  local github_keep_items=()

  # Remove development and documentation files/directories
  local remove_items=(
    "src"
    "tests"
    ".git"
    ".vscode"
    ".claude"
    "coverage"
    "README.md"
    "CLAUDE.md"
    "INSTALLATION.md"
    "install.sh"
    "tsconfig.json"
    "vitest.config.ts"
    ".gitignore"
    ".editorconfig"
    "pnpm-workspace.yaml"
    ".env"
    ".DS_Store"
    "Claude Code PM.txt"
    ".specpilot-install.log"
    "package-lock.json"
    "pnpm-lock.yaml"
  )

  # Remove .github directory selectively (keep essential GitHub integration files)
  if [[ -d ".github" ]]; then
    # Create temporary directory to preserve essential files
    local temp_github_dir="/tmp/specpilot-github-backup"
    mkdir -p "$temp_github_dir"

    # Backup essential GitHub files
    if [[ ${#github_keep_items[@]} -gt 0 ]]; then
      for item in "${github_keep_items[@]}"; do
        if [[ -f "$item" ]]; then
          local item_dir=$(dirname "$item")
          mkdir -p "$temp_github_dir/$item_dir"
          cp "$item" "$temp_github_dir/$item"
          info "Preserving GitHub integration file: $item"
        fi
      done
    fi

    # Remove original .github directory
    rm -rf ".github"
    info "Removed .github directory (except essential files)"

    # Restore essential files
    if [[ -d "$temp_github_dir/.github" ]]; then
      cp -r "$temp_github_dir/.github" "./"
      success "Restored essential GitHub integration files"
    fi

    # Cleanup temporary directory
    rm -rf "$temp_github_dir"
  fi

  local removed_count=0
  local total_removed_size=0

  for item in "${remove_items[@]}"; do
    if [[ -e "$item" ]]; then
      # Get size before removal (for reporting) - simplified to avoid fork issues
      if command -v du &>/dev/null; then
        local item_size=0
        if [[ -f "$item" ]]; then
          # For files, get size more efficiently
          item_size=$(wc -c <"$item" 2>/dev/null | awk '{print int($1/1024+1)}' || echo "0")
        elif [[ -d "$item" ]]; then
          # For directories, skip size calculation to avoid fork issues
          item_size=0
        fi
        total_removed_size=$((total_removed_size + item_size))
      fi

      rm -rf "$item"
      info "Removed: $item"
      removed_count=$((removed_count + 1))
    fi
  done

  # Verify essential directories exist
  local missing_dirs=()
  for dir in "${essential_dirs[@]}"; do
    if [[ ! -d "$dir" ]]; then
      missing_dirs+=("$dir")
      warning "Essential directory missing: $dir"
    fi
  done

  # Verify essential files exist
  for file in "${essential_files[@]}"; do
    if [[ ! -f "$file" ]]; then
      warning "Essential file missing: $file"
    fi
  done

  # Make script files executable - use simpler approach to avoid fork issues
  if [[ -d "${PROJECT_DIR}/scripts" ]]; then
    progress "Making script files executable..."
    # Use a simpler approach that doesn't require as many forks
    for script_dir in "${PROJECT_DIR}/scripts"/*; do
      if [[ -d "$script_dir" ]]; then
        for script in "$script_dir"/*.sh; do
          if [[ -f "$script" ]]; then
            chmod +x "$script"
          fi
        done
      fi
    done
    # Also handle direct scripts in scripts/ directory
    for script in "${PROJECT_DIR}/scripts"/*.sh; do
      if [[ -f "$script" ]]; then
        chmod +x "$script"
      fi
    done
    success "Script files made executable"
  fi

  # Report cleanup results
  if [[ $removed_count -gt 0 ]]; then
    success "Cleaned up $removed_count unnecessary items"
    if [[ $total_removed_size -gt 0 ]]; then
      local removed_mb=$((total_removed_size / 1024))
      info "Freed approximately ${removed_mb}MB of disk space"
    fi
  fi

  # Show final installation size and contents - simplified to avoid fork issues
  info "Installation cleanup completed"

  # List remaining contents for verification (without size calculation to avoid fork issues)
  info "Remaining installation contents:"
  for dir in "${essential_dirs[@]}"; do
    if [[ -d "$dir" ]]; then
      info "  📁 $dir/"
    fi
  done

  for file in "${essential_files[@]}"; do
    if [[ -f "$file" ]]; then
      info "  📄 $file"
    fi
  done

  # GitHub workflow files are no longer automatically installed
  # Users should manually configure GitHub integration using scripts/github-manager.sh
}

# Set project environment variables
setup_environment() {
  progress "Setting project environment variables..."

  # Set environment variables for current session
  export SPECROOT="$PROJECT_DIR"
  # export SPECPILOT_SERVER_PATH="$INSTALL_DIR"

  # Create .env file
  local env_file="$PROJECT_DIR/.env"
  if [[ ! -f "$env_file" ]] || ! grep -q "SPECROOT" "$env_file" 2>/dev/null; then
    echo "# SpecPilot MCP Server environment variables" >>"$env_file"
    echo "SPECROOT=\"$PROJECT_DIR\"" >>"$env_file"
    # echo "SPECPILOT_SERVER_PATH=\"$INSTALL_DIR\"" >>"$env_file"
    success ".env file created."
  else
    info "Environment variables already set in .env file."
  fi

  # Note: Comprehensive verification script already exists as verify-mcp-server.sh
  info "Use ./verify-mcp-server.sh for comprehensive installation verification"
}

# Initialize project directory structure
init_project_structure() {
  progress "Initializing project directory structure..."

  cd "$PROJECT_DIR"
  # Create directory structure
  mkdir -p specs/{prd,tsd,epics,tasks}
  mkdir workspaces

  # Copy verification script to project root
  mv $INSTALL_DIR/verify-mcp-server.sh .
  chmod +x verify-mcp-server.sh
  # Copy workflow scripts to project root
  mv $INSTALL_DIR/scripts .
  # Make scripts executable
  find ./scripts -name "*.sh" -type f -exec chmod +x {} \;

  # Create or update .gitignore entries
  local gitignore_file="$PROJECT_DIR/.gitignore"
  if [[ -f "$gitignore_file" ]]; then
    if ! grep -q ".specpilot" "$gitignore_file"; then
      echo "" >>"$gitignore_file"
      echo "# SpecPilot MCP Server" >>"$gitignore_file"
      echo ".specpilot/" >>"$gitignore_file"
      echo ".specpilot-install.log" >>"$gitignore_file"
      info ".gitignore updated."
    fi
  else
    # Create new .gitignore file with SpecPilot entries
    cat >"$gitignore_file" <<EOF
# SpecPilot MCP Server
.specpilot/
.specpilot-install.log
.specpilot-debug.log
workspaces/

# Node.js
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Environment variables
.env
.env.local
.env.development.local
.env.test.local
.env.production.local

# OS generated files
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db
EOF
    success ".gitignore created."
  fi

  success "Project directory structure initialization completed."
}

# Test installation
test_installation() {
  progress "Testing SpecPilot installation..."

  cd "$INSTALL_DIR"

  # Test if compilation was successful
  if [[ ! -f "dist/index.js" ]]; then
    error "Compiled file does not exist."
    return 1
  fi

  # Test basic functionality
  export SPECROOT="$PROJECT_DIR"
  if timeout 10s node dist/index.js 2>/dev/null; then
    success "✅ SpecPilot MCP server test passed."
  else
    local exit_code=$?
    if [[ $exit_code -eq 124 ]]; then
      success "✅ SpecPilot MCP server can start normally (timeout is expected behavior)."
    else
      warning "⚠️ SpecPilot test failed, but this does not affect installation."
      info "After installation, please run ./verify-mcp-server.sh for full verification."
    fi
  fi

  cd "$PROJECT_DIR"
}

# Generate MCP config from template file
generate_mcp_config() {
  local tool="$1"
  local config_template=""

  # Use local template file or download from GitHub
  local template_file=""

  case "$tool" in
  "claude")
    template_file="claude.json"
    ;;
  "cursor")
    template_file="cursor.json"
    ;;
  "codex")
    template_file="codex.toml"
    ;;
  "vscode")
    template_file="vscode.json"
    ;;
  "gemini")
    template_file="gemini.json"
    ;;
  *)
    template_file="claude.json" # Default to Claude Code format
    ;;
  esac

  # Try to read from local configs directory (after installation)
  local config_file_path="$INSTALL_DIR/configs/$template_file"
  if [[ -f "$config_file_path" ]]; then
    config_template=$(cat "$config_file_path")
  else
    # Use fallback config if template not available
    warning "⚠️ Config template file not found, using fallback configuration"
    config_template=$(generate_fallback_config "$tool")
  fi

  # Replace placeholders
  config_template=${config_template//\{\{INSTALL_DIR\}\}/$INSTALL_DIR}
  config_template=${config_template//\{\{PROJECT_DIR\}\}/$PROJECT_DIR}

  echo "$config_template"
}

# Generate fallback config (when template file cannot be fetched)
generate_fallback_config() {
  local tool="$1"

  case "$tool" in
  "claude")
    cat <<EOF
{
  "mcpServers": {
    "specpilot": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "--prefix", "$INSTALL_DIR", "specpilot-mcp-server"],
      "env": {
        "SPECROOT": "$PROJECT_DIR"
      }
    }
  }
}
EOF
    ;;
  "cursor")
    cat <<EOF
{
  "mcp": {
    "servers": {
      "specpilot": {
        "command": "npx",
        "args": ["-y", "--prefix", "$INSTALL_DIR", "specpilot-mcp-server"],
        "env": {
          "SPECROOT": "$PROJECT_DIR"
        }
      }
    }
  }
}
EOF
    ;;
  "codex")
    cat <<EOF
[mcp_servers.specpilot]
command = "npx"
args = ["-y", "--prefix", "$INSTALL_DIR", "specpilot-mcp-server"]
env = { "SPECROOT" = "$PROJECT_DIR" }
EOF
    ;;
  "vscode")
    cat <<EOF
{
  "servers": {
    "specpilot": {
      "command": "npx",
      "args": ["-y", "--prefix", "$INSTALL_DIR", "specpilot-mcp-server"],
      "env": {
        "SPECROOT": "$PROJECT_DIR"
      }
    }
  }
}
EOF
    ;;
  "gemini")
    cat <<EOF
{
  "mcpServers": {
    "specpilot": {
      "command": "npx",
      "args": ["-y", "--prefix", "$INSTALL_DIR", "specpilot-mcp-server"],
      "env": {
        "SPECROOT": "$PROJECT_DIR"
      }
    }
  }
}
EOF
    ;;
  *)
    generate_fallback_config "claude"
    ;;
  esac
}

# Handle installation choice
handle_install_choice() {
  case "$INSTALL_CHOICE" in
  "1" | "2" | "3" | "4" | "5")
    local tools=("claude" "cursor" "codex" "vscode" "gemini")
    local selected_tool="${tools[$((INSTALL_CHOICE - 1))]}"
    install_mcp_config "$selected_tool"
    ;;
  "6")
    show_manual_config
    ;;
  "0")
    if [[ -n "${DETECTED_AI_TOOLS+x}" ]] && [[ ${#DETECTED_AI_TOOLS[@]} -gt 0 ]]; then
      for tool in "${DETECTED_AI_TOOLS[@]}"; do
        install_mcp_config "$tool"
      done
    else
      warning "No AI tools detected for installation."
    fi
    ;;
  *)
    warning "Invalid selection."
    ;;
  esac
}

# Install MCP config safely with backup and merge support
install_mcp_config() {
  local tool="$1"
  local config_dir=""
  local config_file=""

  case "$tool" in
  "claude")
    config_dir="$PROJECT_DIR"
    config_file=".mcp.json"
    ;;
  "cursor")
    config_dir="$PROJECT_DIR/.cursor"
    config_file="mcp.json"
    ;;
  "codex")
    config_dir="$PROJECT_DIR/.codex"
    config_file="config.toml"
    ;;
  "vscode")
    config_dir="$PROJECT_DIR/.vscode"
    config_file="mcp.json"
    ;;
  "gemini")
    config_dir="$PROJECT_DIR/.gemini"
    config_file="settings.json"
    ;;
  *)
    warning "Unsupported tool: $tool"
    return
    ;;
  esac

  progress "Installing $tool MCP config..."

  # Create config directory if not exists
  mkdir -p "$config_dir"

  local config_path="$config_dir/$config_file"
  local config_content
  config_content=$(generate_mcp_config "$tool")

  # Check if config file already exists
  if [[ -f "$config_path" ]]; then
    # Create backup with timestamp
    local backup_path="${config_path}.backup.$(date +%Y%m%d_%H%M%S)"
    cp "$config_path" "$backup_path"
    success "Existing config backed up to: $backup_path"

    # Check if SpecPilot is already configured (for JSON files)
    if [[ "$config_file" == *.json ]]; then
      if grep -q "specpilot" "$config_path" 2>/dev/null; then
        warning "SpecPilot configuration already exists in $config_path"
        echo
        echo "Options:"
        echo "  1) Keep existing configuration (skip)"
        echo "  2) Replace with new configuration"
        echo "  3) Show manual merge instructions"
        echo
        read -p "Please select (1-3): " -n 1 -r choice
        echo

        case "$choice" in
        "1")
          info "Keeping existing configuration."
          return
          ;;
        "2")
          info "Replacing with new configuration..."
          ;;
        "3")
          show_merge_instructions "$tool" "$config_path" "$config_content"
          return
          ;;
        *)
          warning "Invalid selection, keeping existing configuration."
          return
          ;;
        esac
      else
        info "Merging SpecPilot config with existing configuration..."
        merge_config "$config_path" "$config_content" "$tool" "$config_file"
        return
      fi
    else
      # Handle TOML files (Codex)
      if grep -q "specpilot" "$config_path" 2>/dev/null; then
        warning "SpecPilot configuration already exists in $config_path"
        echo
        echo "Options:"
        echo "  1) Keep existing configuration (skip)"
        echo "  2) Replace with new configuration"
        echo "  3) Show manual merge instructions"
        echo
        read -p "Please select (1-3): " -n 1 -r choice
        echo

        case "$choice" in
        "1")
          info "Keeping existing configuration."
          return
          ;;
        "2")
          info "Replacing with new configuration..."
          ;;
        "3")
          show_merge_instructions "$tool" "$config_path" "$config_content"
          return
          ;;
        *)
          warning "Invalid selection, keeping existing configuration."
          return
          ;;
        esac
      else
        info "Merging SpecPilot config with existing configuration..."
        merge_config "$config_path" "$config_content" "$tool" "$config_file"
        return
      fi
    fi
  fi

  # Write new config (either new file or user chose to replace)
  echo "$config_content" >"$config_path"
  success "$tool MCP config installed to $config_path."
}

# Merge SpecPilot config into existing configuration
merge_config() {
  local config_path="$1"
  local new_config_content="$2"
  local tool="$3"
  local config_file="$4"

  # Handle TOML files (Codex)
  if [[ "$config_file" == *.toml ]]; then
    merge_toml_config "$config_path" "$new_config_content" "$tool"
    return
  fi

  # Handle JSON files
  if command -v jq &>/dev/null; then
    merge_json_config "$config_path" "$new_config_content" "$tool"
  else
    warning "jq not available for automatic JSON merging. Showing manual instructions instead."
    show_merge_instructions "$tool" "$config_path" "$new_config_content"
  fi
}

# Merge SpecPilot config into existing JSON configuration
merge_json_config() {
  local config_path="$1"
  local new_config_content="$2"
  local tool="$3"

  # Extract SpecPilot server config from new config
  local specpilot_config
  case "$tool" in
  "claude")
    specpilot_config=$(echo "$new_config_content" | jq '.mcpServers.specpilot')
    # Merge into existing config
    if jq -e '.mcpServers' "$config_path" &>/dev/null; then
      jq --argjson specpilot "$specpilot_config" '.mcpServers.specpilot = $specpilot' "$config_path" >"${config_path}.tmp" && mv "${config_path}.tmp" "$config_path"
    else
      jq --argjson specpilot "$specpilot_config" '. + {"mcpServers": {"specpilot": $specpilot}}' "$config_path" >"${config_path}.tmp" && mv "${config_path}.tmp" "$config_path"
    fi
    ;;
  "cursor")
    specpilot_config=$(echo "$new_config_content" | jq '.mcpServers.specpilot')
    # Handle Cursor's mcpServers structure
    if jq -e '.mcpServers' "$config_path" &>/dev/null; then
      jq --argjson specpilot "$specpilot_config" '.mcpServers.specpilot = $specpilot' "$config_path" >"${config_path}.tmp" && mv "${config_path}.tmp" "$config_path"
    else
      jq --argjson specpilot "$specpilot_config" '. + {"mcpServers": {"specpilot": $specpilot}}' "$config_path" >"${config_path}.tmp" && mv "${config_path}.tmp" "$config_path"
    fi
    ;;
  "vscode")
    specpilot_config=$(echo "$new_config_content" | jq '.["servers"].specpilot')
    # Handle VS Code's servers structure
    if jq -e '.["servers"]' "$config_path" &>/dev/null; then
      jq --argjson specpilot "$specpilot_config" '.["servers"].specpilot = $specpilot' "$config_path" >"${config_path}.tmp" && mv "${config_path}.tmp" "$config_path"
    else
      jq --argjson specpilot "$specpilot_config" '. + {"servers": {"specpilot": $specpilot}}' "$config_path" >"${config_path}.tmp" && mv "${config_path}.tmp" "$config_path"
    fi
    ;;
  "gemini")
    specpilot_config=$(echo "$new_config_content" | jq '.mcpServers.specpilot')
    # Handle Gemini's mcpServers structure
    if jq -e '.mcpServers' "$config_path" &>/dev/null; then
      jq --argjson specpilot "$specpilot_config" '.mcpServers.specpilot = $specpilot' "$config_path" >"${config_path}.tmp" && mv "${config_path}.tmp" "$config_path"
    else
      jq --argjson specpilot "$specpilot_config" '. + {"mcpServers": {"specpilot": $specpilot}}' "$config_path" >"${config_path}.tmp" && mv "${config_path}.tmp" "$config_path"
    fi
    ;;
  esac
  success "SpecPilot configuration merged successfully."
}

# Merge SpecPilot config into existing TOML configuration
merge_toml_config() {
  local config_path="$1"
  local new_config_content="$2"
  local tool="$3"

  # Check if SpecPilot configuration already exists
  if grep -q "\\[mcp_servers.specpilot\\]" "$config_path" 2>/dev/null; then
    warning "SpecPilot configuration already exists in TOML file."
    info "Please manually check and update the configuration if needed."
    return
  fi

  # For Codex TOML format, append the SpecPilot configuration
  case "$tool" in
  "codex")
    # Add SpecPilot section to TOML file
    echo "" >>"$config_path"
    echo "[mcp_servers.specpilot]" >>"$config_path"
    echo "command = \"npx\"" >>"$config_path"
    echo "args = [\"-y\", \"--prefix\", \"{{INSTALL_DIR}}\", \"specpilot-mcp-server\"]" >>"$config_path"
    echo "env = { \"SPECROOT\" = \"{{PROJECT_DIR}}\" }" >>"$config_path"
    success "SpecPilot configuration appended to Codex TOML file."
    ;;
  *)
    warning "Unknown TOML configuration format for tool: $tool"
    info "Please manually add the configuration."
    show_toml_merge_instructions "$tool" "$config_path"
    ;;
  esac
}

# Show manual merge instructions
show_merge_instructions() {
  local tool="$1"
  local config_path="$2"
  local new_config="$3"

  title "Manual Configuration Merge Instructions:"
  echo
  echo "Your existing configuration file: $config_path"
  echo "Please manually add the following SpecPilot configuration:"
  echo
  echo "--- SpecPilot Configuration to Add ---"

  case "$tool" in
  "claude")
    echo "Add this inside your existing 'mcpServers' object:"
    echo "$new_config" | jq '.mcpServers.specpilot'
    ;;
  "cursor")
    echo "Add this inside your existing 'servers' object:"
    echo "$new_config" | jq '.servers.specpilot' 2>/dev/null || echo "$new_config"
    ;;
  "vscode")
    echo "Add this inside your existing 'servers' object:"
    echo "$new_config" | jq '.["servers"].specpilot' 2>/dev/null || echo "$new_config"
    ;;
  "gemini")
    echo "Add this inside your existing 'mcpServers' object:"
    echo "$new_config" | jq '.mcpServers.specpilot' 2>/dev/null || echo "$new_config"
    ;;
  esac

  echo "--- End Configuration ---"
  echo
  warning "Please backup your existing configuration before making changes."
  info "After manual merge, you can test the configuration with: npx specpilot-mcp-server"
}

# Show manual TOML merge instructions
show_toml_merge_instructions() {
  local tool="$1"
  local config_path="$2"

  title "Manual TOML Configuration Merge Instructions:"
  echo
  echo "Your existing configuration file: $config_path"
  echo "Please manually add the following SpecPilot configuration:"
  echo
  echo "--- SpecPilot TOML Configuration to Add ---"
  echo "[mcp_servers.specpilot]"
  echo "command = \"npx\""
  echo "args = [\"-y\", \"--prefix\", \"{{INSTALL_DIR}}\", \"specpilot-mcp-server\"]"
  echo "env = { \"SPECROOT\" = \"{{PROJECT_DIR}}\" }"
  echo "--- End Configuration ---"
  echo
  warning "Please backup your existing configuration before making changes."
  info "After manual merge, you can test the configuration with: npx specpilot-mcp-server"
}

# Show manual config
show_manual_config() {
  title "Manual configuration JSON:"
  echo
  echo "Please add the following JSON config to your AI tool configuration file:"
  echo
  echo "$(generate_mcp_config "manual" | sed "s|{{SPECROOT}}|$PROJECT_DIR|g")"
  echo
}

# Auto-commit installation changes
auto_commit_installation() {
  # Check if we're in a git repository
  if [[ ! -d ".git" ]]; then
    info "Not in a git repository, skipping auto-commit."
    return 0
  fi

  progress "Committing SpecPilot installation changes..."

  # Check if there are any changes to commit (including untracked files)
  local has_untracked_files=false
  local has_modified_files=false
  local has_staged_files=false

  # Check for untracked files
  if [[ -n $(git ls-files --others --exclude-standard) ]]; then
    has_untracked_files=true
  fi

  # Check for modified tracked files
  if ! git diff --quiet; then
    has_modified_files=true
  fi

  # Check for staged files
  if ! git diff --cached --quiet; then
    has_staged_files=true
  fi

  # If no changes at all, skip commit
  if [[ "$has_untracked_files" == false ]] && [[ "$has_modified_files" == false ]] && [[ "$has_staged_files" == false ]]; then
    info "No changes to commit."
    return 0
  fi

  # Report what types of changes were found
  local changes_summary=""
  if [[ "$has_untracked_files" == true ]]; then
    local untracked_count=$(git ls-files --others --exclude-standard | wc -l)
    changes_summary+="$untracked_count new files"
  fi
  if [[ "$has_modified_files" == true ]]; then
    if [[ -n "$changes_summary" ]]; then changes_summary+=", "; fi
    changes_summary+="modified files"
  fi
  if [[ "$has_staged_files" == true ]]; then
    if [[ -n "$changes_summary" ]]; then changes_summary+=", "; fi
    changes_summary+="staged files"
  fi

  info "Found changes to commit: $changes_summary"

  # Add all installation-related files
  git add .

  # Create a comprehensive commit message
  local commit_message="feat: Add SpecPilot MCP server installation

🚀 SpecPilot v$VERSION installation completed

## Installation Summary:
- SpecPilot MCP server installed in .specpilot/
- Project structure initialized (specs/, configs/)
- Environment variables configured (.env)
- AI tool configurations added"

  # Add detected AI tools to commit message
  if [[ -n "${DETECTED_AI_TOOLS+x}" ]] && [[ ${#DETECTED_AI_TOOLS[@]} -gt 0 ]]; then
    commit_message+="
- AI tools configured: ${DETECTED_AI_TOOLS[*]}"
  fi

  # Add GitHub repository info if available
  if command -v gh &>/dev/null && gh auth status &>/dev/null 2>&1; then
    local repo_url=$(git config --get remote.origin.url 2>/dev/null || echo "")
    if [[ -n "$repo_url" ]]; then
      commit_message+="
- GitHub repository: $repo_url"
    fi
  fi

  commit_message+="

## Ready for development workflow:
- Use 'scripts/specpilot-workflow.sh start-task <task-id>' to begin
- All MCP tools available for AI-driven development
- Project state clean and ready for feature branches

🤖 Generated with SpecPilot installation script
Co-Authored-By: SpecPilot <noreply@anthropic.com>"

  # Commit changes
  if git commit -m "$commit_message"; then
    success "✅ Installation changes committed successfully."

    # Push to remote if it exists and we're authenticated
    if git config --get remote.origin.url &>/dev/null; then
      if command -v gh &>/dev/null && gh auth status &>/dev/null 2>&1; then
        echo
        read -p "Push installation commit to remote repository? [Y/n]: " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$|^$ ]]; then
          progress "Pushing to remote repository..."
          local current_branch=$(git branch --show-current)
          if git push origin "$current_branch"; then
            success "✅ Changes pushed to remote repository."
          else
            warning "⚠️ Could not push to remote. You can push manually later."
          fi
        else
          info "Skipping push to remote. You can push manually later with: git push"
        fi
      else
        info "GitHub CLI not authenticated. You can push manually later with: git push"
      fi
    else
      info "No remote repository configured. Commit saved locally."
    fi
  else
    warning "⚠️ Could not commit installation changes. Please commit manually if needed."
  fi
}

# Show completion message
show_completion_message() {
  echo
  title "🎉 SpecPilot installation completed!"
  echo
  success "Installation path: $INSTALL_DIR"
  success "Project root directory: $PROJECT_DIR"
  echo

  title "Quick Start:"
  echo "  1. Set the environment variable:"
  echo "     export SPECROOT=\"$PROJECT_DIR\""
  echo "  2. Start using SpecPilot in your AI development tool"
  echo "  3. Begin development workflow:"
  echo "     ./scripts/specpilot-workflow.sh start-task <task-id>"
  echo

  title "Available MCP tools:"
  echo "  1. project-init: Initialize project directory structure and default policies"
  echo "  2. prd-generate: AI-driven PRD specification generation (modular architecture)"
  echo "  3. tsd-generate: AI-driven Technical Spec Document generation (tsd-{number}.md in specs/tsd/)"
  echo "  4. epic-generate: AI-driven Epic file generation (epic-{epic-number}.md in specs/epics/)"
  echo "  5. task-generate: AI-driven development task generation (task-{task-number}.md) with dependency analysis and AI guidance"
  echo "  6. project-status: Calculate progress percentage, health, and signal detection"
  echo "  7. next-action: Intelligent next action suggestion, supports file existence check and parallel development scheduling"
  echo "  8. git-worktree: Git worktree management for parallel Epic/Task branch isolation"
  echo "  9. check-dependencies: Check for dependency cycles and parallel group conflicts"
  echo

  title "🔧 Claude Code Setup:"
  echo "  If using Claude Code with project scope MCP, run:"
  echo "     claude mcp reset-project-choices"
  echo "  This resets MCP permissions for project-specific access."
  echo

  title "Git Worktree Scripts (for AI agents):"
  echo "  • ./scripts/specpilot-workflow.sh: Master workflow script"
  echo "    - start-task <task-id>: Create worktree and start development"
  echo "    - finish-task <task-id>: Commit and create PR"
  echo "    - complete-task <task-id>: Merge PR and cleanup worktree"
  echo "  • Individual scripts in scripts/git-worktree/ and scripts/github/"
  echo

  title "Verify installation:"
  echo "  Run comprehensive installation verification:"
  echo "     ./verify-mcp-server.sh"
  echo

  info "For full documentation, please refer to: https://github.com/sacahan/SpecPilot"
  info "Installation log saved to: $LOG_FILE"
}

# Main program
main() {
  # Initialize log
  echo "SpecPilot installation started - $(date)" >"$LOG_FILE"

  title "🚀 SpecPilot MCP Server Installation v$VERSION"
  echo

  # Environment check
  check_root
  detect_os
  check_required_tools
  check_node_version
  detect_package_manager

  # Git and GitHub check
  check_git_status
  check_github_cli
  check_github_repository

  # Detect AI tools
  detect_ai_tools

  # Safety check - ensure DETECTED_AI_TOOLS exists
  if [[ -z "${DETECTED_AI_TOOLS+x}" ]]; then
    warning "DETECTED_AI_TOOLS was not set, initializing as empty array"
    DETECTED_AI_TOOLS=()
  fi

  # Show installation options
  if [[ -n "${DETECTED_AI_TOOLS+x}" ]] && [[ ${#DETECTED_AI_TOOLS[@]} -gt 0 ]]; then
    show_install_options
  else
    warning "No supported AI tools detected, proceeding with basic installation."
    export INSTALL_CHOICE="5"
  fi

  # Execute installation
  install_specpilot
  setup_environment
  init_project_structure

  # Note: GitHub labels will be created automatically when first issue/milestone is created

  # Configure MCP
  handle_install_choice

  # Test installation
  test_installation

  # Auto-commit installation changes
  auto_commit_installation

  # Show completion message
  show_completion_message
}

# Error handling
trap 'error "An error occurred during installation, please check: $LOG_FILE"; exit 1' ERR

# Execute main program
main "$@"
