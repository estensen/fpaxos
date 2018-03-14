import ast
import socket
from time import sleep, time
from threading import Thread
from config import cluster
from random import randint
from statistics import median

prev_time = time()
count_tput = 1
latencies = []
BUFFER_SIZE = 1024
threads = []

class Client:
    def __init__(self):
        self.socket_setup()
        self.thread_setup()

    def socket_setup(self):
        self.identifier = input("Which datacenter do you want to connect to? (A, B, C, D or E) ")

        if self.identifier not in cluster:
            ip = input("IP: ")
            port = int(input("Port: "))
            self.server_addr = (ip, port)
        else:
            self.server_addr = cluster[self.identifier]

        self.client_addr = (self.server_addr[0], self.server_addr[1] + 10)

        self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.client_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.client_sock.bind(self.client_addr)

    def send_msg(self, data):
        msg = bytes(data, encoding="ascii")
        self.server_sock.sendto(msg, self.server_addr)
        print("Message sent to", self.server_addr)

    def process_user_input(self, user_input):
        words = user_input.split(" ")
        command = words[0]
        if len(words) > 1:
            arg = words[1]

        milliseconds = time() * 1000

        if command == "show" or command == "random":
            self.send_msg("{},{},{}".format(command, str(self.client_addr[1]), str(milliseconds)))
        elif command == "buy" and arg.isdigit():
            self.send_msg("{},{},{},{}".format(command, arg, self.client_addr[1], str(milliseconds)))
        elif command == "change":
            # Kill listen_thread before changing server_sock
            self.server_sock.close()
            self.client_sock.close()
            self.socket_setup()
        else:
            print("Couldn't recognize the command", user_input)
    
    def save_measurement_to_files(self, milliseconds_send, milliseconds_rcvd):
        global prev_time
        global count_tput
        global latencies
        THROUGHPUT_EVERY_MILLISECONDS = 1000
        LATENCY_EVERY_MILLISECONDS = 1000

        count_tput += 1
        latency = abs(float(milliseconds_rcvd) - float(milliseconds_send))
        latencies.append(latency)

        if milliseconds_send - prev_time > THROUGHPUT_EVERY_MILLISECONDS:
            median_lat = round(median(latencies), 1)

            with open('throughput_latency.txt', 'a+') as tput_file:
                tput_file.write(str(count_tput) + ' ' + str(median_lat) + '\n')
            prev_time = milliseconds_send
            latencies = []
            count_tput = 0

    def record_measurements(self, msg, milliseconds_rcvd):
        if msg[0].isdigit():
            msg_list = ast.literal_eval(msg)
            for line in msg_list:
                print(line)
            milliseconds_send = float(msg_list[-1])
        else:
            milliseconds_send = float(msg.split(",")[-1])

        self.save_measurement_to_files(milliseconds_send, milliseconds_rcvd)

    def listen(self):
        while True:
            data, _ = self.client_sock.recvfrom(BUFFER_SIZE)
            msg = data.decode("utf-8")
            print(msg)

            milliseconds_rcvd = time() * 1000
            self.record_measurements(msg, milliseconds_rcvd)

    def msg_load(self):
        msg_per_sec = 1
        msg_count = 0
        rate_interval = 1000
        while True:
            interval_time_start = time() * 1000
            while True:
                interval_time_current = time() * 1000

                if interval_time_current - interval_time_start < rate_interval:
                    sleep_time = 1 / float(msg_per_sec)
                    sleep(sleep_time)

                    msg_count += 1
                    num_tickets = randint(1, 100)
                    msg_data = ('buy ' + str(num_tickets))
                    self.process_user_input(msg_data)
                else:
                    if msg_per_sec < 100:
                        msg_per_sec += 0.1

                    break

    def thread_setup(self):
        msg_thread = Thread(target=self.msg_load)
        threads.append(msg_thread)
        msg_thread.start()
        
        listen_thread = Thread(target=self.listen)
        threads.append(listen_thread)
        listen_thread.start()

def run():
    Client()

if __name__ == "__main__":
    with open('throughput_latency.txt', 'w') as tput_file:
        tput_file.write("")
    run()
