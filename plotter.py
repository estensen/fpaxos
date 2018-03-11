import matplotlib
from random import randint

matplotlib.use('Agg')
import matplotlib.pyplot as plt


def graph_plotter():
    with open(filename, 'r') as file:
        line = ''
        avg_tput = ''
        avg_lat = ''
        avg_tput_X = []
        avg_lat_X = []
        for line in f:
            avg_tput,avg_lat = line.strip().split(' ')
            avg_tput_X.append(avg_tput)
            avg_lat_X.append(avg_lat)
            print(avg_tput_X,avg_lat_X)
        f.close()

        plot.figure(1)
        plt.subplot(211)
        plt.plot(avg_lat_X , 'ro' , avg_lat_X , 'b--')
        plot.ylabel('Average Latency(ms)')

        plt.subplot(212)
        plt.plot(avg_tput_X , 'g^' , avg_tput_X ,'r--' )
        plot.ylabel('Average Throughput(# messages/sec)')

        plt.savefig("output.png")


def main():
    graph_plotter("my_tput.txt")


if __name__ == '__main__':
    main()
