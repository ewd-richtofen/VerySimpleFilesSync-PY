from core.main import SFTP, list_server, list_client, compute_diffs, copy_server, copy_client, user_config

#################################################
### ||| The Synchronization for Systsemd ||| ###
################################################

def main() -> None:
    
    # Intialize SFTP connection
    sftp = SFTP()
    
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

if __name__ == "__main__":
    main()