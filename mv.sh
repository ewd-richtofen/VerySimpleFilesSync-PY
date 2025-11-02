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
if  sudo mv $systemd_service /etc/systemd/system/. && \
    sudo mv $systemd_timer /etc/systemd/system/.; then

    printf "\e[1;32mThe moving process Complete!\e[0m\n"

else
    printf "\e[1;31mThe moving process is Failed!\e[0m\n"

fi

# Restart systemd_daemon and start the systemd
if  sudo systemctl daemon-reload && \
    sudo systemctl enable vsfs.service &&
    sudo systemctl start vsfs.service &&
    sudo systemctl enable vsfs.timer &&
    sudo systemctl start vsfs.timer; then

    printf "\e[1;32mEnable Systemd process Complete!\e[0m\n"

else
    printf "\e[1;31mEnable Systemd process is Failed!\e[0m\n"

fi