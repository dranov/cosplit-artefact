#!/usr/bin/env python3
from pprint import pprint

from pyzil.crypto import zilkey
from pyzil.zilliqa import chain
from pyzil.zilliqa.units import Zil, Qa
from pyzil.account import Account, BatchTransfer
from pyzil.contract import Contract
from pyzil.zilliqa.api import ZilliqaAPI, APIError
import json
import os.path
import random
import time, datetime
import math
import sys
from collections import Counter
from subprocess import Popen, PIPE
from copy import copy
from concurrent import futures
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import hashlib

API_ENDPOINT = "http://localhost:4201"
ZILLIQA_PATH = "/home/pldi21/Zilliqa"
CONFIG_FILE = "config.json"

WAIT_TIME = 10
WAIT_BLOCKS = 4

BUILD_PATH = os.path.join(ZILLIQA_PATH, 'build/')
BIN_PATH = os.path.join(BUILD_PATH, 'bin/')
CONTRACTS_PATH = "contracts/"
ACCOUNTS_FILE = "accounts.csv"
PENDING_FILE = "pending.txt"

NUM_ACCOUNTS = 25000
ACC_BATCH_SIZE = 1000
TX_TIMEOUT = 300

ACC_MIN_BALANCE = 1000
TOKEN_MIN_BALANCE = 1000000

LocalNet = chain.BlockChain(API_ENDPOINT, version=1, network_id=0)
chain.set_active_chain(LocalNet)
api = ZilliqaAPI(API_ENDPOINT)

saved_accs = []
nonces = {}
sent_by = {}

with open(CONFIG_FILE) as f:
    conf = json.load(f)

genesis = Account(private_key=conf['genesis']['privkey'])

def new_nonce(acc):
    addr = acc.bech32_address
    nn = nonces.get(addr, acc.get_nonce()) + 1
    nonces[addr] = nn
    return nn

def assign_nonce(acc, nonce):
    addr = acc.bech32_address
    nonces[addr] = nonce

def sync_nonce_to_blockchain(acc):
    addr = acc.bech32_address
    nonces[addr] = acc.get_nonce()

def register_send(acc, txn_info):
    if txn_info is not None:
        tran_id = txn_info["TranID"]
        sent_by[tran_id] = acc

def gen_account():
    try:
        gen_account.counter += 1
    except AttributeError:
        gen_account.counter = 1

    if gen_account.counter % ACC_BATCH_SIZE == 0:
        print("Account #{}".format(gen_account.counter))

    # Populate pregen_accs if it is empty
    if len(saved_accs) == 0:
        i = 0
        with open(ACCOUNTS_FILE, 'r') as af:
            for line in af:
                pub, priv, _ = tuple(line.split(','))
                saved_accs.append((pub, priv))

    # Don't generate a new keypair if we already have enough in accounts file
    if gen_account.counter < len(saved_accs):
        pub, priv = saved_accs[gen_account.counter]
        return Account(public_key=pub, private_key=priv)
    else:
        process = Popen([os.path.join(BUILD_PATH, "tests/Zilliqa/genkeypair")], stdout=PIPE, universal_newlines=True)
        (output, _) = process.communicate()
        _ = process.wait()
        pub, priv = output.strip().split(' ')
        acc = Account(public_key=pub, private_key=priv)
        with open(ACCOUNTS_FILE, "a") as af:
            af.write("{},{},{}\n".format(pub, priv, acc.address))
        return acc

def wait_txn_confirm(txn_id, max_block, timeout=TX_TIMEOUT, sleep=5):
    start = time.time()
    this_block = int(api.GetBlockchainInfo()["CurrentMiniEpoch"])
    while (time.time() - start <= timeout) and (this_block <= max_block):
        this_block = int(api.GetBlockchainInfo()["CurrentMiniEpoch"])
        try:
            return api.GetTransaction(txn_id)
        except APIError as e:
            time.sleep(sleep)
    return None

