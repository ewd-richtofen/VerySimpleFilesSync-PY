import os
import sys
import stat
import paramiko
from pathlib import Path
from datetime import datetime
from config.config import server_location, client_location, user_config, sftp_config
from typing import Dict, Tuple
from colorama import Fore, Style, init

# Intialise colourama
init(autoreset=True)

# Global declaration
files_info = int         # For size, and mtime
files_map = Dict[str, int]       # For Relative paths -> Information

"""---------------------- 
||| The SFTP Function |||
----------------------"""

# SFTP Manager
class SFTP:
    
    # Manage the SFTP connection cycle
    def __init__(self) -> None:
        self.sftp = None
        self.transport = None
        
        try:
            self.transport = paramiko.Transport((sftp_config["host"], sftp_config["port"]))
            
            if "password" in sftp_config:
                self.transport.connect(username=sftp_config["username"], password=sftp_config["password"])
            
            # If user have authorized_keys
            elif "key_path" in sftp_config:
                key = paramiko.RSAKey.from_private_key_file(sftp_config["key_path"])
                self.transport.connect(username=sftp_config["username"], pkey=key)
            
            else:
                raise ValueError("No password or key provide for SFTP authentication")
            
            self.sftp = paramiko.SFTPClient.from_transport(self.transport)

        except Exception as e:
            print(f"Error establishing SFTP connection: {e}")
            
            if self.transport:
                self.transport.close()
                
            raise
        
    # Remove files
    def remove(self, path) -> None:
        
            if self.sftp is None:
                raise RuntimeError("SFTP client not initialized")
            
            self.sftp.remove(path)
    
    # Remove empty dir
    def rmdir(self, path) -> None:
        
        if self.sftp is None:
            raise RuntimeError("SFTP client not initialized")
        
        self.sftp.rmdir(path)
    
    # Return metada paramiko
    def stat(self, path) -> paramiko.SFTPAttributes:
        
        if self.sftp is None:
            raise RuntimeError("SFTP client not initialized")

        return self.sftp.stat(path)
    
    # Listdir paramiko
    def listdir_attr(self, path: str = ".") -> list[paramiko.SFTPAttributes]:
    
        if self.sftp is None:
            raise RuntimeError("SFTP client not initialized")
        
        return self.sftp.listdir_attr(path)
        
    # Closing sftp connection
    def close(self) -> None:
        
        if self.sftp:
            self.sftp.close
        
        if self.transport:
            self.transport.close
            
"""-------------------------------
||| The Status Metada Function |||
-------------------------------"""
        
# Check status metadata ( size, and mtime ) of server
def stat_server(sftp, server_path: str):
    
    # Return the (size, and mtime) for server files
    try:
        status = sftp.sftp.stat(server_path)
        
        return status.st_size, status.st_mtime
    
    except Exception:
        
        return None, None

# Check status metadata ( size, and mtime ) of client
def stat_client(path: Path):

    # Return the (size, and mtime) for client files
    try:
        status = path.stat()
        
        return status.st_size, status.st_mtime
    
    except Exception:
        
        return None, None

"""-------------------------------- 
||| The List Directory Function |||
--------------------------------"""

# list server, and client function
def list_server(sftp_manager) -> files_map:
    
    # Return as {Relative path: (size, mtime)} For every files and dir under server_location
    server_path: str = str(server_location).rstrip("/")
    result: files_map = {}
    
    def _walk(server_dir: str) -> None:
        
        for entry in sftp_manager.sftp.listdir_attr(server_dir):
            remote_location = f"{server_dir}/{entry.filename}"
            relative = os.path.relpath(remote_location, server_path)
            
            if stat.S_ISDIR(entry.st_mode):
                result[relative] = 0
                _walk(remote_location)
                
            else:
                result[relative] = entry.st_size
            
    try:
        _walk(server_path)
    
    except Exception as e:
        print(f"Error walking to server tree: {e}")
        
    return result
        
def list_client() -> files_map:
    
    # Return as {Relative paths: (size, mtime)} For every files and dir under client_location
    client_path = client_location
    result: files_map = {}
    
    def _walk(client_dir: Path) -> None:
        
        for entry in client_dir.iterdir():
            
            relative: str = str(entry.relative_to(client_path))
            
            if entry.is_dir():
                result[relative] = 0
                _walk(entry)
            
            elif entry.is_file():
                result[relative] = entry.stat().st_size
                
    if client_path.exists():
        _walk(client_path)
    
    else:
        print(f"Client base directory is missing: {client_path}")
    
    return result    

