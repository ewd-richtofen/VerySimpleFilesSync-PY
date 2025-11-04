import os
import sys
import stat
import paramiko
from tqdm import tqdm
from pathlib import Path
from datetime import datetime
from config import server_location, client_location, user_config, sftp_config
from typing import Dict, Tuple

"""--------------------------------- 
||| The Essential Function To Sync |||
---------------------------------"""

# Global declaration
files_info = int         # For size, and mtime
files_map = Dict[str, int]       # For Relative paths -> Information

# Initialize SFTP
def get_sftp():
    
    # Try to connect to sftp server
    try:
        # If user use password
        transport = paramiko.Transport((sftp_config["host"], sftp_config["port"]))
        if "password" in sftp_config:
            transport.connect(username=sftp_config["username"], password=sftp_config["password"])
        
        # If user have authorized_keys
        elif "key_path" in sftp_config:
            key = paramiko.RSAKey.from_private_key_file(sftp_config["key_path"])
            transport.connect(username=sftp_config["username"], pkey=key)
        
        else:
            raise ValueError("No password or key provide for SFTP authentication")
        
        sftp = paramiko.SFTPClient.from_transport(transport)
        return sftp, transport
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
        
# Check status path of server, and client
def stat_server(sftp, server_path: str):
    
    # Return the (size, and mtime) for server files
    try:
        status = sftp.stat(server_path)
        return status.st_size, status.st_mtime
    
    except Exception:
        return None, None

def stat_client(path: Path):

    # Return the (size, and mtime) for client files
    try:
        status = path.stat()
        return status.st_size, status.st_mtime
    
    except Exception:
        return None, None

# list server, and client function
def list_server(sftp) -> files_map:
    
    # Return as {Relative path: (size, mtime)} For every files and dir under server_location
    server_path: str = str(server_location).rstrip("/")
    result: files_map = {}
    
    def _walk(server_dir: str) -> None:
        
        for entry in sftp.listdir_attr(server_dir):
            remote_location = f"{server_dir}/{entry.filename}"
            
            if stat.S_ISDIR(entry.st_mode):
                _walk(remote_location)
                
            else:
                relative = os.path.relpath(remote_location, server_path)
                print(f"[DEBUG] Remote: {relative} | size={entry.st_size} | mtime={entry.st_mtime} ({datetime.fromtimestamp(entry.st_mtime)})")
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
            
            if entry.is_dir():
                _walk(entry)
            
            elif entry.is_file():
                relative: str = str(entry.relative_to(client_path))
                result[relative] = entry.stat().st_size
                
    if client_path.exists():
        _walk(client_path)
    
    else:
        print(f"Client base directory is missing: {client_path}")
    
    return result    

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
    
    # Download progres bar per (bytes)
    file_size = sftp.stat(remote_location).st_size
    
    with tqdm(total=file_size, unit='B', unit_scale=True, desc=desc, leave=False) as bar:
        def callback(transferred, total):
            bar.update(transferred - bar.n)
        
        with open(client_location, "wb") as f:
            sftp.getfo(remote_location, f, callback=callback)

def _put_progress(sftp, client_location: str, remote_location: str, desc: str) -> None:
    
    # Upload progress bar per (bytes)
    file_size = os.path.getsize(client_location)
    
    with tqdm(total=file_size, unit='B', unit_scale=True, desc=desc, leave=False) as bar:
        def callback(transferred, total):
            bar.update(transferred - bar.n)
            
        with open(client_location, "rb") as f:
            sftp.putfo(f, remote_location, callback=callback, confirm=True)         

# Copy files from server to client
def copy_server(sftp, download: list[str]) -> None:
    
    # Make individual dir of server files
    for file in tqdm(download, desc="Downloading", unit="File"):
        remote_file = str(server_location / file)
        local_file = client_location / file
        local_file.parent.mkdir(parents=True, exist_ok=True)

        # Cause paramiko dosn't support callback, wrap the sfpt.get that update tqdm
        try:
            # Get remote file size, and mtime
            remote_stat = sftp.stat(remote_file)
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
    for file in tqdm(upload, desc="Uploading", unit="File"):
        client_file = client_location / file
        remote_file = str(server_location / file)
        
        # Creating sub-folder for remote files
        remote_dir = os.path.dirname(remote_file)
        _mkdir_p(sftp, remote_dir)

        # Cause paramiko dosn't support callback, wrap the sfpt.put that update tqdm
        try:
            # get client mtime
            client_mtime = client_file.stat().st_mtime
            
            # Uploading progress
            _put_progress(sftp, str(client_file), remote_file, desc=file)
            
            # Set mtime via SFTP, and convert to (seconds, nanoseconds)
            try:
                sftp.utime(remote_file, (client_mtime, client_mtime))
            
            except Exception as e:
                print(f"[WARN] Failed to set mtime on server for {file}: {e}")
            
        except FileNotFoundError as e:
            print(f"Error: {e}")
            
        except PermissionError as e:
            print(f"Error: {e}")
            
        except Exception as e:
            print(f"Failed Upload {file}: {e}")

def _mkdir_p(sftp, remote_dir: str):
    
    # Create remote directory recursively
    try:
        sftp.listdir(remote_dir)
        
    except FileNotFoundError:
        parent = os.path.dirname(remote_dir)
        
        if parent and parent != remote_dir:
            _mkdir_p(sftp, parent)
        sftp.mkdir(remote_dir)

"""-------------------------------------- 
||| The Main Function Of This Program |||
--------------------------------------"""

def main() -> None:
    
    # Intialize SFTP connection
    sftp, transport = get_sftp()
    
    # Declare the list
    server_map = list_server(sftp)
    client_map = list_client()

    download, upload = compute_diffs(server_map, client_map)
   
    # User configuration
    try:
        
        if user_config == 1:
            
            if download:
                copy_server(sftp, download)
            
            if upload:
                copy_client(sftp, upload)
            print("\nSynchronization complete (bidirectional)")

        else:
            
            if upload:
                copy_client(sftp, upload)
            print("\nSynchronization complete (client to server only)")
        
        if not (download or upload):
            print("\nNothing to sync - trees are identical")
        
    finally:
        # Close SFTP connection
        sftp.close()
        transport.close()

if __name__ == "__main__":
    main()