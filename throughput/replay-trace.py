#!/usr/bin/env python3
from pprint import pprint

from pyzil.zilliqa.api import ZilliqaAPI, APIError
from pyzil.zilliqa import chain
from pyzil.account import Account
import json
import sys
import datetime
import math
from concurrent import futures
from concurrent.futures import ProcessPoolExecutor

API_ENDPOINT = "http://localhost:4201"

LocalNet = chain.BlockChain(API_ENDPOINT, version=1, network_id=0)
chain.set_active_chain(LocalNet)

MAX_NUM_WORKERS = 100
TARGET_BUCKET_SIZE = 1000
GET_CHAIN_NONCE = False

nonces = {}

def partition(list, num_buckets):
    part = {}
    for b in range(num_buckets):
        part[b] = []

    for i, val in enumerate(list):
        part[i % num_buckets].append(val)

    return part

def submit_chunk(tx_list, chunk_id=0):
    api = ZilliqaAPI(API_ENDPOINT)
    start = datetime.datetime.now()
    num_txs = 0

    print_interval = int(0.1 * len(tx_list))
    for i, tx in enumerate(tx_list):
        try:
            txn_info = api.CreateTransaction(tx)
            print(txn_info)
            num_txs += 1
        # Within a ProcessPool, we can print the exception, but not raise it to parent
        except Exception as e:
            print("Exception from lookup: {}".format(e))

        if i % print_interval == 0:
            td = datetime.datetime.now() - start
            print("Chunk {}: replayed {} transactions in {} => {:.2f} TPS".format(chunk_id, num_txs, td, num_txs/td.total_seconds()), file=sys.stderr)
            start = datetime.datetime.now()
            num_txs = 0

def get_chain_nonce(sender_pubkey):
    acc = Account(public_key=sender_pubkey)
    return acc.get_nonce()

def new_nonce(sender_id):
    sender_id = str(sender_id)
    # Python has eager evaluation; don't want nonces.get(sender_id, get_chain_nonce(sender_id))!
    nn = nonces.get(sender_id, -1) + 1
    if nn == 0:
        nn = get_chain_nonce(sender_id) + 1 if GET_CHAIN_NONCE else 1
    nonces[sender_id] = nn
    return nn

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Provide path to at least one input file!", file=sys.stderr)

    txs = []

    # Process input
    num_args = len(sys.argv)
    for idx in range(1, num_args):
        with open(sys.argv[idx], 'r') as tf:
            # Readjust nonces if getting multiple files as input
            for line in tf:
                try:
                    tx = json.loads(line)
                    sender_id = tx["pubKey"]
                    tx["nonce"] = new_nonce(sender_id)
                    txs.append(tx)
                except Exception as e:
                    print("Failed to parse transaction {}: {}".format(line, e))

    # Send transactions
    num_txs = len(txs)
    print("Loaded {} transactions".format(num_txs))
    # num_workers = min(math.ceil(num_txs / TARGET_BUCKET_SIZE), MAX_NUM_WORKERS)
    num_workers = MAX_NUM_WORKERS
    part = partition(txs, num_workers)

    start = datetime.datetime.now()
    with ProcessPoolExecutor(max_workers=num_workers) as pool:
        all_tasks = [pool.submit(submit_chunk, part[chunk_id], chunk_id) for chunk_id in part.keys()]
        for future in futures.as_completed(all_tasks):
            pass

    end = datetime.datetime.now()
    td = end - start
    print("Replayed {} transactions in {} => {:.2f} TPS".format(num_txs, td, num_txs/td.total_seconds()), file=sys.stderr)
