import socket
from threading import Thread
from config import cluster
from server import Server

BUFFER_SIZE = 1024
threads = []

def setup(Server):
    # Create socket to receive msgs from other datacenters
    print("Cluster", cluster)
    identifier = input("Pick an address (A, B or C): ")

    if identifier not in cluster:
        ip = input("IP: ")
        port = int(input("Port: "))
        server_addr = (ip, port)
    else:
        server_addr = cluster[identifier]

    server = Server(identifier, server_addr)
    return server


def run():
    server = setup(Server)


if __name__ == "__main__":
    run()
