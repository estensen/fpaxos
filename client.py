import ast
import socket
from time import sleep, time
from threading import Thread
from config import cluster

t_send_prv = time.time()
count_tput = 0
count_lat = 0
BUFFER_SIZE = 1024
threads = []

class Client:
    def __init__(self):
        self.socket_setup()
        self.thread_setup()

    def socket_setup(self):
        # TODO: Print identifiers in the cluster
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

        if command == "show":
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
    
   def stats(t_send):
	global ftime
        global t_send_prv
        global count_tput
        global count_lat
        if(t_send - t_send_prv > 1000):
       	    avg_lat = count_lat/float(count_tput)
            ftime=open('tput.txt','a+')
            ftime.write(str(count_tput) + "," + str(avg_lat))
            ftime.close()
            t_send_prv = t_send
            count_lat = 0;
            count_tput = 0;
	count_tput += 1
        t_rcvd = time.time() * 1000
        lat = abs(int(t_rcvd) - int(t_send)) 
        count_lat += lat
        ftime = open('latency.txt','a+')
        ftime.write(lat)
        ftime.close()
		
    def listen(self):
	while True:
            data, addr = self.client_sock.recvfrom(BUFFER_SIZE)
            msg = data.decode("utf-8")
	
            if msg[0].isdigit():
                msg_list = ast.literal_eval(msg)
                for line in msg_list:
                    print(line)
		t_send = msg_list[-1]
		stats(t_send)
            else:
		t_send = msg.split(",")[-1]
		stats(t_send)
                print(msg)

    def user_input(self):
        while True:
            user_input = input("Send msg to datacenter: ")
            self.process_user_input(user_input)

    def thread_setup(self):
        listen_thread = Thread(target=self.listen)
        threads.append(listen_thread)
        listen_thread.start()

        input_thread = Thread(target=self.user_input)
        threads.append(input_thread)
        input_thread.start()


def run():
    client = Client()

if __name__ == "__main__":
    run()
