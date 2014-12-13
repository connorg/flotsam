#!/usr/bin/env bash

echo "Getting pip installer script and running it."
wget https://bootstrap.pypa.io/get-pip.py -O /tmp/get-pip.py
python /tmp/get-pip.py