def get_sharding(txn_info_list):
    ss = api.GetBlockchainInfo()["ShardingStructure"]
    num_shards = 0
    c = Counter()

    if len(txn_info_list) > 0:
        txn_info = txn_info_list[-1]
        num_shards = txn_info["num_shards"]

    for txn_info in txn_info_list:
        c.update([txn_info["proc_shard"]])

    return (ss, c)

def wait_for_txs(txn_info_list):
    num = len(txn_info_list)

    with open(PENDING_FILE, 'w') as f:
        for tx in txn_info_list:
            f.write("{}\n".format(tx["TranID"]))

    tx_block = int(api.GetBlockchainInfo()["CurrentMiniEpoch"])
    cutoff_block = tx_block + WAIT_BLOCKS
    print("Waiting to confirm {} transactions; cut-off block: {}".format(num, cutoff_block), flush=True)
    start = datetime.datetime.now()
    for txn_info in txn_info_list:
        wait_txn_confirm(txn_info["TranID"], cutoff_block)
    end = datetime.datetime.now()
    td = end - start

    not_confirmed = 0
    for txn_info in txn_info_list:
        txn_id = txn_info["TranID"]
        try:
            r = api.GetPendingTxn(txn_id)
            if bool(r["confirmed"]) == False:
                not_confirmed += 1
                sync_nonce_to_blockchain(sent_by[txn_id])
        except Exception as e:
            print("{}".format(e))

    pprint(get_sharding(txn_info_list))
    print("CONFIRMED {}/{} transactions in {}".format(num - not_confirmed, num, td), flush=True)

def deploy_contract(acc, file, init_params=[]):
    print("Deploying {} contract".format(file), flush=True)
    code = open(os.path.join(CONTRACTS_PATH, file)).read()
    contract = Contract.new_from_code(code)
    contract.account = acc
    txn_info = contract.deploy(timeout=TX_TIMEOUT, sleep=10, confirm=True,
        init_params=init_params, gas_limit=20000
    )
    print(json.dumps(acc.last_params), file=sys.stderr, flush=True)
    pprint(contract)
    return contract

def get_txn_map(from_accounts, to_accounts):
    txn_map = {}
    acc_map = {}
    from_accounts = random.sample(from_accounts, len(from_accounts))
    to_accounts = random.sample(to_accounts, len(to_accounts))
    for i, fa in enumerate(from_accounts):
        acc_map[i] = fa
        txn_map[fa] = []
    # Determine which from_account sends to which to_accounts
    for i, dest_acc in enumerate(to_accounts):
        src_idx = i % len(acc_map)
        src_acc = acc_map[src_idx]
        txn_map[src_acc].append(dest_acc)
    return txn_map

def iat_create_txns(src_acc, dest_accs, zils):
        # Clear any cached sessions. This is needed to ensure multiple processes
        # don't try to reuse the same TCP connection, which would lead to havoc
        LocalNet = chain.BlockChain(API_ENDPOINT, version=1, network_id=0)
        chain.set_active_chain(LocalNet)
        src_acc = Account(private_key=src_acc.private_key)

        txn_info_list = []
        src_addr = src_acc.bech32_address
        orig_nonce = nonces.get(src_addr, src_acc.get_nonce())
        for dest_acc in dest_accs:
            try:
                dest = dest_acc.bech32_address
                txn_info = src_acc.transfer(to_addr=dest, zils=zils, nonce=new_nonce(src_acc), gas_price=100)
                txn_info_list.append(txn_info)
                print(json.dumps(src_acc.last_params), file=sys.stderr)
                print("Created {} transactions".format(len(txn_info_list)))
            except Exception as e:
                print("Could not send from {} to {}: {}".format(src_addr, dest, e))

        nonce_now = nonces.get(src_addr, src_acc.get_nonce())
        # print("{}: created {} transactions; nonce went from {} to {}".format(src_acc.bech32_address, len(txn_info_list), orig_nonce, nonce_now))
        return txn_info_list, src_acc, nonce_now

