import os
import sys
import subprocess

# Configuration files
config_file: str = "config.py"
systemd_service_file: str = "vsfs.service"
systemd_timer_file: str = "vsfs.timer"

# Configuration input
server_location: str = ''
client_location: str = ''
user_config: int = 0

# To change the path to global path and correct the path if user forgot add slash
def pathname(path: str) -> str:
    
    # Make a global path
    path = os.path.abspath(path.strip())
    
    # Check the seperator
    if not path.endswith(os.path.sep):
        path += os.path.sep
    
    return path
 
def config() -> None:
    
    # Write file config.py
    try:
        with open(config_file, 'w') as file:
            file.write("#||| THE CONFIG LOCATION OF SERVER AND CLIENT |||")
            file.write("\n")
            file.write("# You can just change the path location from here,")
            file.write("# and restart the programs, or the systemd service!")
            file.write("\n")
            file.write(f"""server_location: Path = Path('{server_location}') """)
            file.write("\n")
            file.write(f"""client_location: Path = Path('{client_location}') """)
            file.write("\n")
            file.write("# [1] Default: Copy each other from server to client, and client to server")
            file.write("# [2] Server Only: Just copy the client to server if the files list not same")
            file.write("\n")
            file.write(f"user_config: int = {user_config}")
        
    except Exception as e:
        print(f"Error: {e}")

def location() -> tuple[str, str]:
    
    # Make user to input the path location
    server_location: str = input("Please input the server location!\n: ")
    client_location: str = input("Please input the client location!\n: ")
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

def systemd() -> None:
    
    # Make user systemd settings
    systemd_user: str = input("Please input the name user of your systemd: ")
    systemd_group: str = input("Please input the name group of your systemd: ")
    main_py: str = input("Please input where the main.py is located: ")
    main_py: str = pathname(main_py)
    
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
    
    ExecStart={main_py}
    
    StandardOutput=journal
    StandardError=journal
    
    Restart=on-failure
    
    [Install]
    WantedBy=multi-user.target
    """
    
    # Make the time sync
    print("This system will be run every one hour, you can change it in vsfs.timer")
    
    systemd_timer: str = """
    [Unit]
    Description=Run the VSFS every one hour
    
    [Timer]
    OnCalender=*-*-* *:00:00
    
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



""" Main section programs for user input path location """

def main() -> None:
    
     # Declare global variable
    global server_location, client_location, user_config

    
    if os.path.exists(config_file):
        print("|| WELCOME TO VERY SIMPLE FILE SYNC ||")
        print("The file config is already exist!")
        print("Is you want to change it?")
        print("[yes/no]")
        
        while True:
            
            # Make a choice to replace the existed config or not
            choice: str = input(": ").strip().lower()
           
            if choice == "yes" or choice == "y":
                print("Now fill the path location again!\n")
                server_location, client_location = location()
                print("please choice the sync settings!")
                print("[1] Default: Copy each other from server to client, and client to server")
                print("[2] Server Only: Just copy the client to server if the files list not same")
                user_config = user()
                config()
                
                break
            
            elif choice == "no" or choice == "N":
                print("Okey, nothing has change")
                
                break
            
            else:
                print("Your input is incorrect, please select between [yes/no]!")
            
    else:
                
        print("|| WELCOME TO VERY SIMPLE FILE SYNC ||")
        print("Please input your server location, and client location!")
        print("to continue the VERY SIMPLE FILE SYNC program")
        server_location, client_location = location()
        print("\n")
        
        print("please choice the sync settings!")
        print("[1] Default: Copy each other from server to client, and client to server")
        print("[2] Server Only: Just copy the client to server if the files list not same")
        user_config = user()
        config()
        print("\n")
        
        print("Write the configuration complete")
        print("\n")
        
        while True:
            
            # Make choice to create default systemd, or not
            choice:str = input("Create the default systemd for vsfs?\n:").strip().lower()
            
            if choice == "yes" or choice == "y" or choice == "":
                systemd()
                print("The systemd has created!")
                print("You can try to move it to /etc/systemd/system")
                print("And enable, and start the systemd")
                
                break
            
            elif choice == "no" or choice == "n":
                
                break
            
            else:
                print("Your input is incorrect, please select between [yes/no]!")
        
        
if __name__ == "__main__":
    main()
