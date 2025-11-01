#!/bin/sh

#################################################
### This For Moving The Systemd Configuration ###
#################################################

systemd_service="vsfs.service"
systemd_timer="vsfs.timer"

if ! [ -f "$systemd_service" ] && ! [ -f "$systemd_timer" ]; then

    printf "\n\e[1;31mThe Systemd Configuration Not Found\n"
    printf "Please Generate The Systemd Configuration Frist!\n\e[0m\n"

    exit 1

fi

# Move the files to systemd configuration directory
sudo mv $systemd_service /etc/systemd/system/.
sudo mv $systemd_timer /etc/systemd/system/.

# Restart systemd_daemon and start the systemd
sudo systemctl daemon-reload
sudo systemctl enable vsfs.service
sudo systemctl start vsfs.service
sudo systemctl enable vsfs.timer
sudo systemctl start vsfs.timer

printf "THE INSTALLATION OF SYSTEMD SUCCES\n"