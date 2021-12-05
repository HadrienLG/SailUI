#!/bin/sh

# SailUI install script
echo "---------------------------"
echo "--- SAILUI INSTALLATION ---"
echo "---------------------------"
date

# Mise à jour du Raspberry Pi
echo "Mise à jour du raspberry"
sudo apt-get update -y
sudo apt-get dist-upgrade -y
sudo rpi-update -y

# Installation des paquets systèmes de base
echo "Installation des paquets nécessaires"
sudo apt-get install python3 gpsd gpsd-clients python-pip

# Installation de Telegraf & InfluxDB (code frome doc.influxdata.com)
# wget -qO- https://repos.influxdata.com/influxdb.key | sudo tee /etc/apt/trusted.gpg.d/influxdb.asc >/dev/null
# source /etc/os-release
# echo "deb https://repos.influxdata.com/${ID} ${VERSION_CODENAME} stable" | sudo tee /etc/apt/sources.list.d/influxdb.list
# sudo apt-get update && sudo apt-get install telegraf influxdb

# sudo systemctl unmask influxdb
# sudo systemctl enable influxdb
# sudo systemctl start influxdb

# Clonage du dépôt Github SailUI
echo "Clonage du code source depuis Github"
cd ~
git clone https://github.com/HadrienLG/SailUI.git

# Installation des dépendances python
echo "Installation des dépendances python"
sudo pip install pip --upgrade # Mise à jour de pip pour commencer
cd 'SailUI\server'
sudo pip install -r requirements.txt

# Lancement des services systemd
fichier='/etc/systemd/system/SAILui_server.service'

