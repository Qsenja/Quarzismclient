#!/bin/bash
set -e

INSTALL_DIR="$(pwd)/Quarzism Client"
DESKTOP_FILE="$HOME/.local/share/applications/quarzism-client.desktop"

if [ "$EUID" -eq 0 ]; then
    echo "Please do not run this uninstaller as root."
    exit 1
fi

read -p "Are you sure you want to uninstall Quarzism Client? (y/N): " confirm
if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
    echo "Uninstallation cancelled."
    exit 0
fi

if [ -d "$INSTALL_DIR" ]; then
    rm -rf "$INSTALL_DIR"
    echo "Removed installation directory: $INSTALL_DIR"
fi

if [ -f "$DESKTOP_FILE" ]; then
    rm "$DESKTOP_FILE"
    echo "Removed desktop entry: $DESKTOP_FILE"
    
    if command -v update-desktop-database &> /dev/null; then
        update-desktop-database "$HOME/.local/share/applications"
    fi
fi

echo "Uninstallation completed successfully."
