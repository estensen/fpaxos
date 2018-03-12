#!/bin/bash

IF=ens3
for handle in {2..6}; do
 sudo tc filter del dev $IF pref $handle
 sudo tc qdisc del dev $IF handle $handle: parent 1:$handle netem delay 1000ms
done
sudo tc qdisc del dev $IF root