def inter_account_transactions(from_accounts, to_accounts, zils, max_workers=8):
    assert len(from_accounts) > 0
    txn_map = get_txn_map(from_accounts, to_accounts)

    txn_info_list = []
    start = datetime.datetime.now()

    with ProcessPoolExecutor(max_workers=max_workers) as pool:
        all_tasks = [pool.submit(iat_create_txns, src_acc, txn_map[src_acc], zils) for src_acc in txn_map]

        for future in futures.as_completed(all_tasks):
            try:
                txns, src_acc, new_nonce = future.result()
                for tx in txns:
                    register_send(src_acc, tx)
                txn_info_list.extend(txns)
                assign_nonce(src_acc, new_nonce)
            except Exception as e:
                print("IAT Error: {}".format(e))

    end = datetime.datetime.now()
    td = end - start
    print("Produced {} transactions in {} => {:.2f} TPS".format(len(txn_info_list), td, len(txn_info_list)/td.total_seconds()), flush=True)
    return txn_info_list

def tiat_create_txns(contract, src_acc, dest_accs, amount):
        # Clear any cached sessions. This is needed to ensure multiple processes
        # don't try to reuse the same TCP connection, which would lead to havoc
        LocalNet = chain.BlockChain(API_ENDPOINT, version=1, network_id=0)
        chain.set_active_chain(LocalNet)
        src_acc = Account(private_key=src_acc.private_key)
        contract = Contract.load_from_address(contract.address, load_state=False)

        txn_info_list = []
        contract.account = src_acc
        src_addr = src_acc.bech32_address
        orig_nonce = nonces.get(src_addr, src_acc.get_nonce())
        for dest_acc in dest_accs:
            try:
                dest = dest_acc.address0x
                txn_info = contract.call(method="Transfer", params=[Contract.value_dict("to", "ByStr20", dest),
                        Contract.value_dict("tokens", "Uint128", str(amount))], nonce=new_nonce(src_acc), confirm=False)
                txn_info_list.append(txn_info)
                print(json.dumps(src_acc.last_params), file=sys.stderr)
                print("Created {} transactions".format(len(txn_info_list)))
            except Exception as e:
                print("Could not send from {} to {}: {}".format(src_acc.address0x, dest, e))
        nonce_now = nonces.get(src_addr, src_acc.get_nonce())
        # print("{}: created {} transactions; nonce went from {} to {}".format(src_acc.bech32_address, len(txn_info_list), orig_nonce, nonce_now))
        return txn_info_list, src_acc, nonce_now

def token_inter_account_transactions(contract, from_accounts, to_accounts, amount, max_workers=8):
    assert len(from_accounts) > 0
    txn_map = get_txn_map(from_accounts, to_accounts)

    txn_info_list = []
    start = datetime.datetime.now()

    with ProcessPoolExecutor(max_workers=max_workers) as pool:
        all_tasks = [pool.submit(tiat_create_txns, contract, src_acc, txn_map[src_acc], amount) for src_acc in txn_map]

        for future in futures.as_completed(all_tasks):
            try:
                txns, src_acc, new_nonce = future.result()
                for tx in txns:
                    register_send(src_acc, tx)
                txn_info_list.extend(txns)
                assign_nonce(src_acc, new_nonce)
            except Exception as e:
                print("Error: {}".format(e))

    end = datetime.datetime.now()
    td = end - start
    print("Produced {} transactions in {} => {:.2f} TPS".format(len(txn_info_list), td, len(txn_info_list)/td.total_seconds()), flush=True)
    return txn_info_list

def crowd_create_txns(contract, src_accs, amount):
        # Clear any cached sessions. This is needed to ensure multiple processes
        # don't try to reuse the same TCP connection, which would lead to havoc
        LocalNet = chain.BlockChain(API_ENDPOINT, version=1, network_id=0)
        chain.set_active_chain(LocalNet)
        contract = Contract.load_from_address(contract.address, load_state=False)

        txn_info_list = []
        for src_acc in src_accs:
            contract.account = src_acc
            src_addr = src_acc.bech32_address
            try:
                txn_info = contract.call(method="Donate", params=[], zils=amount, nonce=1, confirm=False)
                txn_info_list.append(txn_info)
                print(json.dumps(src_acc.last_params), file=sys.stderr)
                print("Created {} transactions".format(len(txn_info_list)))
            except Exception as e:
                print("Crowdfund exception: {}".format(e))
        # nonce_now = nonces.get(src_addr, src_acc.get_nonce())
        return txn_info_list, src_acc, None

