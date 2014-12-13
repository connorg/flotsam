#!/usr/bin/env bash

echo "Installing libpython-dev, then installing pip packages."
apt-get update
apt-get install libpython-dev
pip install docker-py==0.6.0 requests netifaces
