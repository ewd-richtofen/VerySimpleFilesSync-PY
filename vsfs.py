import os
import sys
import json
import getpass
import subprocess
from pathlib import Path
from core.main import list_server_files, get_files, put_files, delete_server, delete_client

# Configuration files
config_dir: Path = Path("config")
config_dir.mkdir(exist_ok=True)
config_file: Path = config_dir / "config.py"
systemd_service_file: str = "vsfs.service"
systemd_timer_file: str = "vsfs.timer"
move_files = "activate.sh"

# Configuration input
server_location: str = ''
client_location: str = ''
user_config: int = 0
sftp_conf = '{}'

"""--------------------------- 
||| The Essential Function |||
---------------------------"""

# To change the path to global path and correct the path if user forgot add slash
def pathname(path: str) -> str:
    
    # Make a global path
    path = os.path.abspath(path.strip())
    
    # Check the seperator
    if not path.endswith(os.path.sep):
        path += os.path.sep
    
    return path
 
def config(server_loc: str, client_loc: str, user_cfg: int, sftp_cfg: str) -> None:
    
    # Write file config.py
    try:
        with open(config_file, 'w') as file:
            file.write("#||| THE CONFIG LOCATION OF SERVER AND CLIENT |||")
            file.write("\n\n")
            file.write("# You can just change the path location from here,")
            file.write("# and restart the programs, or the systemd service!")
            file.write("\n\n")
            file.write("from pathlib import Path")
            file.write("\n\n")
            file.write(f"""server_location: Path = Path('{server_loc}') """)
            file.write("\n")
            file.write(f"""client_location: Path = Path('{client_loc}') """)
            file.write("\n\n")
            file.write("# [1] Default: Copy each other from server to client, and client to server")
            file.write("# [2] Server Only: Just copy the client to server if the files list not same")
            file.write("\n\n")
            file.write(f"user_config: int = {user_cfg}")
            file.write("\n\n")
            file.write("# The SFTP remote configuration")
            file.write("\n\n")
            file.write(f"sftp_config: dict = {sftp_cfg}")
            
        print(f"{config_file} has been written successfully.")
        
    except Exception as e:
        print(f"Error: {e}")

def location() -> tuple[str, str]:
    
    # Make user to input the path location
    server_location: str = input("Please input the server location!\n> ")
    client_location: str = input("Please input the client location!\n> ")
    server_location: str = pathname(server_location)
    client_location: str = pathname(client_location)
    
    return server_location, client_location

def user() -> int:
    
    # Make user choice of the configuration settings
    while True:
        user_input: str = str(input(": "))
        
        if user_input == "1" or user_input == "":
            user_config: int = 1
            break
        elif user_input == "2":
            user_config: int = 2
            break
        else:
            continue
        
    return user_config

def sftp():
    
    # Make sftp configuration file
    while True:

        # Input the user sftp
        username: str = input("Please input username!: ")
        host: str = input("Please input host!: ")
        port: int = int(input("Please input port!: "))
        
        sftp_config = {"host": host, "port": port, "username": username}
        
        while True:
            
            # Input option
            print("Do you want login with key or password?")
            user_input: str = input("[K/P]: ")
            user_input: str = user_input.upper()
            
            if user_input not in ("K", "P"):
                print("Invalid input!")
                
                continue
            
            break
            
        if user_input == "P":
            password: str = getpass.getpass("Please input password!\n: ")
            
            sftp_config: dict = {
                "host": f"{host}",
                "port": port,
                "username": f"{username}",
                "password": f"{password}"
            }
            
            break
        
        elif user_input == "K":
            key: str = input("Please input your key location!\n> ")

            sftp_config: dict = {
                "host": f"{host}",
                "port": port,
                "username": f"{username}",
                "key_path": f"{key}"
            }
            
            break
            
        else:
            print(f"Invalid input: {user_input}")
            
    while True:
        
        # Make sure user SFTP profile is correct
        print("\nSFTP Config Preview:")
        print(json.dumps(sftp_config, indent=4))
        confirm = input("\nIs this correct? [Y/n]: ").strip().lower()
        
        if confirm in ("", "y", "yes"):
            
            return json.dumps(sftp_config, indent=4)
        
        else:
            print("Restarting configuration...\n")
            
            continue
            
