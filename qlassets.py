import os
import json
import requests
from pathlib import Path
import sys
import zipfile
import struct

class QuarzismAssets:
    def __init__(self, minecraft_dir=None):
        """
        Initialize the assets importer
        
        :param minecraft_dir: Path to Minecraft directory 
        (default: game/.minecraft in the same directory as this script)
        """
        if minecraft_dir is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            minecraft_dir = os.path.join(base_dir, "..", "game", ".minecraft")
        
        self.minecraft_dir = os.path.abspath(minecraft_dir)
        os.makedirs(self.minecraft_dir, exist_ok=True)
        
        # Define servers to import
        self.servers = [
            {"name": "ExtremeCraft", "ip": "sl.extremecraft.net"},
            {"name": "Twenture", "ip": "sl.twenture.net"},
            {"name": "Twerion", "ip": "hey.twerion.net"},
            {"name": "SpiderSMP", "ip": "spidersmp.ddns.net"}
        ]
        
        # Define texture packs to download
        self.texture_packs = [
            {"name": "fixes.zip", "url": "https://github.com/Qsenja/Quarzismclient/raw/refs/heads/main/fixes.zip"},
            {"name": "fullbright.zip", "url": "https://github.com/Qsenja/Quarzismclient/raw/refs/heads/main/fullbright.zip"},
            {"name": "redstone.zip", "url": "https://github.com/Qsenja/Quarzismclient/raw/refs/heads/main/redstone.zip"},
            {"name": "variation.zip", "url": "https://github.com/Qsenja/Quarzismclient/raw/refs/heads/main/variation.zip"}
        ]
        
        # Settings URL
        self.settings_url = "https://github.com/Qsenja/Quarzismclient/raw/refs/heads/main/options.txt"
    
    def download_minecraft_settings(self):
        """Download and install Minecraft settings from GitHub"""
        try:
            print("Downloading Minecraft settings...")
            response = requests.get(self.settings_url, timeout=30)
            response.raise_for_status()
            
            settings_path = os.path.join(self.minecraft_dir, "options.txt")
            
            # Write new settings
            with open(settings_path, 'wb') as f:
                f.write(response.content)
            
            print("Successfully downloaded Minecraft settings")
            return True
            
        except Exception as e:
            print(f"Error downloading Minecraft settings: {e}")
            return False
    
    def import_servers(self):
        """Import servers to the server list using proper NBT format"""
        servers_file = os.path.join(self.minecraft_dir, "servers.dat")
        
        try:
            # Try to use minecraft_launcher_lib for server import if available
            try:
                import minecraft_launcher_lib
                
                # Format servers for the library
                server_list = []
                for server in self.servers:
                    server_list.append({
                        "name": server["name"],
                        "ip": server["ip"],
                        "icon": None,
                        "acceptTextures": 0
                    })
                
                # Use the library to set servers
                minecraft_launcher_lib.server.set_servers(servers_file, server_list)
                print(f"Successfully imported {len(self.servers)} servers using minecraft_launcher_lib")
                return True
                
            except ImportError:
                print("minecraft_launcher_lib not available, using manual server import")
                # Fall through to manual method
            
            # Manual server.dat creation
            with open(servers_file, 'wb') as f:
                # NBT header for compound tag
                f.write(b'\x0a\x00\x00')  # Compound tag with empty name
                
                # Servers list tag
                f.write(b'\x09\x00\x08servers\x00\x00\x00')  # List tag for servers
                f.write(struct.pack('>I', len(self.servers)))  # Number of servers
                
                # Add each server
                for server in self.servers:
                    # Server compound tag
                    f.write(b'\x0a\x00\x00')  # Compound tag
                    
                    # Server name
                    f.write(b'\x08\x00\x04name\x00')  # String tag for name
                    name = server["name"].encode('utf-8')
                    f.write(struct.pack('>H', len(name)))
                    f.write(name)
                    
                    # Server IP
                    f.write(b'\x08\x00\x02ip\x00')  # String tag for IP
                    ip = server["ip"].encode('utf-8')
                    f.write(struct.pack('>H', len(ip)))
                    f.write(ip)
                    
                    # Server icon (empty)
                    f.write(b'\x08\x00\x04icon\x00\x00\x00')  # Empty string tag for icon
                    
                    # Accept textures (0 = prompt)
                    f.write(b'\x01\x00\x0eacceptTextures\x00')  # Byte tag for acceptTextures
                    
                    # Hidden (0 = not hidden)
                    f.write(b'\x01\x00\x06hidden\x00')  # Byte tag for hidden
                    
                    # End of server compound
                    f.write(b'\x00')
                
                # End of root compound
                f.write(b'\x00')
            
            print(f"Successfully imported {len(self.servers)} servers")
            return True
            
        except Exception as e:
            print(f"Error importing servers: {e}")
            return False
    
    def extract_texture_pack(self, zip_path, extract_to):
        """Extract a texture pack zip file to a folder, handling nested folders"""
        try:
            # Create the extraction directory
            os.makedirs(extract_to, exist_ok=True)
            
            # Extract the zip file
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # Get the list of files in the zip
                file_list = zip_ref.namelist()
                
                # Check if all files are in a single root folder
                root_dirs = set()
                for file in file_list:
                    parts = file.split('/')
                    if len(parts) > 1 and parts[0]:  # Has at least one directory level
                        root_dirs.add(parts[0])
                
                # If there's only one root directory, extract its contents directly
                if len(root_dirs) == 1:
                    root_dir = list(root_dirs)[0]
                    for file in file_list:
                        if file.startswith(root_dir + '/') and not file.endswith('/'):
                            # Extract file without the root directory
                            dest_path = os.path.join(extract_to, os.path.relpath(file, root_dir))
                            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                            with open(dest_path, 'wb') as dest_file:
                                dest_file.write(zip_ref.read(file))
                    print(f"Extracted {os.path.basename(zip_path)} without root folder")
                else:
                    # Extract normally
                    zip_ref.extractall(extract_to)
                    print(f"Extracted {os.path.basename(zip_path)} normally")
            
            return True
        except Exception as e:
            print(f"Error extracting {os.path.basename(zip_path)}: {e}")
            return False
    
    def download_texture_packs(self):
        """Download, install, and extract texture packs"""
        resourcepacks_dir = os.path.join(self.minecraft_dir, "resourcepacks")
        os.makedirs(resourcepacks_dir, exist_ok=True)
        
        success_count = 0
        for pack in self.texture_packs:
            try:
                print(f"Downloading {pack['name']}...")
                response = requests.get(pack["url"], timeout=30)
                response.raise_for_status()
                
                # Save the texture pack
                pack_path = os.path.join(resourcepacks_dir, pack["name"])
                with open(pack_path, "wb") as f:
                    f.write(response.content)
                
                print(f"Successfully downloaded {pack['name']}")
                
                # Extract the texture pack
                pack_name_without_ext = os.path.splitext(pack["name"])[0]
                extract_path = os.path.join(resourcepacks_dir, pack_name_without_ext)
                
                if self.extract_texture_pack(pack_path, extract_path):
                    # Remove the zip file after extraction
                    os.remove(pack_path)
                    print(f"Removed zip file: {pack['name']}")
                    success_count += 1
                
            except Exception as e:
                print(f"Error downloading {pack['name']}: {e}")
        
        print(f"Successfully processed {success_count}/{len(self.texture_packs)} texture packs")
        return success_count > 0
    
    def import_all_assets(self):
        """Import all assets (settings, servers, and texture packs)"""
        print("Importing Quarzism Client assets...")
        
        # Download Minecraft settings
        settings_success = self.download_minecraft_settings()
        
        # Import servers
        servers_success = self.import_servers()
        
        # Download and extract texture packs
        textures_success = self.download_texture_packs()
        
        print("Asset import completed!")
        return settings_success or servers_success or textures_success

# For command-line usage
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Quarzism Client Assets Importer")
    parser.add_argument("--dir", help="Minecraft directory", default=None)
    
    args = parser.parse_args()
    
    # Initialize the assets importer
    assets = QuarzismAssets(args.dir)
    
    # Import all assets
    success = assets.import_all_assets()
    sys.exit(0 if success else 1)