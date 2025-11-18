# Very Simple Files Sync | write on Python
<i>Warning!!!</i>

The vsfs program for now is specific, and only can use with sftp_client protocol with module by <i>`PARAMIKO`</i> to serve as <u>server</u> side!, and use the Local Directory as <u>client</u> side

# USER GUIDE

<b>FRIST</b>

Try to clone the reposity to your machine. `git clone https://github.com/ewd-richtofen/VerySimpleFilesSync-PY.git`

Try run the binary `./dist/verysimplefilesync`, if you want run the python file run on main directory `python3 vsfs.py`

Python dependencies that required !

```
python-paramiko
python-colorama
```

<b>SECOND</b>

<details>
<summary>[1] Create/Change configuration!</summary>

The main function to create a `config.py` as user configuration, If there already a `config.py` file, it will be rewrite the file

</details>

<details>
<summary>[2] Get client files!</summary>

The function to copy a tree files from server `(sftp)` to client `(local)`

</details>

<details>
<summary>[3] Put server files!</summary>

The function to copy a tree files from client `(local)` to server `(sftp)`

</details>

<details>
<summary>[4] List Server!</summary>

The function to show visual tree from server `(sftp)` directory

</details>

<details>
<summary>[5] Deletes files!</summary>

The function will make a choice between `server` and `client`, write the available to delete files

It delete files that not in between `server` and `client`

<b>Example</b>

```
Deletes [server] or [client]
-> client
[F] /home/sakana/Documents/code/py/test/Untitled Document | 1
[D] /home/sakana/Documents/code/py/test/Untitled Folder
[F] /home/sakana/Documents/code/py/test/ssss.txt | 1


Are you sure want to remove files in above?
: y

Finished: 3/3 items removed from client.
Closing SFTP...
Closing Transport...
Connection closed.
```

All file and directory in above are not in `server`

</details>

<details>
<summary>[6] Make systemd!</summary>

The function is to make systemd files as `vsfs.service`, and `vsfs.timer`, it will be run the `main.py` every day (every 24h). If use this command you must in main directory `VerySimpleFilesSynce-PY` to make the exec dir is correct!

</details>

<details>
<summary>[0] Exit!!!</summary>

Exit / Done

</details>

# Next update

- ~~Automatic move the systemd with shell~~

- ~~Filter the folder~~

- Whitelist, and Blacklist

- Profiles list

- GUI

- Make a bunch of choice, like samba, sftp, and local only
