#!/usr/bin/env bash

echo "Installing dnsmasq and configuring to use /opt/flostam/dnsmasq.d as its"
echo "configuration dir."
apt-get update
apt-get install dnsmasq
if [ $(grep -c "conf-dir=/opt/flotsam/dnsmasq.d" /etc/dnsmasq.conf) -eq 0 ]; then
  echo "conf-dir=/opt/flotsam/dnsmasq.d" >> /etc/dnsmasq.conf
fi
mkdir -p /opt/flotsam/dnsmasq.d/
service dnsmasq restart
