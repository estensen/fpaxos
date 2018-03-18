

# FPaxos &middot; [![Maintainability](https://api.codeclimate.com/v1/badges/bc2bd87850c319277c5f/maintainability)](https://codeclimate.com/github/estensen/fpaxos/maintainability)

A (naive) implementation of Flexible Paxos made to test throughput and latency at leader failure

# Getting Started
## Prerequisites
- Python 3
- pip3

## Installing
```
pip3 install -r requirements.txt
```

## Setup
Paxos is here configured to run with 5 nodes locally
If you want to run it in the cloud change the IP addresses in `config.py`

Run `python main.py` in 5 separate terminal windows and us a unique identifier (A-E) for each window

Run `python client.py` in another terminal window. It will connect to all the nodes and send an increasingly amount of messages.
