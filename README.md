# Multi-Paxos
Elect one kiosk as leader
When the leader is stable the system does not need to go through "prepare phase" and can run "accept phase" when the requests come.
Use heartbeats to confirm whether the leader is still alive.
Should handle configuration changes.
It is not required to handle causality between requests as long as the MUTEX problem is solved.

# User Interface
Starts with 3 datacenters
Configuration changes should add 2 more

Each datacenter has a client connected to it.

Client commands
1. buy numOfTickets tickets
2. show
	First line: State of state machine
	Following lines show committed logs