"""---------------------- 
||| The Copy Function |||
----------------------"""

# Copy files from server to client
def copy_server(sftp, download: list[str]) -> None:
    
    # Make individual dir of server files
    for file in download:
        if not file.strip():
            
            continue
        
        print(f"  → {file}")
        remote_file = str(server_location / file)
        local_file = client_location / file
        local_dir = local_file.parent

        # Fix conflict files and dir
        #_____________________________

        if local_dir != client_location:
            if local_dir.exists():
                if not local_dir.is_dir():
                    print(f"[SKIP] {file}")
                    print(f"[CONFLICT] {local_dir} is FILE, not DIR")
                    
                    continue
                   
            else:
                try:
                    local_dir.mkdir(parents=True, exist_ok=True)
                    
                except Exception as e:
                    print(f" [ERROR] Cannot create local dir {local_dir}: {e}")
                    
                    continue

                    

        # Cause paramiko dosn't support callback, wrap the sfpt.get that update tqdm
        try:
            # Get remote file size, and mtime
            remote_stat = sftp.sftp.stat(remote_file)
            remote_mtime = remote_stat.st_mtime
            
            # Downloading progress
            _get_progress(sftp, remote_file, str(local_file), desc=file)
            
            # Match the mtime
            if remote_mtime > 0:
                fix_mtime(str(local_file), remote_mtime)
                
            else:
                print(f"Warning: Invalid mtime {remote_mtime} for {file}")
                       
        except FileNotFoundError as e:
            print(f"Error: {e}")
            
        except PermissionError as e:
            print(f"Error: {e}")
            
        except Exception as e:
            print(f"Failed Download {file}: {e}")

#Copy files from client to server
def copy_client(sftp, upload: list[str]) -> None:

    # Make individual dir of client files
    for file in upload:
        print(f"  → {file}")
        client_file = client_location / file
        remote_file = str(server_location / file)
        
        # Creating sub-folder for remote files
        remote_dir = os.path.dirname(remote_file)
        _mkdir_p(sftp, remote_dir)
        
        # Fix conflict files and dir
        #_____________________________
        
        if remote_dir and remote_dir != str(server_location):
            
            try:
                # Check what already exist at remote_dir
                status = sftp.stat(remote_dir)
                
                # If directory it pass and continue
                if stat.S_ISDIR(status.st_mode):
                    
                    pass 
                
                # If files it continue and ignore
                else:
                    print(f"[SKIP] {file}")
                    print(f"[CONFLICT] {remote_dir} is FILE, not DIR")
                    
                    continue
                
            except FileNotFoundError:
                _mkdir_p(sftp, remote_dir)
                
        #______________________________

        # Cause paramiko dosn't support callback, wrap the sfpt.put that update tqdm
        try:
            # get client mtime
            client_mtime = client_file.stat().st_mtime
            
            # Uploading progress
            _put_progress(sftp, str(client_file), remote_file, desc=file)
            
            # Set mtime via SFTP, and convert to (seconds, nanoseconds)
            try:
                sftp.sftp.utime(remote_file, (client_mtime, client_mtime))
            
            except Exception as e:
                print(f"[WARN] Failed to set mtime on server for {file}: {e}")
            
        except FileNotFoundError as e:
            print(f"Error: {e}")
            
        except PermissionError as e:
            print(f"Error: {e}")
            
        except Exception as e:
            print(f"Failed Upload {file}: {e}")
            
# Making a dir if is not there
def _mkdir_p(sftp, remote_dir: str):
    
    # Create remote directory recursively
    try:
        sftp.sftp.listdir(remote_dir)
        
        return
        
    except FileNotFoundError:
        parent = os.path.dirname(remote_dir)
        
        if parent and parent != remote_dir:
            _mkdir_p(sftp, parent)
            
        try:
            sftp.sftp.mkdir(remote_dir)
            print(f"[CREATE DIR] -> {remote_dir}")
            
        except OSError as e:
            if e.errno != 17:
                
                raise
            
    except Exception as e:
        print(f"[ERROR] Failed to create dir {remote_dir}: {e}")

"""--------------------------- 
||| The Essential Function |||
---------------------------"""

# Determine what to copy
def compute_diffs(server_map: files_map, client_map: files_map):
    
    # Return as (download, and upload) -> List of Relative paths
    download = []
    upload = []
    
    all_location = set(server_map) | set(client_map)
    
    for relative in all_location:
        server_size = server_map.get(relative)
        client_size = client_map.get(relative)
        
        if server_size is None:
            upload.append(relative)
            
        elif client_size is None:
            download.append(relative)
        
        else:
            if server_size != client_size:
                download.append(relative)
                                    
    return download, upload

