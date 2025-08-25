#!/bin/bash
set -e

INSTALL_DIR="$HOME/Quarzism Client"
SCRIPTS_DIR="$INSTALL_DIR/scripts"
VENV_DIR="$INSTALL_DIR/clientvenv"
DESKTOP_FILE="$HOME/.local/share/applications/quarzism-client.desktop"
UNINSTALLER="$INSTALL_DIR/uninstall_quarzism.sh"
UNINSTALLER_GITHUB="https://github.com/Qsenja/Quarzismclient/raw/refs/heads/main/uninstaller.sh"

check_dependencies() {
    local missing_deps=()
    
    if ! command -v python3 &> /dev/null; then
        missing_deps+=("python3")
    fi
    if ! command -v pip3 &> /dev/null; then
        missing_deps+=("python3-pip")
    fi
    if ! command -v wget &> /dev/null && ! command -v curl &> /dev/null; then
        missing_deps+=("wget or curl")
    fi
    
    if [ ${#missing_deps[@]} -ne 0 ]; then
        echo "Missing dependencies: ${missing_deps[*]}"
        exit 1
    fi
}

download_file() {
    local url=$1
    local output=$2
    
    if command -v wget &> /dev/null; then
        wget -q "$url" -O "$output"
    else
        curl -s -L "$url" -o "$output"
    fi
}

create_install_dir() {
    if [ -d "$INSTALL_DIR" ]; then
        rm -rf "$INSTALL_DIR"
    fi
    mkdir -p "$SCRIPTS_DIR"
}

setup_virtualenv() {
    download_file "https://github.com/Qsenja/Quarzismclient/raw/refs/heads/main/requirements.txt" "$INSTALL_DIR/requirements.txt"
    
    python3 -m venv "$VENV_DIR"
    source "$VENV_DIR/bin/activate"
    pip install --upgrade pip
    pip install -r "$INSTALL_DIR/requirements.txt"
    deactivate
    
    rm "$INSTALL_DIR/requirements.txt"
}

download_scripts() {
    download_file "https://github.com/Qsenja/Quarzismclient/raw/refs/heads/main/qlassets.py" "$SCRIPTS_DIR/qlassets.py"
    download_file "https://github.com/Qsenja/Quarzismclient/raw/refs/heads/main/gui.py" "$SCRIPTS_DIR/gui.py"
    download_file "https://github.com/Qsenja/Quarzismclient/raw/refs/heads/main/launcher.py" "$SCRIPTS_DIR/launcher.py"
    download_file "https://github.com/Qsenja/Quarzismclient/raw/refs/heads/main/icon.png" "$SCRIPTS_DIR/icon.png"
    download_file "$UNINSTALLER_GITHUB" "$UNINSTALLER"
    chmod +x "$UNINSTALLER"
}

create_desktop_entry() {
    mkdir -p "$HOME/.local/share/applications"
    
    cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Quarzism Client
Comment=Minecraft client with Quarzism modifications
Exec=sh -c "cd '$SCRIPTS_DIR' && source '$VENV_DIR/bin/activate' && python gui.py"
Icon=$SCRIPTS_DIR/icon.png
Categories=Game;
Terminal=false
StartupWMClass=QuarzismClient
EOF
    
    chmod +x "$DESKTOP_FILE"
    if command -v update-desktop-database &> /dev/null; then
        update-desktop-database "$HOME/.local/share/applications"
    fi
}

main() {
    check_dependencies
    create_install_dir
    setup_virtualenv
    download_scripts
    create_desktop_entry
    echo "Installation completed successfully!"
    echo "You can uninstall anytime by running: $UNINSTALLER"
}

main "$@"
