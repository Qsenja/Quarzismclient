# Check for updates first
import os
import sys
from pathlib import Path

base_dir = Path(__file__).parent
updater_path = base_dir / "updater.py"

if updater_path.exists():
    os.system(f"{sys.executable} {updater_path}")
    sys.exit(0)

import json, os, sys, threading, time
from pathlib import Path
import requests
import minecraft_launcher_lib
from PySide6.QtCore import Qt, QRegularExpression, QTimer
from PySide6.QtGui import QFont, QRegularExpressionValidator, QPalette, QColor, QIcon
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QFormLayout, QLineEdit,
    QPushButton, QGroupBox, QLabel, QMessageBox, QComboBox, QProgressBar
)

sys.path.insert(0, str(Path(__file__).parent))
from launcher import MinecraftLauncher
from qlassets import QuarzismAssets

CONFIG_FILE = Path(__file__).with_name("settings.json")

def load_settings():
    try:
        with open(CONFIG_FILE, "r") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        data = {}
    return {"username": data.get("username", "Player"), "ram": int(data.get("ram", 4096))}

def save_settings(username, ram):
    CONFIG_FILE.write_text(json.dumps({"username": username, "ram": ram}, indent=2))

class QuarzismClientGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Quarzism Client")
        self.setWindowIcon(QIcon(str(Path(__file__).parent / "icon.png")))
        self.resize(800, 600)
        self.settings = load_settings()
        self.launcher = MinecraftLauncher(Path(__file__).parent / ".." / "game" / ".minecraft")
        self.assets = QuarzismAssets(self.launcher.minecraft_dir)
        self.process = None
        self.available_versions = []
        self._build_ui()
        self._load_versions()
        threading.Thread(target=self._import_settings, daemon=True).start()

    def _build_ui(self):
        vbox = QVBoxLayout(self)
        vbox.setContentsMargins(30, 20, 30, 20)
        vbox.setSpacing(20)

        header = QLabel("Quarzism Client")
        header.setFont(QFont("Segoe UI", 26, QFont.Bold))
        header.setAlignment(Qt.AlignCenter)
        vbox.addWidget(header)

        group = QGroupBox("Game Settings")
        group.setFont(QFont("Segoe UI", 12))
        form = QFormLayout(group)
        form.setLabelAlignment(Qt.AlignRight)
        form.setSpacing(12)

        self.version_combo = QComboBox()
        self.version_combo.setFont(QFont("Segoe UI", 11))
        self.version_combo.setMaxVisibleItems(5)
        self.version_combo.view().setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        form.addRow("Version:", self.version_combo)

        self.username_edit = QLineEdit(self.settings["username"])
        self.username_edit.setFont(QFont("Segoe UI", 11))
        form.addRow("Username:", self.username_edit)

        self.ram_edit = QLineEdit(str(self.settings["ram"]))
        self.ram_edit.setFont(QFont("Segoe UI", 11))
        self.ram_edit.setValidator(QRegularExpressionValidator(QRegularExpression(r"\d+")))
        form.addRow("RAM (MB):", self.ram_edit)
        vbox.addWidget(group)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        vbox.addWidget(self.progress_bar)

        self.btn = QPushButton("LAUNCH")
        self.btn.setFixedHeight(70)
        self.btn.setFont(QFont("Segoe UI", 24, QFont.Bold))
        self.btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                              stop:0 #34b1eb, stop:1 #2a91d0);
                color: white;
                border-radius: 14px;
            }
            QPushButton:hover:!pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                              stop:0 #5dcbff, stop:1 #34b1eb);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                              stop:0 #1a6fb5, stop:1 #1771c8);
            }
            QPushButton:disabled {
                background: #1e1e2e;
                color: #6c7086;
            }
        """)
        vbox.addWidget(self.btn)
        self.btn.clicked.connect(self._launch_button)

    def _load_versions(self):
        try:
            self.available_versions = self.launcher.get_available_versions()
            self.version_combo.clear()
            for version in self.available_versions:
                self.version_combo.addItem(version)
            try:
                latest = minecraft_launcher_lib.utils.get_latest_version()["release"]
                index = self.version_combo.findText(latest)
                if index >= 0:
                    self.version_combo.setCurrentIndex(index)
            except:
                pass
        except Exception as e:
            print(f"Error loading versions: {e}")

    def _import_settings(self):
        try:
            OPTIONS_URL = "https://github.com/Qsenja/Quarzismclient/raw/refs/heads/main/options.txt"
            response = requests.get(OPTIONS_URL, timeout=10)
            response.raise_for_status()
            options_path = Path(self.launcher.minecraft_dir) / "options.txt"
            with open(options_path, 'wb') as f:
                f.write(response.content)
            print("Minecraft settings imported successfully")
        except Exception as e:
            print(f"Failed to import Minecraft settings: {e}")

    def _import_assets(self):
        time.sleep(10)
        success = self.assets.import_all_assets()
        if success:
            print("Quarzism assets imported successfully")
        else:
            print("Failed to import some Quarzism assets")

    def _launch_button(self):
        if self.btn.text() == "KILL":
            self._kill()
            return

        version = self.version_combo.currentText()
        username = self.username_edit.text().strip() or "Player"
        ram = max(512, int(self.ram_edit.text()))
        save_settings(username, ram)

        if not self.launcher.is_version_installed(version):
            self.btn.setText("Downloading…")
            self.btn.setEnabled(False)
            self.progress_bar.setVisible(True)
            
            def install_callback(status):
                if "Progress" in status:
                    try:
                        progress = int(status.split(" ")[-1].replace("%", ""))
                        self.progress_bar.setValue(progress)
                    except:
                        pass
            
            ok = self.launcher.install_version(version, callback=install_callback)
            self.progress_bar.setVisible(False)
            
            if not ok:
                QMessageBox.critical(self, "Install failed", "Could not install the selected version.")
                self._reset()
                return

        self.btn.setText("Starting…")
        self.btn.setEnabled(False)
        cmd = self.launcher.get_launch_command(version, username, ram, [])
        import subprocess
        self.process = subprocess.Popen(cmd)
        threading.Thread(target=self._import_assets, daemon=True).start()
        threading.Thread(target=self._monitor, daemon=True).start()

    def _monitor(self):
        if not self.process:
            return
        time.sleep(3)
        self.btn.setText("KILL")
        self.btn.setEnabled(True)
        while True:
            if self.process.poll() is not None:
                QTimer.singleShot(0, self._reset)
                break
            time.sleep(0.25)

    def _kill(self):
        if self.process and self.process.poll() is None:
            self.process.terminate()
            self.process.wait()
        self._reset()

    def _reset(self):
        self.btn.setText("LAUNCH")
        self.btn.setEnabled(True)
        self.process = None

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    palette = app.palette()
    palette.setColor(QPalette.Window, QColor("#0d0d0d"))
    palette.setColor(QPalette.WindowText, Qt.white)
    palette.setColor(QPalette.Base, QColor("#111111"))
    palette.setColor(QPalette.Button, QColor("#1e1e2e"))
    palette.setColor(QPalette.ButtonText, Qt.white)
    palette.setColor(QPalette.Highlight, QColor("#34b1eb"))
    palette.setColor(QPalette.HighlightedText, Qt.black)
    app.setPalette(palette)

    gui = QuarzismClientGUI()
    gui.show()
    sys.exit(app.exec())
