# Multi-Paxos
Elect one kiosk as leader
When the leader is stable the system does not need to go through "prepare phase" and can run "accept phase" when the requests come.
Use heartbeats to confirm whether the leader is still alive.
Should handle configuration changes.
It is not required to handle causality between requests as long as the MUTEX problem is solved.

# Getting Started
## Installing
```
brew install python
```

## Setup
Paxos is here configured to run with 5 nodes

Run `python main.py` in 5 separate terminal windows and us a unique identifier (A-E) for each window

Run `python client.py` in another terminal window and select the node you want to connect to

## Client commands
1. buy numOfTickets
2. show
	- First line: State of state machine
	- Following lines show committed logs
