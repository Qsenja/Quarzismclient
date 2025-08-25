download_scripts() {
    download_file "https://github.com/Qsenja/Quarzismclient/raw/refs/heads/main/qlassets.py" "$SCRIPTS_DIR/qlassets.py"
    download_file "https://github.com/Qsenja/Quarzismclient/raw/refs/heads/main/gui.py" "$SCRIPTS_DIR/gui.py"
    download_file "https://github.com/Qsenja/Quarzismclient/raw/refs/heads/main/launcher.py" "$SCRIPTS_DIR/launcher.py"
    download_file "https://github.com/Qsenja/Quarzismclient/raw/refs/heads/main/icon.png" "$SCRIPTS_DIR/icon.png"
    download_file "https://github.com/Qsenja/Quarzismclient/raw/refs/heads/main/updater.py" "$SCRIPTS_DIR/updater.py"
    download_file "https://github.com/Qsenja/Quarzismclient/raw/refs/heads/main/version.txt" "$SCRIPTS_DIR/version.txt"
    download_file "$UNINSTALLER_GITHUB" "$UNINSTALLER"
    chmod +x "$UNINSTALLER"
}
