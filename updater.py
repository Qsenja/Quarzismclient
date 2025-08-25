import os
import sys
import requests
import shutil
import ast
from pathlib import Path

def download_file(url, destination):
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        with open(destination, 'wb') as f:
            f.write(response.content)
        return True
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return False

def get_file_list():
    try:
        response = requests.get("https://github.com/Qsenja/Quarzismclient/raw/refs/heads/main/source.txt", timeout=10)
        response.raise_for_status()
        
        # Parse the file content as a list of tuples
        file_list = []
        for line in response.text.strip().split('\n'):
            if line.strip() and not line.strip().startswith('#'):
                try:
                    # Use ast to safely evaluate the tuple
                    file_tuple = ast.literal_eval(line.strip().rstrip(','))
                    file_list.append(file_tuple)
                except:
                    # Fallback for simple parsing if ast fails
                    if '(' in line and ')' in line:
                        parts = line.strip().rstrip(',').strip('()').split(',')
                        if len(parts) >= 2:
                            filename = parts[0].strip().strip('"\'')
                            url = parts[1].strip().strip('"\'')
                            file_list.append((filename, url))
        return file_list
    except Exception as e:
        print(f"Error getting file list: {e}")
        # Return default list if we can't fetch the source file
        return [
            ("qlassets.py", "https://github.com/Qsenja/Quarzismclient/raw/refs/heads/main/qlassets.py"),
            ("gui.py", "https://github.com/Qsenja/Quarzismclient/raw/refs/heads/main/gui.py"),
            ("launcher.py", "https://github.com/Qsenja/Quarzismclient/raw/refs/heads/main/launcher.py"),
            ("icon.png", "https://github.com/Qsenja/Quarzismclient/raw/refs/heads/main/icon.png"),
            ("version.txt", "https://github.com/Qsenja/Quarzismclient/raw/refs/heads/main/version.txt")
        ]

def main():
    # Get paths
    base_dir = Path(__file__).parent
    scripts_dir = base_dir / "scripts"
    
    # Get current version
    try:
        with open(base_dir / "version.txt", "r") as f:
            current_version = f.read().strip()
    except:
        current_version = "1.0"
    
    # Get latest version from GitHub
    try:
        response = requests.get("https://github.com/Qsenja/Quarzismclient/raw/refs/heads/main/version.txt", timeout=10)
        latest_version = response.text.strip()
    except:
        latest_version = current_version
    
    # If versions match, launch GUI
    if current_version == latest_version:
        os.chdir(scripts_dir)
        os.system(f"{sys.executable} gui.py")
        return
    
    # Otherwise, update files
    print(f"Updating from {current_version} to {latest_version}...")
    
    # Get the list of files to update
    files_to_update = get_file_list()
    
    # Create a backup directory
    backup_dir = base_dir / "backup"
    backup_dir.mkdir(exist_ok=True)
    
    # Backup current files
    for filename, url in files_to_update:
        file_path = scripts_dir / filename
        if file_path.exists():
            backup_path = backup_dir / filename
            shutil.copy2(file_path, backup_path)
    
    # Download new files
    for filename, url in files_to_update:
        destination = scripts_dir / filename
        if download_file(url, destination):
            print(f"Downloaded {filename}")
        else:
            # Restore from backup if download failed
            backup_path = backup_dir / filename
            if backup_path.exists():
                shutil.copy2(backup_path, destination)
                print(f"Restored {filename} from backup")
    
    # Update version file
    try:
        with open(scripts_dir / "version.txt", "w") as f:
            f.write(latest_version)
    except:
        pass
    
    # Clean up backup
    try:
        shutil.rmtree(backup_dir)
    except:
        pass
    
    # Launch GUI with new version
    os.chdir(scripts_dir)
    os.system(f"{sys.executable} gui.py")

if __name__ == "__main__":
    main()