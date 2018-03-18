import os
import socket
import ast
from threading import Thread
from random import choice, random
from math import ceil
from queue import Queue
from time import sleep, time
from config import cluster

BUFFER_SIZE = 1024
threads = []

HEARTBEAT_FREQ = 0.4
heartbeat_delta = HEARTBEAT_FREQ * 2 + random() * 3

class Server:
    def __init__(self, identifier, server_addr):
        self.uid = server_addr[1]
        self.leader = False
        self.leader_queue = Queue()
        self.last_recv_heartbeat = None
        self.identifier = identifier
        self.server_addr = server_addr
        self.cluster = cluster
        # Quorum sizes are hardcoded for now to expect 5 nodes
        self.quorum1_size = 4
        self.quorum2_size = 2

        self.init_tickets_available = 1000000000
        self.tickets_available = self.init_tickets_available
        self.client_requests = None

        self.proposal_id = (0, 0)
        self.proposal_val = None
        self.next_proposal_num = 1
        self.last_accepted_num = 0
        self.last_accepted_proposer_id = 0
        self.last_accepted_val = None
        self.promised_id = (0, 0)

        self.log = []
        self.filename = self.identifier + ".txt"
        self.setup()

    def set_proposal(self, val):
        if self.proposal_val == None:
            self.proposal_val = val

    def send_prepare(self):
        self.proposal_id = (self.next_proposal_num, self.uid)
        self.next_proposal_num += 1
        self.recv_promises_uid = set()
        proposal_num = self.proposal_id[0]
        proposal_id = self.proposal_id[1]
        data = "prepare,{},{}".format(proposal_num, proposal_id)
        self.send_data_to_all(data)

    def recv_prepare(self, addr, msg_list):
        proposal_num, proposer_id = msg_list[1:]
        proposal_id = (int(proposal_num), int(proposer_id))
        if proposal_id >= self.promised_id:
            self.promised_id = proposal_id

            promise_msg = "promise,{},{},{},{},{},{}".format(
                proposal_num,
                proposer_id,
                self.uid,
                self.last_accepted_num,
                self.last_accepted_proposer_id,
                self.last_accepted_val
            )

            self.send_data(promise_msg, addr)
            print("Returned promise")

    def recv_promise(self, msg_list):
        proposal_num, proposer_id, from_uid, last_accepted_num, \
        last_accepted_proposer_id, last_accepted_val = msg_list[1:]

        if self.proposal_id < (int(last_accepted_num), int(last_accepted_proposer_id)):
            self.proposal_val = last_accepted_val

        self.recv_promises_uid.add(from_uid)
        if not self.leader:
            if len(self.recv_promises_uid) >= self.quorum1_size:
                self.recv_promises_uid = set()
                self.send_accepts()

    def send_accepts(self):
        self.recv_accepted_uid = set()
        data = "accept,{},{},{},{}".format(self.proposal_id[0], self.proposal_id[1], self.proposal_val, len(self.log))
        self.send_data_to_all(data)

    def recv_accept(self, addr, msg_list):
        proposal_num, proposer_id, proposal_val, leader_log_len = msg_list[1:]
        proposal_id = (int(proposal_num), int(proposer_id))

        log_diff = int(leader_log_len) - len(self.log)
        print("log_diff", log_diff)
        if log_diff > 0:
            self.request_missing_bytes(int(leader_log_len))

        elif proposal_id >= self.promised_id:
            self.last_accepted_num = proposal_num
            self.last_accepted_proposer_id = proposer_id
            self.last_accepted_val = proposal_val

            self.send_accept(addr)

    def send_accept(self, addr):
        accepted_data = "accepted,{},{},{},{}".format(self.last_accepted_num, \
            self.last_accepted_proposer_id, self.uid, self.last_accepted_val)
        to_addr = (addr[0], int(self.last_accepted_proposer_id))
        self.send_data(accepted_data, to_addr)

    def recv_accepted(self, msg_list):
        proposal_num, proposer_id, from_uid, proposal_val = msg_list[1:]
        self.recv_accepted_uid.add(from_uid)

        if len(self.recv_accepted_uid) >= self.quorum2_size:
            self.recv_accepted_uid = set()
            if not self.leader:
                self.leader = True
                self.send_data_to_all("heartbeat")
                print("###I am leader###")
            self.send_learn()

    def send_learn(self):
        proposal_num = self.proposal_id[0]
        proposal_id = self.proposal_id[1]
        data = "learn,{},{},{}".format(proposal_num, proposal_id, self.proposal_val)
        self.proposal_val = None
        self.send_data_to_all(data)

    def validate_transaction(self, addr, msg_list):
        # Compare log length
        tickets = msg_list[2]
        if tickets.isdigit():
            tickets = int(tickets)
            new_ticket_balance = self.tickets_available - tickets
            if new_ticket_balance >= 0:
                self.tickets_available = new_ticket_balance
                print(str(self.tickets_available) + " left")
                self.log.append(msg_list)
                self.write_to_persistent_storage(msg_list)
            if addr:
                self.send_client_response(addr, tickets, new_ticket_balance)

    def request_missing_bytes(self, leader_log_len):
        from_index = len(self.log)
        to_index = leader_log_len
        data = "missing,{},{},{}".format(from_index, to_index, self.uid)
        self.send_data_to_others(data)

    def send_log(self, addr, msg_list):
        print("Send log to resync node")
        if self.leader:
            from_index = int(msg_list[1])
            to_index = int(msg_list[2])
            from_uid = int(msg_list[3])
            # If log isn't synced the node wants all the log from from_index
            # Maybe refuse commit item and get that item from the log sync instead?
            log_str = ",".join(map(str, self.log[from_index:]))
            print("Send log to resync node")
            print("Log", log_str)
            data = "log," + log_str
            addr = (addr[0], from_uid)
            self.send_data(data, addr)

    def sync_log(self, msg):
        print("Sync log")
        log_index_start = msg.index("[")
        log_elements = msg[log_index_start:]
        log_list = ast.literal_eval(log_elements)

        for el in log_list:
            print("el", el)
            self.validate_transaction(None, el)

    def recv_buy(self, msg, from_uid):
        msg_list = msg.split(",")

        if self.leader:
            print("Will buy")
            self.leader_queue.put(msg_list)
            self.pop_leader_queue()
        else:
            if msg_list[-1] != "redirected" and from_uid not in self.get_server_uids():
                msg += ",redirected"
                self.send_data_to_others(msg)
                print("Have to relay to leader")

    def recv_show(self, addr, msg_list):
        addr = (addr[0], int(msg_list[1]))
        milliseconds = msg_list[2]
        if not self.log:
            log_str = "no transactions"
        else:
            log_str = str(self.tickets_available) + "," + ",".join(map(str, self.log))
        data = log_str + "," + milliseconds
        self.send_data(data, addr)

    def recv_random(self, addr, msg_list):
        addr = (addr[0], int(msg_list[1]))
        milliseconds = msg_list[2]
        random_transaction = "no transactions" if not self.log else str(choice(self.log))
        data = random_transaction + "," + milliseconds
        self.send_data(data, addr)

    def send_data(self, data, addr):
        msg = bytes(data, encoding="ascii")
        self.sock.sendto(msg, addr)
        if data[:9] != "heartbeat":
            print("Message {} sent to {}".format(data, addr))

    def send_data_to_all(self, data):
        for _, addr in self.cluster.items():
            self.send_data(data, addr)

    def send_data_to_others(self, data):
        for _, addr in self.cluster.items():
            if addr != self.server_addr:
                self.send_data(data, addr)

    def send_client_response(self, addr, tickets, new_ticket_balance):
        tickets = str(tickets)

        if self.client_requests and self.client_requests[1] == tickets:
            ip = self.client_requests[2]
            port = int(self.client_requests[3])
            addr = (ip, port)

            milliseconds = self.client_requests[4]

            if new_ticket_balance >= 0:
                data = "Here's your " + tickets + " ticket(s)," + milliseconds
            else:
                data = "Could not buy " + self.client_requests[1] + " ticket(s)"
            self.send_data(data, addr)
            self.client_requests = None
            self.pop_leader_queue()

    def pop_leader_queue(self):
        if not self.leader_queue.empty() and not self.client_requests:
            msg_list = self.leader_queue.get()
            self.client_requests = msg_list
            amount = msg_list[1]
            self.proposal_val = amount
            self.send_accepts()

    def send_add_node(self):
        msg = "node,{},{},{}".format(self.identifier, self.server_addr[0], self.uid)
        self.send_data_to_others(msg)
        print("Try to join cluster")

    def get_server_uids(self):
        uids = []
        for identifier, addr in self.cluster.items():
            uids.append(addr[1])
        return uids

    def listen(self):
        print("Listening")
        while True:
            data, addr = self.sock.recvfrom(BUFFER_SIZE)
            msg = data.decode("utf-8")

            msg_list = msg.split(",")
            command = msg_list[0]

            if command != "heartbeat":
                print("Received {} from {}".format(msg, addr))
                print("msg_list", msg_list)

            # Client commands
            if command == "buy":
                uid = addr[1]
                self.recv_buy(msg, uid)
            elif command == "show":
                self.recv_show(addr, msg_list)
            elif command == "random":
                self.recv_random(addr, msg_list)

            # Phase 1
            elif command == "prepare":
                self.recv_prepare(addr, msg_list)
            elif command == "promise":
                self.recv_promise(msg_list)

            # Phase 2
            elif command == "accept":
                self.recv_accept(addr, msg_list)
            elif command == "accepted":
                self.recv_accepted(msg_list)

            # Phase 3
            elif command == "learn":
                self.validate_transaction(addr, msg_list[1:])

            elif command == "missing":
                self.send_log(addr, msg_list)

            elif command == "log":
                self.sync_log(msg)

            elif command == "heartbeat":
                self.last_recv_heartbeat = time()
            else:
                print("Message command {} not recognized".format(command))

    def heartbeat(self):
        while True:
            if self.leader:
                self.last_recv_heartbeat = time()
                self.send_data_to_all("heartbeat")
            sleep(HEARTBEAT_FREQ)

    def listen_for_heartbeats(self):
        while True:
            sleep(heartbeat_delta)
            if not self.leader:
                if self.last_recv_heartbeat == None:
                    self.send_prepare()
                    self.last_recv_heartbeat = time()
                delta = time() - self.last_recv_heartbeat
                if delta > heartbeat_delta:
                    self.send_prepare()

    def load_log_from_persistent_storage(self):
        if os.path.isfile(self.filename):
            with open(self.filename, 'r') as persistent_log:
                for line in persistent_log:
                    line_list = ast.literal_eval(line)
                    print(line_list)
                    if line_list[0].isdigit():
                        tickets_sold = int(line_list[2])
                        self.tickets_available -= tickets_sold
                        self.log.append(line_list)
                print("Recovered log from persistent storage")
                print("Log", self.log)
        else:
            with open(self.filename, 'w') as persistent_log:
                persistent_log.write("")

    def write_to_persistent_storage(self, log_item):
        with open(self.filename, 'a') as persistent_log:
            line = str(log_item) + '\n'
            persistent_log.write(line)

    def setup(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(self.server_addr)
        print("Server socket created")
        print("Server addr:", self.server_addr)

        self.load_log_from_persistent_storage()

        listen_thread = Thread(target=self.listen)
        threads.append(listen_thread)
        listen_thread.start()

        heartbeat_thread = Thread(target=self.heartbeat)
        threads.append(heartbeat_thread)
        heartbeat_thread.start()

        listen_heartbeats_thread = Thread(target=self.listen_for_heartbeats)
        threads.append(listen_heartbeats_thread)
        listen_heartbeats_thread.start()

        if self.identifier not in self.cluster:
            self.send_add_node()
