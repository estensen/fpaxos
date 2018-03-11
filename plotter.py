import matplotlib
from random import randint

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def graph_plotter(filename):
    avg_tput = ""
    avg_lat = ""
    avg_tput_X = []
    avg_lat_X = []

    with open(filename, 'r') as f:
        for line in f:
            avg_tput, avg_lat = line.strip().split(" ")
            avg_tput_X.append(avg_tput)
            avg_lat_X.append(avg_lat)

    plt.figure(1)
    plt.subplot(211)
    plt.plot(avg_lat_X, "ro", avg_lat_X , "b--")
    plt.ylabel("Avg Latency (ms)")
    plt.xlabel("Time (sec)")

    plt.subplot(212)
    plt.plot(avg_tput_X, "g^", avg_tput_X ,'r--' )
    plt.ylabel("Avg Throughput (# msgs/sec)")
    plt.xlabel("Time (sec)")

    plt.subplots_adjust(hspace=0.5)

    plt.savefig("output.png")


def main():
    graph_plotter("throughput.txt")


if __name__ == "__main__":
    main()
