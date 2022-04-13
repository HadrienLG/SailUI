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

# Installation des paquets systèmes de base
echo "Installation des paquets nécessaires"
sudo apt-get install python3 gpsd gpsd-clients pps-tools ntp mosquitto -y

# Configuration du récepteur GPS Waveshare Ublox M8Q
export UBXOPTS="-P 18 -v 2"
sudo sed -i 's/USBAUTO="true"/USBAUTO="false"/g' /etc/default/gpsd # GPSD is the program used to receive the GPS data. By default, it looks for a USB based GPS module. Since ours is not USB, we disable this to speed things up.
sudo sed -i 's:DEVICES="":DEVICES="/dev/ttyAMA0 /dev/pps0":g' /etc/default/gpsd # we want to use ttyAMA0 to deliver the GPS data
sudo sed -i 's:GPSD_OPTIONS="":GPSD_OPTIONS="-n":g' /etc/default/gpsd # Setting GPSD Options to -n ensure the GPS Daemon continues to run even if no application is using it.
sudo systemctl enable gpsd

sudo echo dtoverlay=pps-gpio,gpiopin=18 >> /boot/config.txt # Configuration du PIN PPS, voir documentation Waveshare M8Q https://www.waveshare.com/product/raspberry-pi/hats/max-m8q-gnss-hat.htm
sudo echo pps-gpio >> /etc/modules # Ajout du module PPS-GPIO au démarrage

# Clonage du dépôt Github SailUI
echo "Clonage du code source depuis Github"
cd ~
git clone https://github.com/HadrienLG/SailUI.git

# Installation des dépendances python
echo "Installation des dépendances python"
sudo pip install pip --upgrade # Mise à jour de pip pour commencer
cd 'SailUI\server'
sudo pip install -r requirements.txt

# Installation de RaspAP 
curl -sL https://install.raspap.com | bash -s -- --yes

# Installation de Telegraf & InfluxDB (code frome doc.influxdata.com)
wget -qO- https://repos.influxdata.com/influxdb.key | gpg --dearmor | sudo tee /etc/apt/trusted.gpg.d/influxdb.gpg > /dev/null
export DISTRIB_ID=$(lsb_release -si); export DISTRIB_CODENAME=$(lsb_release -sc)
echo "deb [signed-by=/etc/apt/trusted.gpg.d/influxdb.gpg] https://repos.influxdata.com/${DISTRIB_ID,,} ${DISTRIB_CODENAME} stable" | sudo tee /etc/apt/sources.list.d/influxdb.list > /dev/null
sudo apt-get update && sudo apt-get install influxdb2
sudo service influxdb start

wget https://dl.influxdata.com/telegraf/releases/telegraf_1.22.1-1_amd64.deb
sudo dpkg -i telegraf_1.22.1-1_amd64.deb


# wget -qO- https://repos.influxdata.com/influxdb.key | sudo tee /etc/apt/trusted.gpg.d/influxdb.asc >/dev/null
# source /etc/os-release
# echo "deb https://repos.influxdata.com/${ID} ${VERSION_CODENAME} stable" | sudo tee /etc/apt/sources.list.d/influxdb.list
# sudo apt-get update && sudo apt-get install telegraf influxdb
# sudo systemctl unmask influxdb
# sudo systemctl enable influxdb
# sudo systemctl start influxdb

# Lancement des services systemd
# fichier='/etc/systemd/system/SAILui_server.service'
