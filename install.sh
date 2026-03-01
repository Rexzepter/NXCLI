#!/bin/bash

# NXCLI Installer for Mac/Linux
# This script sets up the nxcli alias and installs dependencies.

set -e

echo "🚀 Installing NXCLI..."

# Check for Python 3
if ! command -v python3 &> /dev/null
then
    echo "❌ Error: Python 3 is not installed."
    exit 1
fi

# Install Python dependencies
echo "📦 Installing Python dependencies (rich)..."
python3 -m pip install -r requirements.txt

# Set up the alias
SHELL_CONFIG=""
if [[ "$SHELL" == *"zsh"* ]]; then
    SHELL_CONFIG="$HOME/.zshrc"
elif [[ "$SHELL" == *"bash"* ]]; then
    SHELL_CONFIG="$HOME/.bashrc"
fi

if [ -n "$SHELL_CONFIG" ]; then
    echo "🔗 Adding 'nxcli' alias to $SHELL_CONFIG..."
    SCRIPT_PATH="$(pwd)/nxcli.py"
    # Remove existing alias if it exists
    sed -i '' '/alias nxcli=/d' "$SHELL_CONFIG" || true
    # Add new alias
    echo "alias nxcli='python3 "$SCRIPT_PATH"'" >> "$SHELL_CONFIG"
    echo "✅ Alias added! Please run 'source $SHELL_CONFIG' to start using nxcli."
else
    echo "⚠️  Could not detect shell config (zsh/bash). Please add the following alias manually:"
    echo "alias nxcli='python3 "$(pwd)/nxcli.py"'"
fi

echo "✨ NXCLI is ready! Type 'nxcli' to begin."
