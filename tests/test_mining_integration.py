import os
import sys

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

sys.path.insert(0, PROJECT_ROOT)

os.environ["WEED_DATA_DIR"] = os.path.join(
    PROJECT_ROOT,
    "test_data"
)

import copy
import time

from wallet import Wallet
from transaction import Transaction
from mempool import Mempool
from node import WeedNode, Block
from chain_validator import validate_chain
from consensus import (
    get_block_reward,
    get_difficulty,
)

from cli import (
    validate_transaction,
    calculate_transaction_fee,
    apply_transaction_to_utxos
)


def test_mining_and_blockchain_validation():

    miner = Wallet()
    receiver = Wallet()

    node = WeedNode()

    mempool = Mempool()
    mempool.clear()

    transaction = Transaction(
        inputs=[
            {
                "txid": "integration-mining-utxo",
                "index": 0
            }
        ],
        outputs=[
            {
                "address": receiver.address,
                "amount": 5
            }
        ],
        public_key=miner.public_key_hex
    )

    transaction.sign(miner)

    assert transaction.verify_signature(miner)

    mempool.add_transaction(transaction)

    assert mempool.count() == 1

    previous_height = node.latest_block().index

    temp_utxos = copy.deepcopy(node.utxos)

    transactions = []
    total_fees = 0

    for tx in mempool.get_transactions():

        valid, reason = validate_transaction(
            tx,
            temp_utxos,
            current_height=len(node.chain)
        )

        if not valid:
            continue

        fee = calculate_transaction_fee(
            tx,
            temp_utxos
        )

        transaction_data = {
            "type": "transaction",
            "hash": tx.transaction_hash(),
            "inputs": tx.inputs,
            "outputs": tx.outputs,
            "public_key": tx.public_key,
            "signature": tx.signature
        }

        applied = apply_transaction_to_utxos(
            transaction_data,
            temp_utxos
        )

        if not applied:
            continue

        transactions.append(
            transaction_data
        )

        total_fees += fee

    subsidy = get_block_reward(
        len(node.chain)
    )

    miner_reward = subsidy + total_fees

    reward = {
        "type": "coinbase",
        "receiver": miner.address,
        "amount": miner_reward
    }

    block_transactions = [
        reward
    ] + transactions

    block = Block(
        index=len(node.chain),
        timestamp=time.time(),
        previous_hash=node.latest_block().hash,
        transactions=block_transactions
    )

    block.mine(
    get_difficulty(
        block.index,
        node.chain
    )
)

    node.chain.append(block)

    node.utxos = temp_utxos

    coinbase_id = f"{block.hash}:0"

    node.utxos[coinbase_id] = {
        "address": miner.address,
        "amount": miner_reward,
        "coinbase": True,
        "created_height": block.index
    }

    assert block.index == previous_height + 1
    assert block.hash.startswith("0000")

    chain_data = []

    for item in node.chain:

        chain_data.append({
            "index": item.index,
            "timestamp": item.timestamp,
            "previous_hash": item.previous_hash,
            "transactions": item.transactions,
            "nonce": item.nonce,
            "hash": item.hash
        })

    valid, reason = validate_chain(
        chain_data
    )

    assert valid, reason
    assert reason == "Blockchain is valid"

    mempool.clear()