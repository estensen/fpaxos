#!/bin/bash
apt-get update
sudo apt install python3-pip -y
pip3 install -r requirements.txt
echo 'Ready to run FPaxos'
