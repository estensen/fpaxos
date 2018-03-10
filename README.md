# FPaxos
An implementation of Flexible Paxos made to test throughput and latency at leader failure

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
