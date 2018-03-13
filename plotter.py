import matplotlib
from random import randint

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def graph_plotter(filename): #, filename2):
    avg_tput = ""
    avg_lat = ""
    avg_tput_X = []
    avg_lat_X = []
    avg_tput_M = []	#mulitpaxos
    avg_lat_M = []	#multipaxos
    with open(filename, 'r') as f:
        for line in f:
            avg_tput, avg_lat = line.strip().split(" ")
            avg_tput_X.append(avg_tput)
            avg_lat_X.append(avg_lat)

## Multipaxos
#    with open(filename2, 'r') as f2:
#	for line in f2:
#	    avg_tput, avg_lat = line.strip().split(" ")
#	    avg_tput_M.append(avg_tput)
#	    avg_lat_M.append(avg_lat)

    plt.figure(1)
    plt.subplot(211)
    plt.plot(avg_tput_X, avg_lat_X,'ro')
    plt.plot(avg_tput_X, avg_lat_X,'g')

##Multipaxos
#    plt.plot(avg_lat_M, avg_tput_M , 'b^')
#    plt.plot(avg_lat_M, avg_tput_M , 'r')

    plt.ylabel("Avg Latency (ms)")
    plt.xlabel("Throughput (#msgs/sec)")

    plt.subplot(212)
    plt.plot(avg_tput_X, "g^", avg_tput_X ,'r--' )
    plt.ylabel("Avg Throughput (# msgs/sec)")
    plt.xlabel("Time (sec)")

    plt.subplots_adjust(hspace=0.5)

    plt.savefig("output.png")


def main():
    graph_plotter("throughput_latency.txt")


if __name__ == "__main__":
    main()
