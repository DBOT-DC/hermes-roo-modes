#!/usr/bin/env bash
# =============================================================================
# hermes-roo-modes installer
# =============================================================================
# Installs the Roo Code mode system plugin for Hermes Agent.
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/DBOT-DC/hermes-roo-modes/main/install.sh | bash
#   OR
#   bash install.sh [--force]
#
# Prerequisites:
#   - Hermes Agent installed (~/.hermes/hermes-agent/)
#   - git, python3
# =============================================================================

set -euo pipefail

PLUGIN_NAME="hermes-roo-modes"
REPO="DBOT-DC/hermes-roo-modes"
HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
PLUGINS_DIR="$HERMES_HOME/plugins"
FORCE=false

for arg in "$@"; do
    case "$arg" in
        --force|-f) FORCE=true ;;
        --help|-h)
            echo "Usage: $0 [--force]"
            echo ""
            echo "Installs the $PLUGIN_NAME plugin for Hermes Agent."
            echo ""
            echo "Options:"
            echo "  --force  Reinstall even if already present"
            echo "  --help   Show this help"
            exit 0
            ;;
    esac
done

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
DIM='\033[2m'
NC='\033[0m'

info()  { echo -e "${GREEN}✓${NC} $1"; }
warn()  { echo -e "${YELLOW}!${NC} $1"; }
error() { echo -e "${RED}✗${NC} $1"; exit 1; }

# --- Preflight checks ---
if ! command -v git &>/dev/null; then
    error "git is required but not found in PATH"
fi

if ! command -v python3 &>/dev/null; then
    error "python3 is required but not found in PATH"
fi

if [ ! -d "$HERMES_HOME/hermes-agent" ]; then
    error "Hermes Agent not found at $HERMES_HOME/hermes-agent"
fi

# --- Install ---
TARGET="$PLUGINS_DIR/$PLUGIN_NAME"

if [ -d "$TARGET" ] && [ "$FORCE" = false ]; then
    warn "Plugin already installed at $TARGET"
    echo -e "  Use ${DIM}--force${NC} to reinstall"
    echo ""
    echo "To update:  cd $TARGET && git pull"
    echo "To enable: hermes plugins enable $PLUGIN_NAME"
    exit 0
fi

echo ""
echo -e "${DIM}Installing $PLUGIN_NAME...${NC}"
echo ""

# Remove existing if --force
if [ -d "$TARGET" ]; then
    echo -e "${DIM}  Removing existing installation...${NC}"
    rm -rf "$TARGET"
fi

mkdir -p "$PLUGINS_DIR"

# Clone
echo -e "${DIM}  Cloning $REPO...${NC}"
if ! git clone --depth 1 "https://github.com/$REPO.git" "$TARGET" 2>/dev/null; then
    error "Failed to clone $REPO"
fi

# Validate
if [ ! -f "$TARGET/plugin.yaml" ]; then
    error "Invalid plugin: plugin.yaml not found"
fi

if [ ! -f "$TARGET/__init__.py" ]; then
    error "Invalid plugin: __init__.py not found"
fi

# Verify Python imports work
echo -e "${DIM}  Verifying plugin modules...${NC}"
if ! (cd "$TARGET" && python3 -c "import sys; sys.path.insert(0, '.'); from hermes_roo_modes.modes import list_modes; modes = list_modes(); assert len(modes) >= 5, f'Expected 5+ modes, got {len(modes)}'" 2>/dev/null); then
    warn "Plugin module verification failed — may need dependencies"
fi

info "Plugin installed to $TARGET"

# --- Enable ---
echo ""
echo -e "${DIM}To enable, add to ${HERMES_HOME}/config.yaml:${NC}"
echo ""
echo "  plugins:"
echo "    enabled:"
echo "      - $PLUGIN_NAME"
echo ""
echo -e "${DIM}Or use the CLI:${NC}"
echo "  hermes plugins enable $PLUGIN_NAME"
echo ""
echo -e "${DIM}Then restart:${NC}"
echo "  hermes gateway restart"
echo ""
info "Done!"
