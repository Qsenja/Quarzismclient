import subprocess
import os
import sys
import minecraft_launcher_lib
import logging
import json
import requests
from typing import List, Dict, Any, Callable, Optional
from pathlib import Path

# Set up logging
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "logs")
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, "launcher.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

class MinecraftLauncher:
    def __init__(self, minecraft_dir: str = None):
        """
        Initialize the Minecraft launcher
        
        :param minecraft_dir: Path to Minecraft directory 
        (default: game/.minecraft in the same directory as this script)
        """
        if minecraft_dir is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            minecraft_dir = os.path.join(base_dir, "..", "game", ".minecraft")
        
        self.minecraft_dir = os.path.abspath(minecraft_dir)
        os.makedirs(self.minecraft_dir, exist_ok=True)
        self.logger = logging.getLogger(__name__)
        
    def get_available_versions(self) -> List[str]:
        """Get list of all available Minecraft versions"""
        try:
            version_list = minecraft_launcher_lib.utils.get_version_list()
            return [v["id"] for v in version_list]
        except Exception as e:
            self.logger.error(f"Error fetching versions: {e}")
            # Return some common versions as fallback
            return ["1.20.1", "1.19.4", "1.18.2", "1.17.1", "1.16.5"]
    
    def is_version_installed(self, version: str) -> bool:
        """Check if a specific version is already installed"""
        version_path = os.path.join(self.minecraft_dir, "versions", version)
        return os.path.exists(version_path)
    
    def install_version(self, version: str, callback: Optional[Callable] = None) -> bool:
        """
        Install a specific Minecraft version with all its dependencies
        
        :param version: Minecraft version to install
        :param callback: Function to call with status updates
        :return: True if successful, False otherwise
        """
        try:
            if callback:
                callback(f"Installing Minecraft {version}...")
            
            # Create proper callback dictionary for minecraft_launcher_lib
            callback_dict = None
            if callback:
                callback_dict = {
                    "setStatus": lambda status: callback(status),
                    "setProgress": lambda progress: None,
                    "setMax": lambda max: None
                }
            
            # Download the version
            minecraft_launcher_lib.install.install_minecraft_version(
                versionid=version,
                minecraft_directory=self.minecraft_dir,
                callback=callback_dict
            )
            
            if callback:
                callback(f"Successfully installed Minecraft {version}")
            self.logger.info(f"Installed Minecraft version {version}")
            return True
        except Exception as e:
            error_msg = f"Error installing Minecraft {version}: {str(e)}"
            if callback:
                callback(error_msg)
            self.logger.error(error_msg)
            return False
    
    def get_launch_command(self, version: str, username: str, ram_mb: int = 4096, 
                          custom_args: List[str] = None) -> List[str]:
        """
        Generate the launch command for Minecraft
        
        :param version: Minecraft version to launch
        :param username: Player username
        :param ram_mb: Amount of RAM in MB to allocate
        :param custom_args: Additional custom JVM arguments
        :return: List of command arguments
        """
        # Default JVM arguments
        jvm_args = [
            f"-Xms{ram_mb//2}M",
            f"-Xmx{ram_mb}M",
            "-XX:+UnlockExperimentalVMOptions",
            "-XX:+UseG1GC",
            "-XX:G1NewSizePercent=20",
            "-XX:G1ReservePercent=20",
            "-XX:MaxGCPauseMillis=50",
            "-XX:G1HeapRegionSize=32M"
        ]
        
        # Add custom arguments if provided
        if custom_args:
            jvm_args.extend(custom_args)
            
        # Get the Minecraft launch command for offline mode
        options = {
            "username": username,
            "uuid": "",
            "token": ""
        }
        
        command = minecraft_launcher_lib.command.get_minecraft_command(
            version=version,
            minecraft_directory=self.minecraft_dir,
            options=options
        )
        
        # Insert JVM arguments at the beginning
        command = [command[0]] + jvm_args + command[1:]
        
        return command
    
    def launch_game(self, version: str, username: str = "Player", 
                   ram_mb: int = 4096, custom_args: List[str] = None, 
                   callback: Optional[Callable] = None) -> int:
        """
        Launch Minecraft with the specified parameters
        
        :param version: Minecraft version to launch
        :param username: Player username
        :param ram_mb: Amount of RAM in MB to allocate
        :param custom_args: Additional custom JVM arguments
        :param callback: Function to call with status updates
        :return: Exit code of the Minecraft process
        """
        # Settings import is now handled by qlassets.py
        
        # Check if version is installed
        if not self.is_version_installed(version):
            if callback:
                callback(f"Version {version} is not installed. Installing now...")
            if not self.install_version(version, callback):
                return 1
        
        # Generate launch command
        command = self.get_launch_command(version, username, ram_mb, custom_args)
        
        if callback:
            callback(f"Launching Minecraft {version} with {ram_mb}MB RAM...")
        
        # Launch the game
        try:
            self.logger.info(f"Launching Minecraft with command: {' '.join(command)}")
            process = subprocess.Popen(command)
            process.wait()
            exit_code = process.returncode
            self.logger.info(f"Minecraft exited with code {exit_code}")
            return exit_code
        except Exception as e:
            error_msg = f"Error launching Minecraft: {str(e)}"
            if callback:
                callback(error_msg)
            self.logger.error(error_msg)
            return 1

# For command-line usage
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Quarzism Client - Minecraft Launcher")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Install command
    install_parser = subparsers.add_parser("install", help="Install a Minecraft version")
    install_parser.add_argument("version", help="Minecraft version to install")
    install_parser.add_argument("--dir", help="Minecraft directory", default=None)
    
    # List command
    list_parser = subparsers.add_parser("list", help="List available Minecraft versions")
    list_parser.add_argument("--dir", help="Minecraft directory", default=None)
    
    # Launch command
    launch_parser = subparsers.add_parser("launch", help="Launch Minecraft")
    launch_parser.add_argument("version", help="Minecraft version to launch")
    launch_parser.add_argument("--username", "-u", help="Player username", default="Player")
    launch_parser.add_argument("--ram", "-r", help="RAM in MB", type=int, default=4096)
    launch_parser.add_argument("--dir", help="Minecraft directory", default=None)
    launch_parser.add_argument("--jvm-args", help="Additional JVM arguments", nargs="+")
    
    args = parser.parse_args()
    
    # Initialize the launcher
    launcher = MinecraftLauncher(args.dir)
    
    def print_status(status):
        print(status)
    
    if args.command == "install":
        success = launcher.install_version(args.version, print_status)
        sys.exit(0 if success else 1)
        
    elif args.command == "list":
        versions = launcher.get_available_versions()
        print("Available Minecraft versions:")
        for version in versions:
            installed = "(installed)" if launcher.is_version_installed(version) else ""
            print(f"  {version} {installed}")
            
    elif args.command == "launch":
        exit_code = launcher.launch_game(
            version=args.version,
            username=args.username,
            ram_mb=args.ram,
            custom_args=args.jvm_args,
            callback=print_status
        )
        sys.exit(exit_code)
        
    else:
        parser.print_help()
        sys.exit(1)