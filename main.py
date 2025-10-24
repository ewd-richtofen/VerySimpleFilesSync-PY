import os
import sys
import subprocess
import shutil
from pathlib import Path
from config import server_location, client_location, user_config

# list server, and client function
def list_server() -> set:
    return {d.name for d in server_location.iterdir() if d.is_file()}

def list_client() -> set:
    return {d.name for d in client_location.iterdir() if d.is_file()}

# Declare the list
server_set: set = list_server()
client_set: set = list_client()

# Determine which file to be copy from server side, or client side
server_side: set = server_set - client_set
client_side: set = client_set - server_set

# copy file from server to client, or client to server function
def copy_server() -> None:
    for file in server_set:
        server_file = server_location / file

        try:
            shutil.copy(server_file, client_location)
        except FileNotFoundError as e:
            print(f"Error: {e}")
        except PermissionError as e:
            print(f"Error: {e}")

def copy_client() -> None:
    for file in client_set:
        client_file = client_location / file

        try:
            shutil.copy(client_file, server_location)
        except FileNotFoundError as e:
            print(f"Error: {e}")
        except PermissionError as e:
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
            copy_server()

        # The client have more files than server
        if client_side:
            copy_client()
        
        print("\nThe synchronization is complete")

    else:
        print("\nDon't process the synchronization, the files already sync")

# The oneside configuration it just copy file from client to server as backup option
def oneside() -> None:
    if client_side:
        copy_client()

        print("\nThe synchronization is complete")

    else:
        print("\nDon't process the synchronization, the files already sync")

def main() -> None:
    if user_config == 1:
        default()

    else:
        oneside()



if __name__ == "__main__":
    main()