# Fix modified time status don't match
def fix_mtime(path: str, mtime: float) -> None:
    
    # Skip termux
    if not mtime or mtime <= 0:
        print(f"[WARN] Invalid mtime {mtime} for {path} — skipping")
        
        return
    
    # Fix the file date, to match with original modified date
    try:
        os.utime(path, (mtime, mtime))
        print(f"[OK] Set mtime on {path} → {datetime.fromtimestamp(mtime)}")
        
    except Exception as e:
        print(f"Failed to set mtime on {path}: {e}")

# A wrapper for show a progress bar
def _get_progress(sftp, remote_location: str, client_location: str, desc: str) -> None:
    
    try:
        # Download progres bar per (bytes)
        file_size = sftp.stat(remote_location).st_size
        download = 0
        print(f"[DOWNLOAD] {desc} | 0 B / {file_size // 1024} KB", end="")
        
        def callback(transferred, total):
            nonlocal download
            download = transferred
            percent = (transferred / file_size) * 100
            print(f"\r[DOWNLOAD] {desc} | {transferred // 1024} KB / {file_size // 1024} KB ({percent:.1f}%)", end="")
        
        sftp.sftp.get(remote_location, client_location, callback=callback)     
        print(f"\n[OK] Downloaded: {desc}")

    except Exception as e:
        print(f"\n[Error] Download failed {desc}: {e}")

# Progress bar on upload
def _put_progress(sftp, client_location: str, remote_location: str, desc: str) -> None:
   
    try:
        # Upload progress bar per (bytes)
        file_size = os.path.getsize(client_location)
        upload = 0
        print(f"[UPLOAD] {desc} | 0 B / {file_size // 1024} KB", end="")
        
        def callback(transferred, total):
            nonlocal upload
            upload = transferred
            percent = (transferred / file_size) * 100
            print(f"\r[UPLOAD] {desc} | {transferred // 1024} KB / {file_size // 1024} KB ({percent:.1f}%)", end="")
            
        sftp.sftp.put(client_location, remote_location, callback=callback, confirm=True)   
            
        print(f"\n[OK] Uploaded: {desc}")      

    except Exception as e:
        print(f"[Error] Upload failed {desc}: {e}")

"""---------------------- 
||| The Menu Function |||
----------------------"""

# List the files of server
def list_server_files():
    
    # Intialize SFTP connection
    sftp = SFTP()
    
    list = list_server(sftp)
    
    try:
        
        # Tree function
        def tree(dictionary):
            
            tree = {}
            
            for location, size in dictionary.items():
                path = location.split('/')
                current = tree
                
                for p in path:
                    if p not in current:
                        current[p] = {'_size': 0, '_children': {}}
                    current = current[p]['_children']
                current['_size'] = size
                
            return tree
        
        # Make visual to tree
        def tree_visual(node, prefix="", is_last=True, is_root=True):
            
            if is_root:
                server_dir = str(server_location)
                server_root = os.path.basename(server_dir.rstrip('/\\'))
                print(server_root)
                new_prefix = ""
            
            else:
                connector = "└── " if is_last else "├── "
                
                # Get the name of this node (we need to pass it from parent)
                new_prefix = prefix + ("    " if is_last else "|    ")
                
            # Get all children
            children = []
            
            for key, value in node.items():
                if key == '_size':
                    
                    continue
                
                children.append((key, value))
                
            # Sort for consistent output
            children.sort(key=lambda x: x[0])
            
            for i, (name, child_node) in enumerate(children):
                is_last_child = (i == len(children) -1)
                
                # Determine if this is a file or directory
                size = child_node.get('_size', 0)
                
                if size > 0:
                    # it's files
                    size_str = f" ({size} bytes)"
                    
                else:
                    # it's directory
                    size_str = ""
                    
                connector = "└── " if is_last_child else "├── "
                print(prefix + connector + name + size_str)
                
                # Recurse into children
                child_prefix = prefix + ("    " if is_last_child else "│   ")
                tree_visual(child_node['_children'], child_prefix, is_last_child, is_root=False)

        tree_dir = tree(list)
        tree_visual(tree_dir)
        
    except Exception as e:
        print(f"Listing error: {e}")
        
    finally:
        sftp.close()
        print("\n")

