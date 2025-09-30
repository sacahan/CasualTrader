#!/bin/bash
# Common logging utilities for SpecPilot shell scripts
# Follows the same pattern as src/tools/common.ts logging

# Project root directory
SPECROOT="${SPECROOT:-$(pwd)}"

# Debug logging control
DEBUG_MODE="${SPECPILOT_DEBUG:-false}"
DEBUG_FILE="${SPECPILOT_DEBUG_FILE:-$SPECROOT/.specpilot-debug.log}"

# Log level emoji mapping function (compatible with older bash versions)
get_log_emoji() {
  case "$1" in
    "INFO") echo "ℹ️" ;;
    "WARN") echo "⚠️" ;;
    "ERROR") echo "❌" ;;
    "SCRIPT_START") echo "🚀" ;;
    "SCRIPT_END") echo "✅" ;;
    *) echo "📝" ;;
  esac
}

# Internal logging function
write_log() {
  local level="$1"
  local message="$2"
  local data="$3"

  if [[ "$DEBUG_MODE" != "true" ]]; then
    return 0
  fi

  # Use fallback for systems that don't support milliseconds
  local timestamp
  if timestamp=$(date -u +"%Y-%m-%dT%H:%M:%S.%3NZ" 2>/dev/null); then
    : # timestamp set successfully
  else
    timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
  fi

  local emoji=$(get_log_emoji "$level")

  local log_message="[$timestamp] $emoji $level: $message"
  if [[ -n "$data" ]]; then
    log_message="$log_message\n$data"
  fi
  log_message="$log_message\n"

  # Append to debug file, silently ignore errors
  echo -e "$log_message" >>"$DEBUG_FILE" 2>/dev/null || true
}

# Unified debug interface
log_info() {
  local message="$1"
  local data="$2"
  write_log "INFO" "$message" "$data"
}

log_warn() {
  local message="$1"
  local data="$2"
  write_log "WARN" "$message" "$data"
}

log_error() {
  local message="$1"
  local data="$2"
  write_log "ERROR" "$message" "$data"
}

log_script_start() {
  local script_name="$1"
  local args="$2"
  write_log "SCRIPT_START" "$script_name" "args: $args"
}

log_script_end() {
  local script_name="$1"
  local success="${2:-true}"
  local status_emoji

  if [[ "$success" == "true" ]]; then
    status_emoji="✅"
  else
    status_emoji="❌"
  fi

  write_log "SCRIPT_END" "$status_emoji $script_name $(if [[ "$success" == "true" ]]; then echo "SUCCESS"; else echo "FAILED"; fi)"
}

# Function to log command execution
log_command() {
  local command="$1"
  local description="$2"
  log_info "Executing: $command" "$description"
}

# Function to log operation start/end
log_operation() {
  local operation="$1"
  local details="$2"
  log_info "Operation: $operation" "$details"
}
