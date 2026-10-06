import hashlib
import json
import os
import socket
import subprocess
import sys
import time

from node import Block
from wallet import Wallet


PROJECT_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)


def wait_for_port(port, timeout=10):
    start = time.time()

    while time.time() - start < timeout:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.5):
                return True
        except OSError:
            time.sleep(0.1)

    return False


def load_chain(data_dir):
    path = os.path.join(data_dir, "blockchain.json")

    if not os.path.exists(path):
        return []

    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def send_message(port, message):
    with socket.create_connection(("127.0.0.1", port), timeout=5) as connection:
        connection.sendall(json.dumps(message).encode())


def make_coinbase_block(index, previous_hash, receiver, amount=50):
    block = Block(
        index=index,
        timestamp=time.time(),
        previous_hash=previous_hash,
        transactions=[
            {
                "type": "coinbase",
                "receiver": receiver,
                "amount": amount,
            }
        ],
    )

    block.mine(4)
    return block


def stop_process(process):
    if process is None:
        return

    if process.poll() is None:
        process.terminate()

        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


def test_real_p2p_block_propagation():
    data_a = os.path.join(PROJECT_ROOT, "test_real_p2p_a")
    data_b = os.path.join(PROJECT_ROOT, "test_real_p2p_b")

    os.makedirs(data_a, exist_ok=True)
    os.makedirs(data_b, exist_ok=True)

    for data_dir in [data_a, data_b]:
        for filename in ["blockchain.json", "mempool.json"]:
            path = os.path.join(data_dir, filename)
            if os.path.exists(path):
                os.remove(path)

    env_a = os.environ.copy()
    env_a["WEED_DATA_DIR"] = data_a

    env_b = os.environ.copy()
    env_b["WEED_DATA_DIR"] = data_b

    process_a = subprocess.Popen(
        [sys.executable, "-u", "p2p_server.py", "5000"],
        cwd=PROJECT_ROOT,
        env=env_a,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    process_b = None

    try:
        assert wait_for_port(5000)

        genesis_path_a = os.path.join(data_a, "blockchain.json")
        genesis_path_b = os.path.join(data_b, "blockchain.json")

        with open(genesis_path_a, "r", encoding="utf-8") as file:
            genesis_data = json.load(file)

        with open(genesis_path_b, "w", encoding="utf-8") as file:
            json.dump(genesis_data, file, indent=2)

        process_b = subprocess.Popen(
            [sys.executable, "-u", "p2p_server.py", "5001"],
            cwd=PROJECT_ROOT,
            env=env_b,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )

        assert wait_for_port(5001)
        time.sleep(1)

        chain_a = load_chain(data_a)
        chain_b = load_chain(data_b)

        assert len(chain_a) == 1
        assert len(chain_b) == 1

        wallet = Wallet()

        block_1 = make_coinbase_block(
            index=1,
            previous_hash=chain_a[-1]["hash"],
            receiver=wallet.address,
        )

        block_1_data = {
            "index": block_1.index,
            "timestamp": block_1.timestamp,
            "previous_hash": block_1.previous_hash,
            "transactions": block_1.transactions,
            "nonce": block_1.nonce,
            "hash": block_1.hash,
        }

        send_message(5000, {"type": "new_block", "block": block_1_data})

        propagated = False

        for _ in range(50):
            time.sleep(0.2)
            chain_a = load_chain(data_a)
            chain_b = load_chain(data_b)
            if len(chain_a) == 2 and len(chain_b) == 2:
                propagated = True
                break

        assert propagated
        assert chain_a[-1]["index"] == 1
        assert chain_b[-1]["index"] == 1
        assert chain_a[-1]["hash"] == block_1.hash
        assert chain_b[-1]["hash"] == block_1.hash

        block_2 = make_coinbase_block(
            index=2,
            previous_hash=chain_b[-1]["hash"],
            receiver=wallet.address,
        )

        block_2_data = {
            "index": block_2.index,
            "timestamp": block_2.timestamp,
            "previous_hash": block_2.previous_hash,
            "transactions": block_2.transactions,
            "nonce": block_2.nonce,
            "hash": block_2.hash,
        }

        send_message(5001, {"type": "new_block", "block": block_2_data})

        propagated = False

        for _ in range(50):
            time.sleep(0.2)
            chain_a = load_chain(data_a)
            chain_b = load_chain(data_b)
            if len(chain_a) == 3 and len(chain_b) == 3:
                propagated = True
                break

        assert propagated
        assert chain_a[-1]["index"] == 2
        assert chain_b[-1]["index"] == 2
        assert chain_a[-1]["hash"] == block_2.hash
        assert chain_b[-1]["hash"] == block_2.hash

    finally:
        stop_process(process_a)
        stop_process(process_b)

        output_a = process_a.stdout.read()
        output_b = process_b.stdout.read() if process_b is not None else ""

        print()
        print("--- NODE A ---")
        print(output_a)
        print()
        print("--- NODE B ---")
        print(output_b)


from node import Block, WeedNode
from p2p import P2PNode


def make_block(index, previous_hash, receiver):
    block = Block(
        index=index,
        timestamp=1000 + index,
        previous_hash=previous_hash,
        transactions=[
            {
                "type": "coinbase",
                "receiver": receiver,
                "amount": 50,
            }
        ],
    )

    block.mine(4)
    return block


def block_to_dict(block):
    return {
        "index": block.index,
        "timestamp": block.timestamp,
        "previous_hash": block.previous_hash,
        "transactions": block.transactions,
        "nonce": block.nonce,
        "hash": block.hash,
    }


def test_receive_longer_chain_reorganizes():
    node = WeedNode()
    genesis_block = node.chain[0]

    genesis_data = {
        "index": genesis_block.index,
        "timestamp": genesis_block.timestamp,
        "previous_hash": genesis_block.previous_hash,
        "transactions": genesis_block.transactions,
        "nonce": genesis_block.nonce,
        "hash": genesis_block.hash,
    }

    genesis_hash = genesis_block.hash

    a1 = make_block(1, genesis_hash, "WEED1local")
    a2 = make_block(2, a1.hash, "WEED1local")
    local_chain = [
        genesis_data,
        block_to_dict(a1),
        block_to_dict(a2),
    ]

    b1 = make_block(1, genesis_hash, "WEED1remote")
    b2 = make_block(2, b1.hash, "WEED1remote")
    b3 = make_block(3, b2.hash, "WEED1remote")
    longer_chain = [
        genesis_data,
        block_to_dict(b1),
        block_to_dict(b2),
        block_to_dict(b3),
    ]

    p2p = P2PNode(local_chain, host="127.0.0.1", port=5999)

    assert len(p2p.blockchain) == 3

    accepted = p2p.receive_chain(longer_chain)
    assert accepted is True

    assert len(p2p.blockchain) == 4
    assert p2p.blockchain[-1]["hash"] == b3.hash
    assert p2p.blockchain[1]["hash"] == b1.hash
    assert p2p.blockchain[2]["hash"] == b2.hash
    assert p2p.blockchain[3]["hash"] == b3.hash


def test_real_p2p_transaction_propagation_and_double_spend():
    data_a = os.path.join(PROJECT_ROOT, "test_real_tx_a")
    data_b = os.path.join(PROJECT_ROOT, "test_real_tx_b")

    os.makedirs(data_a, exist_ok=True)
    os.makedirs(data_b, exist_ok=True)

    for data_dir in [data_a, data_b]:
        for filename in ["blockchain.json", "mempool.json"]:
            path = os.path.join(data_dir, filename)
            if os.path.exists(path):
                os.remove(path)

    env_a = os.environ.copy()
    env_a["WEED_DATA_DIR"] = data_a

    env_b = os.environ.copy()
    env_b["WEED_DATA_DIR"] = data_b

    process_a = subprocess.Popen(
        [sys.executable, "-u", "p2p_server.py", "5000"],
        cwd=PROJECT_ROOT,
        env=env_a,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    process_b = None

    try:
        assert wait_for_port(5000)

        genesis_path_a = os.path.join(data_a, "blockchain.json")
        genesis_path_b = os.path.join(data_b, "blockchain.json")

        with open(genesis_path_a, "r", encoding="utf-8") as file:
            genesis_data = json.load(file)

        with open(genesis_path_b, "w", encoding="utf-8") as file:
            json.dump(genesis_data, file, indent=2)

        process_b = subprocess.Popen(
            [sys.executable, "-u", "p2p_server.py", "5001"],
            cwd=PROJECT_ROOT,
            env=env_b,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )

        assert wait_for_port(5001)
        time.sleep(1)

        wallet = Wallet()
        chain_a = load_chain(data_a)

        funding_block = make_coinbase_block(
            index=1,
            previous_hash=chain_a[-1]["hash"],
            receiver=wallet.address,
            amount=50,
        )

        funding_block_data = {
            "index": funding_block.index,
            "timestamp": funding_block.timestamp,
            "previous_hash": funding_block.previous_hash,
            "transactions": funding_block.transactions,
            "nonce": funding_block.nonce,
            "hash": funding_block.hash,
        }

        send_message(5000, {"type": "new_block", "block": funding_block_data})

        funding_propagated = False

        for _ in range(50):
            time.sleep(0.2)
            chain_a = load_chain(data_a)
            chain_b = load_chain(data_b)
            if (
                len(chain_a) == 2
                and len(chain_b) == 2
                and chain_a[-1]["hash"] == funding_block.hash
                and chain_b[-1]["hash"] == funding_block.hash
            ):
                funding_propagated = True
                break

        assert funding_propagated

        funding_txid = funding_block.hash

        transaction = {
            "type": "transaction",
            "inputs": [
                {
                    "txid": funding_txid,
                    "index": 0,
                    "amount": 50,
                    "address": wallet.address,
                }
            ],
            "outputs": [
                {"address": "WEED1receiver", "amount": 40}
            ],
            "public_key": wallet.public_key_hex,
            "signature": None,
        }

        signing_data = json.dumps(
            {
                "inputs": transaction["inputs"],
                "outputs": transaction["outputs"],
                "public_key": transaction["public_key"],
            },
            sort_keys=True,
            separators=(",", ":"),
        )

        transaction["signature"] = wallet.sign(signing_data)

        transaction_data = json.dumps(
            {
                "inputs": transaction["inputs"],
                "outputs": transaction["outputs"],
                "public_key": transaction["public_key"],
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode()

        transaction["hash"] = hashlib.sha256(transaction_data).hexdigest()

        send_message(5000, {"type": "new_transaction", "transaction": transaction})

        propagated = False

        for _ in range(50):
            time.sleep(0.2)

            mempool_a = os.path.join(data_a, "mempool.json")
            mempool_b = os.path.join(data_b, "mempool.json")

            if os.path.exists(mempool_a) and os.path.exists(mempool_b):
                with open(mempool_a, "r", encoding="utf-8") as file:
                    pool_a = json.load(file)

                with open(mempool_b, "r", encoding="utf-8") as file:
                    pool_b = json.load(file)

                if (
                    len(pool_a) == 1
                    and len(pool_b) == 1
                    and pool_a[0]["inputs"] == transaction["inputs"]
                    and pool_a[0]["outputs"] == transaction["outputs"]
                    and pool_a[0]["public_key"] == transaction["public_key"]
                    and pool_b[0]["inputs"] == transaction["inputs"]
                    and pool_b[0]["outputs"] == transaction["outputs"]
                    and pool_b[0]["public_key"] == transaction["public_key"]
                ):
                    propagated = True
                    break

        assert propagated

        double_spend = {
            "type": "transaction",
            "inputs": [
                {
                    "txid": funding_txid,
                    "index": 0,
                    "amount": 50,
                    "address": wallet.address,
                }
            ],
            "outputs": [
                {"address": "WEED1attacker", "amount": 40}
            ],
            "public_key": wallet.public_key_hex,
            "signature": None,
        }

        double_spend_signing_data = json.dumps(
            {
                "inputs": double_spend["inputs"],
                "outputs": double_spend["outputs"],
                "public_key": double_spend["public_key"],
            },
            sort_keys=True,
            separators=(",", ":"),
        )

        double_spend["signature"] = wallet.sign(double_spend_signing_data)

        double_spend_data = json.dumps(
            {
                "inputs": double_spend["inputs"],
                "outputs": double_spend["outputs"],
                "public_key": double_spend["public_key"],
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode()

        double_spend["hash"] = hashlib.sha256(double_spend_data).hexdigest()

        send_message(5001, {"type": "new_transaction", "transaction": double_spend})

        time.sleep(1)

        with open(os.path.join(data_b, "mempool.json"), "r", encoding="utf-8") as file:
            final_pool_b = json.load(file)

        assert len(final_pool_b) == 1

        assert (
            final_pool_b[0]["inputs"]
            == transaction["inputs"]
        )

        assert (
            final_pool_b[0]["outputs"]
            == transaction["outputs"]
        )

        assert (
            final_pool_b[0]["public_key"]
            == transaction["public_key"]
        )

        assert (
            final_pool_b[0]["outputs"]
            != double_spend["outputs"]
        )

    finally:
        stop_process(process_a)
        stop_process(process_b)

        output_a = process_a.stdout.read()
        output_b = process_b.stdout.read() if process_b is not None else ""

        print()
        print("--- NODE A ---")
        print(output_a)
        print()
        print("--- NODE B ---")
        print(output_b)