def crowd_transactions(contract, src_accs, amount, max_workers=8):
    txn_info_list = []
    with ProcessPoolExecutor(max_workers=max_workers) as pool:
        all_tasks = [pool.submit(crowd_create_txns, contract, [ src_acc ], amount) for src_acc in src_accs]
        for future in futures.as_completed(all_tasks):
            try:
                txns, src_acc, new_nonce = future.result()
                for tx in txns:
                    register_send(src_acc, tx)
                txn_info_list.extend(txns)
                # assign_nonce(src_acc, new_nonce)
            except Exception as e:
                print("Error: {}".format(e))


def get_token_id(owner):
    return str(int(hashlib.md5(owner.encode('utf-8')).hexdigest(), 16))

def nft_create_txns(contract, src_acc, dest_accs, type='mint'):
        # Clear any cached sessions. This is needed to ensure multiple processes
        # don't try to reuse the same TCP connection, which would lead to havoc
        LocalNet = chain.BlockChain(API_ENDPOINT, version=1, network_id=0)
        chain.set_active_chain(LocalNet)
        src_acc = Account(private_key=src_acc.private_key)
        contract = Contract.load_from_address(contract.address, load_state=False)

        txn_info_list = []
        contract.account = src_acc
        src_addr = src_acc.bech32_address
        for dest_acc in dest_accs:
            try:
                src = src_acc.address0x
                dest = dest_acc.address0x
                txn_info = None
                if type == 'mint':
                    txn_info = contract.call(method="mint", params=[Contract.value_dict("to", "ByStr20", dest),
                            Contract.value_dict("tokenId", "Uint256", get_token_id(dest))], nonce=1, confirm=False)
                elif type == 'transfer':
                    txn_info = contract.call(method="transfer", params=[
                            Contract.value_dict("tokenOwner", "ByStr20", src),
                            Contract.value_dict("to", "ByStr20", dest),
                            Contract.value_dict("tokenId", "Uint256", get_token_id(src))], nonce=1, confirm=False)
                txn_info_list.append(txn_info)
                print(json.dumps(src_acc.last_params), file=sys.stderr)
                print("Created {} transactions".format(len(txn_info_list)))
            except Exception as e:
                print("Could not send from {} to {}: {}".format(src_acc.address0x, dest, e))
        return txn_info_list, src_acc, None

def nft_transactions(contract, from_accounts, to_accounts, type='mint', max_workers=8):
    assert len(from_accounts) > 0
    txn_map = get_txn_map(from_accounts, to_accounts)

    txn_info_list = []
    start = datetime.datetime.now()

    with ProcessPoolExecutor(max_workers=max_workers) as pool:
        all_tasks = [pool.submit(nft_create_txns, contract, src_acc, txn_map[src_acc], type) for src_acc in txn_map]

        for future in futures.as_completed(all_tasks):
            try:
                txns, src_acc, new_nonce = future.result()
                for tx in txns:
                    register_send(src_acc, tx)
                txn_info_list.extend(txns)
                # assign_nonce(src_acc, new_nonce)
            except Exception as e:
                print("Error: {}".format(e))

    end = datetime.datetime.now()
    td = end - start
    print("Produced {} transactions in {} => {:.2f} TPS".format(len(txn_info_list), td, len(txn_info_list)/td.total_seconds()), flush=True)
    return txn_info_list

def parentLabelToNode(parentNode, label):
    label_hash = hashlib.sha256(label.encode('utf-8')).hexdigest()
    parentNode = parentNode[2:]
    concat = bytes.fromhex(parentNode + label_hash)
    node = hashlib.sha256(concat).hexdigest()
    return '0x' + node

rootNode = "0x0000000000000000000000000000000000000000000000000000000000000000"

