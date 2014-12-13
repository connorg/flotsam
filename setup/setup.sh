#!/usr/bin/env bash

# partly borrowed from http://stackoverflow.com/questions/3231804
confirm () {
  # call with a prompt string or use a default
  read -r -p "$1 [Y/n] " response
  case $response in
    [yY][eE][sS]|[yY]|"")
    true
    ;;
    *)
    false
    ;;
  esac
}

cd ${0%/*}

echo "This script will help set up your computer for Flotsam."
echo "Ubuntu 14.04 is the recommended environment for Flotsam."
echo "You may wish to use a new virtual machine for Flotsam because Flotsam's"
echo "use of Docker means it requires root access."
echo
echo "Most of these setup steps require sudo/root privileges."
echo "** You should run this whole script using sudo. **"
echo
confirm "Install Docker from Docker-hosted repo?" && ./setup_docker.sh
echo
confirm "Install pip?" && ./setup_pip.sh
echo
confirm "Install required pip packages?" && ./setup_pip_deps.sh
echo
confirm "Install and configure dnsmasq?" && ./setup_dnsmasq.sh
echo
confirm "Generate SSH keys for lite-raft implementation?" && ./setup_literaft.sh
echo
confirm "Build Docker images for projects?" && ./setup_docker_images.sh ../run/docker/
echo
echo "Setup complete!"