# Transfer files from server to client
def get_files() -> None:

    # Intialize SFTP connection
    sftp = SFTP()
    
    # Declare the list
    server_map = list_server(sftp)
    client_map = list_client()

    download, upload = compute_diffs(server_map, client_map)

    try:

        if download:
            copy_server(sftp, download)
            print(f"{Fore.GREEN}Getting Files from server complete!")

        else:
            print(f"{Fore.YELLOW}Files already in directory, Program not processing!")

    except Exception as e:
        print(f"{Fore.RED}Error: {e}")

    finally:
        sftp.close()
        print("\n")

# Transfer files from client to server  
def put_files() -> None:

    # Intialize SFTP connection
    sftp = SFTP()
    
    # Declare the list
    server_map = list_server(sftp)
    client_map = list_client()

    download, upload = compute_diffs(server_map, client_map)

    try:

        if upload:
            copy_client(sftp, upload)
            print(f"{Fore.GREEN}Getting Files from server complete!")

        else:
            print(f"{Fore.YELLOW}Files already in directory, Program not processing!")

    except Exception as e:
        print(f"{Fore.RED}Error: {e}")

    finally:
        sftp.close()
        print("\n")

# Deletes the file from server is there files that not in client
def delete_server() -> None:
    
    sftp = SFTP()
    
    try:
        
        server_files = list_server(sftp)
        client_files = list_client()

        # List files or dir on client, that not in server
        delete = [p for p in server_files if p not in client_files]
        
        if not delete:
            print("There are no FILES or DIR, that are missing on in server")
            
            return
            
        for path in delete:
            full_path = str(server_location / path)
            
            try:
                status = sftp.stat(full_path)
                
                if stat.S_ISREG(status.st_mode):
                    size = status.st_size
                    
                    print(f"[F] {path} | {size}")
                    
                elif stat.S_ISDIR(status.st_mode):
                    print(f"[D] {path}")
                    
                else:
                    print(f"[?] {path}")
            
            except FileNotFoundError:
                print(f"Files are disappeared on server: {path}")
                
                continue
            
            except Exception as e:
                print(f"[Error] Could not get status for {path}: {e}")
                
                continue
            
        print("\n")
        print("Are you sure want to remove files in above?")
        confirm = input(": ").strip().lower()
        
        if confirm != 'y':
            print("Deletion cancelled.")
            
            return

        deleted = 0
        for files in delete:
            full_path = str(server_location / files)
                    
            try:
                status = sftp.stat(full_path)
                
                if stat.S_ISREG(status.st_mode):
                    sftp.remove(full_path)
            
                elif stat.S_ISDIR(status.st_mode):
                    sftp.rmdir(full_path)

                else:
                    print(f"Skipped (not file/dir): {files}")
                    
                deleted += 1
                                
            except OSError as e:
                print(f"[Error] {files} -> {e}")
                
            except Exception as e:
                print(f"[Unexpected] {files} -> {e}")
                
        print(f"\nFinished: {deleted}/{len(delete)} items removed from server.")

    finally:
        sftp.close()
        print("\n")
        
# Deletes the file from client is there files that not in server
def delete_client() -> None:
    
    sftp = SFTP()
    
    try:
        
        server_files: Dict[str, int] = list_server(sftp)
        client_files: Dict[str, int] = list_client()

        # List files or dir on client, that not in server
        delete = [p for p in client_files if p not in server_files]
        
        if not delete:
            print("There are no FILES or DIR, that are missing on in server")
            
            return
            
        for p in delete:
            full_path = client_location / p
            path = full_path
            
            if path.is_file():
                size = path.stat().st_size
                print(f"[F] {path} | {size}")
                
            elif path.is_dir():
                print(f"[D] {path}")
                
            else:
                print(f"[?] {path}")
            
        print("\n")
        print("Are you sure want to remove files in above?")
        confirm = input(": ").strip().lower()
        
        if confirm != 'y':
            print("Deletion cancelled.")
            
            return

        deleted = 0
        for f in delete:
            full_path = client_location / f
            files = full_path
            
            try:
                if files.is_file():
                    files.unlink()
            
                elif files.is_dir():
                    files.rmdir()

                else:
                    print(f"Skipped (not file/dir): {f}")
                    
                deleted += 1
                                
            except OSError as e:
                print(f"[Error] {files} -> {e}")
                
            except Exception as e:
                print(f"[Unexpected] {files} -> {e}")
                
        print(f"\nFinished: {deleted}/{len(delete)} items removed from client.")

    finally:
        sftp.close()
        print("\n")