def contract_create_multidest_txns(contract, src_acc, dest_accs, method):
        # Clear any cached sessions. This is needed to ensure multiple processes
        # don't try to reuse the same TCP connection, which would lead to havoc
        LocalNet = chain.BlockChain(API_ENDPOINT, version=1, network_id=0)
        chain.set_active_chain(LocalNet)
        src_acc = Account(private_key=src_acc.private_key)
        contract = Contract.load_from_address(contract.address, load_state=False)

        txn_info_list = []
        contract.account = src_acc
        src_addr = src_acc.bech32_address
        for dest_acc in dest_accs:
            try:
                dest = dest_acc.address0x
                txn_info = None
                if method == 'bestow':
                    label = dest_acc.bech32_address
                    txn_info = contract.call(method="bestow", params=[
                        Contract.value_dict("node", "ByStr32", parentLabelToNode(rootNode, label)),
                        Contract.value_dict("label", "String", label),
                        Contract.value_dict("owner", "ByStr20", dest),
                        Contract.value_dict("resolver", "ByStr20", "0x0000000000000000000000000000000000000000")], nonce=1, confirm=False)
                txn_info_list.append(txn_info)
                print(json.dumps(src_acc.last_params), file=sys.stderr)
                print("Created {} transactions".format(len(txn_info_list)))
            except Exception as e:
                print("Could not send from {} to {}: {}".format(src_acc.address0x, dest, e))
        return txn_info_list, src_acc, None


def contract_multidest_transactions(contract, from_accounts, to_accounts, method, max_workers=8):
    assert len(from_accounts) > 0
    txn_map = get_txn_map(from_accounts, to_accounts)

    txn_info_list = []
    start = datetime.datetime.now()

    with ProcessPoolExecutor(max_workers=max_workers) as pool:
        all_tasks = [pool.submit(contract_create_multidest_txns, contract, src_acc, txn_map[src_acc], method) for src_acc in txn_map]

        for future in futures.as_completed(all_tasks):
            try:
                txns, src_acc, new_nonce = future.result()
                for tx in txns:
                    register_send(src_acc, tx)
                txn_info_list.extend(txns)
                # assign_nonce(src_acc, new_nonce)
            except Exception as e:
                print("Error: {}".format(e))

    end = datetime.datetime.now()
    td = end - start
    print("Produced {} transactions in {} => {:.2f} TPS".format(len(txn_info_list), td, len(txn_info_list)/td.total_seconds()), flush=True)
    return txn_info_list

def contract_create_txns(contract, src_accs, method):
        # Clear any cached sessions. This is needed to ensure multiple processes
        # don't try to reuse the same TCP connection, which would lead to havoc
        LocalNet = chain.BlockChain(API_ENDPOINT, version=1, network_id=0)
        chain.set_active_chain(LocalNet)
        contract = Contract.load_from_address(contract.address, load_state=False)

        txn_info_list = []
        for src_acc in src_accs:
            contract.account = src_acc
            src_addr = src_acc.bech32_address
            try:
                txn_info = None
                if method == 'registerOwnership':
                    txn_info = contract.call(method="registerOwnership", params=[
                        Contract.value_dict("ipfs_cid", "String", src_addr)], nonce=1, confirm=False)
                elif method == 'configureResolver':
                    label = src_addr
                    txn_info = contract.call(method="configureResolver", params=[
                        Contract.value_dict("recordOwner", "ByStr20", src_acc.address0x),
                        Contract.value_dict("node", "ByStr32", parentLabelToNode(rootNode, label)),
                        Contract.value_dict("resolver", "ByStr20", src_acc.address0x)], nonce=1, confirm=False)
                txn_info_list.append(txn_info)
                print(json.dumps(src_acc.last_params), file=sys.stderr)
                print("Created {} transactions".format(len(txn_info_list)))
            except Exception as e:
                print("Crowdfund exception: {}".format(e))
        # nonce_now = nonces.get(src_addr, src_acc.get_nonce())
        return txn_info_list, src_acc, None

def contract_transactions(contract, src_accs, method, max_workers=8):
    txn_info_list = []
    with ProcessPoolExecutor(max_workers=max_workers) as pool:
        all_tasks = [pool.submit(contract_create_txns, contract, [ src_acc ], method) for src_acc in src_accs]
        for future in futures.as_completed(all_tasks):
            try:
                txns, src_acc, new_nonce = future.result()
                for tx in txns:
                    register_send(src_acc, tx)
                txn_info_list.extend(txns)
                # assign_nonce(src_acc, new_nonce)
            except Exception as e:
                print("Error: {}".format(e))

