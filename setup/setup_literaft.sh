#!/usr/bin/env bash

echo "Generating and staging keys for lite-raft implementation"
ssh-keygen -f ../run/docker/lite-raft/ssh-dir/id_rsa -N ''
cp ../run/docker/lite-raft/ssh-dir/id_rsa.pub ../run/docker/lite-raft/ssh-dir/authorized_keys
