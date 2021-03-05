#!/usr/bin/env python3
from pprint import pprint
from pyzil.zilliqa import chain
from pyzil.zilliqa.api import ZilliqaAPI, APIError
from collections import Counter

API_ENDPOINT = "http://localhost:4201"

LocalNet = chain.BlockChain(API_ENDPOINT, version=0, network_id=0)
chain.set_active_chain(LocalNet)
api = ZilliqaAPI(API_ENDPOINT)

PENDING_FILE = "pending.txt"

def pp_blockchaininfo():
    print("---")
    info = api.GetBlockchainInfo()
    pprint(info)
    print("---")

def pp_gettxblock():
    print("---")
    info = api.GetLatestTxBlock()
    pprint(info)
    print("---")

def pp_getpending():
    c = Counter()
    conf = Counter()
    with open(PENDING_FILE, 'r') as f:
        for line in f:
            h = line.strip()
            r = api.GetPendingTxn(h)
            # if r["confirmed"] == False and r["code"] == 0:
            #     print(h, r)
            c.update([r["info"]])
            conf.update([r["confirmed"]])
    pprint(c)
    pprint(conf)

if __name__ == "__main__":
    pp_blockchaininfo()
    # pp_gettxblock()
    # pp_getpending()