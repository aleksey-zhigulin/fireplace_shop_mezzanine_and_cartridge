#!/usr/bin/env bash

apt-get update
apt-get -y install python-pip python-dev libjpeg-dev openjpeg-tools language-pack-ru
sudo update-locale LC_ALL=ru_RU.UTF-8
sudo pip install cartridge ReportLab==3.1.8 HTML5lib==0.999