def systemd() -> None:
    
    # Make user systemd settings
    systemd_user: str = input("Please input the name user of your systemd: ")
    systemd_group: str = input("Please input the name group of your systemd: ")
    
    # Check location of this program
    main_py = subprocess.run(
        ["pwd"],
        capture_output=True,
        text=True,
        check=True
    )
    
    main_py = pathname(main_py.stdout)
    main_py = main_py + "core/sync.py"
    
    # Systemd.service config
    systemd_service: str = f"""
[Unit]
Description=Very Simple Files Sync
Requires=network-online.target
After=network-online.target

[Service]
User={systemd_user}
Group={systemd_group}

Type=oneshot

ExecStart=/usr/bin/python3 {main_py}

StandardOutput=journal
StandardError=journal

Restart=on-failure

[Install]
WantedBy=multi-user.target
"""

    # Make the time sync
    print("This system will be run every Day(24h), you can change it in vsfs.timer")
    
    systemd_timer: str = """
[Unit]
Description=Run the VSFS every day

[Timer]
OnCalendar=daily

Persistent=true

[Install]
WantedBy=timers.target
"""
    
    try:
        with open(systemd_service_file, 'w') as service:
            service.write(systemd_service)
        with open(systemd_timer_file, 'w') as timer:
            timer.write(systemd_timer)
    
    except Exception as e:
        print(f"Error: {e}")

"""---------------------- 
||| The Menu Function |||
----------------------"""

def write_config() -> None:
    
     # Declare global variable
    global server_location, client_location, user_config

    if os.path.exists(config_file):
        print("The file config is already exist!")
        print("Is you want to change it?")
        print("[y/N]")
        
        while True:
            
            # Make a choice to replace the existed config or not
            choice: str = input(": ").strip().lower()
            print("\n")
           
            if choice == "" or choice == "y" or choice == "Y":
                print("Now fill the path location again!\n")

                server_location, client_location = location()
                print("please choice the sync settings!")
                print("[1] Default: Copy each other from server to client, and client to server")
                print("[2] Server Only: Just copy the client to server if the files list not same")
                
                user_config = user()
                print("Please input the SFTP configuration!")

                sftp_conf = sftp()
                print("\n")

                config(server_location, client_location, user_config, sftp_conf)
                
                break
                
            elif choice == "n" or choice == "N" :
                print("Okey, Nothing has change")
                
                break
            
            else:
                print(f"Invalid input: {choice}")
                
    else:
                
        print("Creating the config file!!!")
        print("Please input your server location, and client location!")

        server_location, client_location = location()
        print("\n")
        
        print("please choice the sync settings!")
        print("[1] Default: Copy each other from server to client, and client to server")
        print("[2] Server Only: Just copy the client to server if the files list not same")

        user_config = user()
        print("\n")
        
        print("Please input the SFTP configuration!")

        sftp_conf = sftp()
        config(server_location, client_location, user_config, sftp_conf)
        print("\n")

        print("Write the configuration complete")
        print("\n")

def write_systemd() -> None:

        while True:
            
            # Make choice to create default systemd, or not
            print("Create the default systemd for vsfs?")
            choice:str = input("[yes/no]: ").strip().lower()
            
            if choice == "yes" or choice == "y" or choice == "":
                systemd()
                subprocess.run(["sh",move_files])
                print("The systemd has created!")
                
                break
            
            elif choice == "no" or choice == "n":
                
                break
            
            else:
                
                continue
        
#############################################
""" Main section programs for Menu Option """
#############################################

# Main menu
def menu() -> None:
    
    # Show menu options
    print("Menu option list!")
    print("[1] -> Create/Change configuration!")
    print("[2] -> Get client files!")
    print("[3] -> Put server files!")
    print("[4] -> List Server!")
    print("[5] -> Deletes files!")
    print("[6] -> Make systemd!")
    print("[0] -> Exit!!!")

    user_input: int = int(input("> "))
    
    while True:
        
        if user_input == 1 :
            write_config()
            
            break
        
        elif user_input == 2 :
            get_files()
            
            break
                
        elif user_input == 3 :
            put_files()

            break
            
        elif user_input == 4 :
            list_server_files()
            
            break
        
        elif user_input == 5 :
            print("\n")
            print("Deletes [server] or [client]")
            another_input = input("-> ")

            while True:

                if another_input == "server":
                    delete_server()

                    break

                elif another_input == "client":
                    delete_client()

                    break

                else:
                    print("Please select avaible options")

            break
         
        elif user_input == 6 :
            systemd()
            
            break
        
        elif user_input == 0 :
            sys.exit(0)

        else:
            continue

if __name__ == "__main__":
    while True:
        menu()