import ast
import socket
from time import sleep, time
from threading import Thread, Lock
from config import clients, cluster
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
        self.server_identifiers = ['A', 'B', 'C', 'D', 'E']
        self.identifiers = ['a', 'b', 'c', 'd', 'e']
        self.server_addrs = {}
        self.server_socks = {}
        self.client_addrs = {}
        self.client_socks = {}

        for identifier in self.server_identifiers:
            self.server_addrs[identifier] = cluster[identifier]
            self.server_socks[identifier] = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        for identifier in self.identifiers:
            self.client_addrs[identifier] = clients[identifier]
            self.client_socks[identifier] = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.client_socks[identifier].bind(self.client_addrs[identifier])


    def send_msg(self, data, identifier):
        identifier = identifier.upper()
        msg = bytes(data, encoding="ascii")
        self.server_socks[identifier].sendto(msg, self.server_addrs[identifier])
        print("{} sent to {}".format(msg, self.server_addrs[identifier]))

    def process_user_input(self, user_input, identifier):
        words = user_input.split(" ")
        command = words[0]
        if len(words) > 1:
            arg = words[1]

        milliseconds = time() * 1000

        if command == "show" or command == "random":
            self.send_msg("{},{},{},{}".format(command,  self.s[identifier][0], self.client_addrs[identifier][1], str(milliseconds)), identifier)
        elif command == "buy" and arg.isdigit():
            self.send_msg("{},{},{},{},{}".format(command, arg, self.client_addrs[identifier][0], self.client_addrs[identifier][1], str(milliseconds)), identifier)
        elif command == "change":
            # Kill listen_thread before changing server_sock
            self.server_sock.close()

            for client_sock in self.client_socks:
                client_sock.close()

            self.socket_setup()
        else:
            print("Couldn't recognize the command", user_input)
    
    def save_measurement_to_files(self, milliseconds_send, milliseconds_rcvd, identifier):
        global prev_time
        global count_tput
        global latencies
        THROUGHPUT_EVERY_MILLISECONDS = 5000
        LATENCY_EVERY_MILLISECONDS = 1000


        latency = abs(float(milliseconds_rcvd) - float(milliseconds_send))

        self.lock.acquire()
        count_tput += 1
        latencies.append(latency)
        self.lock.release()


        if milliseconds_send - prev_time > THROUGHPUT_EVERY_MILLISECONDS and identifier == 'a':
            median_lat = round(median(latencies), 1)

            with open('throughput_latency.txt', 'a+') as tput_file:
                tput_file.write(str(count_tput/5.0) + ' ' + str(median_lat) + '\n')
            prev_time = milliseconds_send
            latencies = []
            count_tput = 0

    def record_measurements(self, msg, milliseconds_rcvd, identifier):
        if msg[0].isdigit():
            msg_list = ast.literal_eval(msg)
            for line in msg_list:
                print(line)
            milliseconds_send = float(msg_list[-1])
        else:
            milliseconds_send = float(msg.split(",")[-1])

        self.save_measurement_to_files(milliseconds_send, milliseconds_rcvd, identifier)

    def listen(self, identifier):
        while True:
            data, _ = self.client_socks[identifier].recvfrom(BUFFER_SIZE)
            msg = data.decode("utf-8")
            print(msg)

            milliseconds_rcvd = time() * 1000
            self.record_measurements(msg, milliseconds_rcvd, identifier)

    def msg_load(self, identifier):
        msg_per_sec = 0.2
        msg_count = 0
        rate_interval = 5000
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
                    self.process_user_input(msg_data, identifier)
                else:
                    if msg_per_sec < 100:
                        msg_per_sec += 0.2

                    break

    def thread_setup(self):
        self.lock = Lock()

        msg_threads = {}
        listen_threads = {}

        for identifier in self.identifiers:
            msg_threads[identifier] = Thread(target=self.msg_load, args=(identifier, ))
            msg_threads[identifier].start()

            listen_threads[identifier] = Thread(target=self.listen, args=(identifier, ))
            listen_threads[identifier].start()

def run():
    Client()

if __name__ == "__main__":
    with open('throughput_latency.txt', 'w') as tput_file:
        tput_file.write("")
    run()
