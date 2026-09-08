#!/bin/sh

set -eu

echo "postStartCommand.sh"
echo "-------------------"

sudo apt-get update
sudo apt-get upgrade -y

python --version
uv --version
kubectl version --client --output=yaml | head -2

echo "Done"