def main_run():

    # # # Dry run
    # funded_accounts = 1
    # level = 1
    # level_bal = {level: int(genesis.get_balance())}
    # prev_batch_size = 1

    # num_levels = math.ceil(math.log(NUM_ACCOUNTS, ACC_BATCH_SIZE))

    # while funded_accounts < NUM_ACCOUNTS:
    #     batch_size = min(ACC_BATCH_SIZE ** level, NUM_ACCOUNTS - funded_accounts)
    #     amount_to_transfer = math.ceil(1.1 * NUM_ACCOUNTS * ACC_MIN_BALANCE) if level == 1 else (level_bal[level]  - ACC_MIN_BALANCE)/ batch_size

    #     print("{} accounts at level {}".format(batch_size, level + 1))
    #     for l, bal in level_bal.items():
    #         print("Level {} balance: {} ZILs".format(l, bal))

    #     total_to_transfer = amount_to_transfer * batch_size
    #     print("Transferring {} ZILs ({}x balance) from each account account @L{} to accounts @L{}".format(total_to_transfer, total_to_transfer/level_bal[level], level, level + 1))

    #     level_bal[level + 1] = amount_to_transfer
    #     level += 1
    #     prev_batch_size = batch_size
    #     funded_accounts += batch_size

    #     print("----------------")

    # exit(0)

    # Simple distribution from genesis to accounts

    # print(genesis.get_nonce())

    # batch_accs = []
    # for _ in range(NUM_ACCOUNTS):
    #     acc = gen_account()
    #     batch_accs.append(acc)
    # nativet = inter_account_transactions( [ genesis ], batch_accs, zils=ACC_MIN_BALANCE)

    # exit(0)

    # token = deploy_contract(genesis,
    #     "fungible.scilla", [
    #     Contract.value_dict("owner", "ByStr20", genesis.address0x),
    #     # Contract.value_dict("_sharding_input", "String",
    #     # "{\"transitions\" : [\"Transfer\", \"TransferFrom\", \"Mint\"], \"weak_reads\": [\"Transfer:balances[_sender]\", \"TransferFrom:balances[from]\"]}"),
    #     Contract.value_dict("init_supply", "Uint128", "1000000000000000000000000000000000"),
    #     Contract.value_dict("decimals", "Uint32", "0"),
    #     Contract.value_dict("name", "String", "Megabux"),
    #     Contract.value_dict("symbol", "String", "MGBX"),
    #     Contract.value_dict("default_operators", "List ByStr20", "[]")])

    # exit(0)

    # Transfers between accounts

    # token = Contract.load_from_address("0xf3a8bc908694DDd2d92c86317827a8A55476a700", load_state=False)

    # batch_accs = []
    # for _ in range(NUM_ACCOUNTS):
    #     acc = gen_account()
    #     batch_accs.append(acc)
    # tokent = token_inter_account_transactions(token, batch_accs, batch_accs, amount=100)

    # crowd = deploy_contract(genesis, "CrowdFunding.scilla", [
    #     Contract.value_dict("owner", "ByStr20", genesis.address0x),
    #     Contract.value_dict("max_block", "BNum", "1000"),
    #     Contract.value_dict("goal", "Uint128", "5000")])

    # pprint(crowd.get_state())

    # nonfung = deploy_contract(genesis, "nonfungible-rewritten.scilla", [
    #     Contract.value_dict("_sharding_input", "String",
    #     "{\"transitions\" : [\"mint\", \"transfer\"]}"),
    #     Contract.value_dict("contractOwner", "ByStr20", genesis.address0x),
    #     Contract.value_dict("name", "String", "CryptoKatz"),
    #     Contract.value_dict("symbol", "String", "KATZ"),
    # ])

    # pprint(nonfung.get_state())


    # proof = deploy_contract(genesis, "ProofIPFS.scilla", [
    #     Contract.value_dict("_sharding_input", "String",
    #     "{\"transitions\" : [\"registerOwnership\"]}"),
    #     Contract.value_dict("owner", "ByStr20", genesis.address0x),
    # ])

    # pprint(proof.get_state())

    # registry = deploy_contract(genesis, "registry-rewritten.scilla", [
    #     Contract.value_dict("_sharding_input", "String",
    #     "{\"transitions\" : [\"configureResolver\", \"bestow\"]}"),
    #     Contract.value_dict("initialOwner", "ByStr20", genesis.address0x),
    #     Contract.value_dict("rootNode", "ByStr32", "0x0000000000000000000000000000000000000000000000000000000000000000"),
    # ])

    # pprint(registry.get_state())

    # exit(0)

    # crowd = Contract.load_from_address("0xe1e16bf479a754f8b1010e6f908bdd5c98f8ff6f", load_state=False)
    # nonfung = Contract.load_from_address("0x25f8fb3dcd66ef086fb69c27c9b7b01c88a7c28d", load_state=False)
    # proof = Contract.load_from_address("0x555395974120a87b73dbc367a01e3f8a9de790f6", load_state=False)
    registry = Contract.load_from_address("0xf4661d40eadcaab4d7547df30a04344558d8e15c", load_state=False)

    batch_accs = []
    for _ in range(NUM_ACCOUNTS):
        acc = gen_account()
        batch_accs.append(acc)

    contract_multidest_transactions(registry, [ genesis ], batch_accs, 'bestow')
    print("XXXXX", file=sys.stderr, flush=True)
    contract_transactions(registry, batch_accs, 'configureResolver')

    # print("XXXXX", file=sys.stderr, flush=True)

    # nft_transactions(nonfung, [genesis], batch_accs, type='mint')
    # print("XXXXX", file=sys.stderr, flush=True)
    # nft_transactions(nonfung, batch_accs, batch_accs, type='transfer')

    exit(0)

    # Fancy distribution
    funded_accounts = 1
    accounts = [ genesis ]
    prev_batch = accounts
    # Keep representative account for each level to check balance
    level = 1
    level_acc = {level: genesis}
    while funded_accounts < NUM_ACCOUNTS:
        # Aim to increase with every batch, until we hit the desired NUM_ACCOUNTS
        batch_size = min(max(ACC_BATCH_SIZE, len(prev_batch) ** 100), NUM_ACCOUNTS - funded_accounts)

        acc = level_acc[level]
        # amount_to_transfer = math.ceil(1.1 * NUM_ACCOUNTS * ACC_MIN_BALANCE) if level == 1 else (acc.get_balance() - ACC_MIN_BALANCE) / batch_size
        tokens_to_transfer = math.ceil(1.1 * NUM_ACCOUNTS * TOKEN_MIN_BALANCE) if level == 1 else (int(token.get_state()["balances"][acc.address0x]) - TOKEN_MIN_BALANCE) // batch_size

        tx_batch = []
        batch_accs = []
        for _ in range(batch_size):
            acc = gen_account()
            batch_accs.append(acc)

        for l, acc in level_acc.items():
            print("Level {} balance: {} ZILs, {} MGBX".format(l, acc.get_balance(), token.get_state()["balances"][acc.address0x]))
        # print("Transferring {} ZILs and {} MGBX from each of {} account(s) @L{} to each of {} account(s) @L{}".format(amount_to_transfer, tokens_to_transfer, len(prev_batch), level, len(batch_accs), level + 1))

        # nativet = inter_account_transactions(prev_batch, batch_accs, zils=amount_to_transfer)
        tokent = token_inter_account_transactions(token, prev_batch, batch_accs, amount=tokens_to_transfer)

        prev_batch = batch_accs
        accounts.extend(batch_accs)
        funded_accounts += len(batch_accs)
        level += 1
        level_acc[level] = batch_accs[0]

        # tx_batch.extend(nativet)
        tx_batch.extend(tokent)
        wait_for_txs(tx_batch)
        print("Total accounts funded: {}".format(funded_accounts))

if __name__ == "__main__":
    main_run()