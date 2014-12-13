#!/usr/bin/env bash

echo "Installing the latest Docker available from Docker's apt repositories"
echo "See https://docs.docker.com/installation/ubuntulinux/ for details"

apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys 36A1D7869245C8950F966E92D8576A8BA88D21E9
echo "deb https://get.docker.com/ubuntu docker main" > /etc/apt/sources.list.d/docker.list
apt-get update
apt-get install lxc-docker-1.3.3
