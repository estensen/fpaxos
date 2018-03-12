#!/bin/bash
#Program to simulate network delay between nodes
#Currently includes delays corresponding to a network of the following 5 AWS
# datcenters: California, Oregon, Virginia, Ireland, Sao Paolo
# Run as follows: ./delay.sh <instance_number>


#Create IP Delay Tables
IP_list=( 128.111.84.146 128.111.84.157 128.111.84.160 128.111.84.161 128.111.84.165 )

let "instance_no = $1 - 1"

declare -A DTable
declare -a Delays
Delays=(1 22 65 136 185 22 1 88 125 182 65 88 1 73 121 136 125 73 1 185 185 182 121 185 1)

counter=0

for ((i=0;i<5;i++)) do
    for ((j=0;j<5;j++)) do
	DTable[$i,$j]=${Delays[$counter]}
	let "counter = $counter + 1"
    done
done

#Add Network emulators, and apply filters to specific IP addresses
Interface=ens3
sudo tc qdisc add dev $Interface root handle 1: htb
sudo tc class add dev $Interface parent 1: classid 1:1 htb rate 1000Mbps

for handle in {2..6}; do
    let "n = $handle - 2"
    delay=${DTable[$instance_no,$n]}
    variance=$(expr $delay / 5 + 1)
    sudo tc class add dev $Interface parent 1:1 classid 1:$handle htb rate 1000Mbps
    sudo tc qdisc add dev $Interface handle $handle: parent 1:$handle netem delay ${delay}ms ${variance}ms distribution normal 

    sudo tc filter add dev $Interface pref $handle protocol ip parent 1:0  u32 match ip dst ${IP_list[$n]} flowid 1:$handle

done