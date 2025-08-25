import os
import json
import requests
from pathlib import Path
import sys
import zipfile
import struct

class QuarzismAssets:
    def __init__(self, minecraft_dir=None):
        if minecraft_dir is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            minecraft_dir = os.path.join(base_dir, "..", "game", ".minecraft")
        
        self.minecraft_dir = os.path.abspath(minecraft_dir)
        os.makedirs(self.minecraft_dir, exist_ok=True)
        
        self.servers = [
            {"name": "ExtremeCraft", "ip": "sl.extremecraft.net"},
            {"name": "Twenture", "ip": "sl.twenture.net"},
            {"name": "Twerion", "ip": "hey.twerion.net"},
            {"name": "SpiderSMP", "ip": "spidersmp.ddns.net"}
        ]
        
        self.texture_packs = [
            {"name": "fixes.zip", "url": "https://github.com/Qsenja/Quarzismclient/raw/refs/heads/main/fixes.zip"},
            {"name": "fullbright.zip", "url": "https://github.com/Qsenja/Quarzismclient/raw/refs/heads/main/fullbright.zip"},
            {"name": "redstone.zip", "url": "https://github.com/Qsenja/Quarzismclient/raw/refs/heads/main/redstone.zip"},
            {"name": "variation.zip", "url": "https://github.com/Qsenja/Quarzismclient/raw/refs/heads/main/variation.zip"}
        ]
        
        self.settings_url = "https://github.com/Qsenja/Quarzismclient/raw/refs/heads/main/options.txt"
    
    def download_minecraft_settings(self):
        try:
            response = requests.get(self.settings_url, timeout=30)
            response.raise_for_status()
            settings_path = os.path.join(self.minecraft_dir, "options.txt")
            with open(settings_path, 'wb') as f:
                f.write(response.content)
            return True
        except Exception as e:
            print(f"Error downloading Minecraft settings: {e}")
            return False
    
    def import_servers(self):
        servers_file = os.path.join(self.minecraft_dir, "servers.dat")
        try:
            try:
                import minecraft_launcher_lib
                server_list = []
                for server in self.servers:
                    server_list.append({
                        "name": server["name"],
                        "ip": server["ip"],
                        "icon": None,
                        "acceptTextures": 0
                    })
                minecraft_launcher_lib.server.set_servers(servers_file, server_list)
                print(f"Successfully imported {len(self.servers)} servers using minecraft_launcher_lib")
                return True
            except ImportError:
                print("minecraft_launcher_lib not available, using manual server import")
            
            with open(servers_file, 'wb') as f:
                f.write(b'\x0a\x00\x00')
                f.write(b'\x09\x00\x08servers\x00\x00\x00')
                f.write(struct.pack('>I', len(self.servers)))
                for server in self.servers:
                    f.write(b'\x0a\x00\x00')
                    f.write(b'\x08\x00\x04name\x00')
                    name = server["name"].encode('utf-8')
                    f.write(struct.pack('>H', len(name)))
                    f.write(name)
                    f.write(b'\x08\x00\x02ip\x00')
                    ip = server["ip"].encode('utf-8')
                    f.write(struct.pack('>H', len(ip)))
                    f.write(ip)
                    f.write(b'\x08\x00\x04icon\x00\x00\x00')
                    f.write(b'\x01\x00\x0eacceptTextures\x00')
                    f.write(b'\x01\x00\x06hidden\x00')
                    f.write(b'\x00')
                f.write(b'\x00')
            print(f"Successfully imported {len(self.servers)} servers")
            return True
        except Exception as e:
            print(f"Error importing servers: {e}")
            return False
    
    def extract_texture_pack(self, zip_path, extract_to):
        try:
            os.makedirs(extract_to, exist_ok=True)
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                file_list = zip_ref.namelist()
                root_dirs = set()
                for file in file_list:
                    parts = file.split('/')
                    if len(parts) > 1 and parts[0]:
                        root_dirs.add(parts[0])
                if len(root_dirs) == 1:
                    root_dir = list(root_dirs)[0]
                    for file in file_list:
                        if file.startswith(root_dir + '/') and not file.endswith('/'):
                            dest_path = os.path.join(extract_to, os.path.relpath(file, root_dir))
                            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                            with open(dest_path, 'wb') as dest_file:
                                dest_file.write(zip_ref.read(file))
                    print(f"Extracted {os.path.basename(zip_path)} without root folder")
                else:
                    zip_ref.extractall(extract_to)
                    print(f"Extracted {os.path.basename(zip_path)} normally")
            return True
        except Exception as e:
            print(f"Error extracting {os.path.basename(zip_path)}: {e}")
            return False
    
    def download_texture_packs(self):
        resourcepacks_dir = os.path.join(self.minecraft_dir, "resourcepacks")
        os.makedirs(resourcepacks_dir, exist_ok=True)
        success_count = 0
        for pack in self.texture_packs:
            try:
                print(f"Downloading {pack['name']}...")
                response = requests.get(pack["url"], timeout=30)
                response.raise_for_status()
                pack_path = os.path.join(resourcepacks_dir, pack["name"])
                with open(pack_path, "wb") as f:
                    f.write(response.content)
                print(f"Successfully downloaded {pack['name']}")
                pack_name_without_ext = os.path.splitext(pack["name"])[0]
                extract_path = os.path.join(resourcepacks_dir, pack_name_without_ext)
                if self.extract_texture_pack(pack_path, extract_path):
                    os.remove(pack_path)
                    print(f"Removed zip file: {pack['name']}")
                    success_count += 1
            except Exception as e:
                print(f"Error downloading {pack['name']}: {e}")
        print(f"Successfully processed {success_count}/{len(self.texture_packs)} texture packs")
        return success_count > 0
    
    def import_all_assets(self):
        print("Importing Quarzism Client assets...")
        settings_success = self.download_minecraft_settings()
        servers_success = self.import_servers()
        textures_success = self.download_texture_packs()
        print("Asset import completed!")
        return settings_success or servers_success or textures_success

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Quarzism Client Assets Importer")
    parser.add_argument("--dir", help="Minecraft directory", default=None)
    args = parser.parse_args()
    assets = QuarzismAssets(args.dir)
    success = assets.import_all_assets()
    sys.exit(0 if success else 1)
