import os
import sys
import paramiko
from pathlib import Path
from datetime import datetime
from config import server_location, client_location, user_config, sftp_config

# Initialize SFTP
def get_sftp():
    try:
        # If user use password
        transport = paramiko.Transport((sftp_config["host"], sftp_config["port"]))
        if "password" in sftp_config:
            transport.connect(username=sftp_config["username"], password=sftp_config["password"])
        
        # If user have authorized_keys
        elif "id_rsa" in sftp_config:
            key = paramiko.RSAKey.from_private_key_file(sftp_config=["id_rsa"])
            transport.connect(username=sftp_config["username"], pkey=key)
        
        else:
            raise ValueError("No password or key provide for SFTP authentication")
        
        sftp = paramiko.SFTPClient.from_transport(transport)
        return sftp, transport
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
        

# list server, and client function
def list_server() -> set:
    try:
        return set(sftp.listdir(str(server_location)))
    
    except Exception as e:
        print(f"Error: {e}")
        return set()

def list_client() -> set:
    return {d.name for d in client_location.iterdir() if d.is_file()}

# copy file from server to client, or client to server function
def copy_server(sftp) -> None:
    for file in server_set:
        server_file = server_location / file

        try:
            sftp.get(server_file, client_location)
        except FileNotFoundError as e:
            print(f"Error: {e}")
        except PermissionError as e:
            print(f"Error: {e}")
        except Exception as e:
            print(f"Error: {e}")


def copy_client(sftp) -> None:
    for file in client_set:
        client_file = client_location / file

        try:
            sftp.put(client_file, server_location)
        except FileNotFoundError as e:
            print(f"Error: {e}")
        except PermissionError as e:
            print(f"Error: {e}")
        except Exception as e:
            print(f"Error: {e}")

"""-------------------------------------------- 
||| The main function that run this program |||
--------------------------------------------"""

# The default configuration that make each file from server, and client 
# will be copy each other if one of them dont have the exact same file name
def default() -> None:
    if server_side or client_side:

        # The server have more files than client
        if server_side:
            copy_server(sftp)

        # The client have more files than server
        if client_side:
            copy_client(sftp)
        
        print("\nThe synchronization is complete")

    else:
        print("\nDon't process the synchronization, the files already sync")

# The oneside configuration it just copy file from client to server as backup option
def oneside() -> None:
    if client_side:
        copy_client(sftp)

        print("\nThe synchronization is complete")

    else:
        print("\nDon't process the synchronization, the files already sync")

def main() -> None:
    # Intialize SFTP connection
    sftp, transport = get_sftp()
    
    # Global variable
    global server_set, client_set, server_side, client_side
    
    # Declare the list
    server_set = list_server(sftp)
    client_set = list_client()

    # Determine which file to be copy from server side, or client side
    server_side = server_set - client_set
    client_side = client_set - server_set

    # User configuration
    try:
        
        if user_config == 1:
            default()

        else:
            oneside()
        
    finally:
        # Close SFTP connection
        sftp.close()
        transport.close()

if __name__ == "__main__":
    main()
