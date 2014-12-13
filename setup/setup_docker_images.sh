#!/usr/bin/env bash

DOCKER_DIR="$1"
for d in $(ls $DOCKER_DIR); do
  echo "Building Docker image for $d"
  docker build -t $d $DOCKER_DIR/$d/
done
