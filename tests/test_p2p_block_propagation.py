from consensus import get_difficulty
import os
import sys

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

sys.path.insert(0, PROJECT_ROOT)

os.environ["WEED_DATA_DIR"] = os.path.join(
    PROJECT_ROOT,
    "test_p2p_data"
)

import copy

from node import WeedNode, Block
from wallet import Wallet
from p2p_server import blockchain_to_dict
from chain_validator import validate_chain


def test_node_b_accepts_valid_block_from_node_a():
    node_a = WeedNode()
    node_b = WeedNode()

    assert len(node_a.chain) == len(node_b.chain)

    miner = Wallet()

    previous_block = node_a.chain[-1]

    block = Block(
        index=len(node_a.chain),
        timestamp=previous_block.timestamp + 1,
        previous_hash=previous_block.hash,
        transactions=[
            {
                "type": "coinbase",
                "receiver": miner.address,
                "amount": 50,
            }
        ]
    )

    block.mine(
        get_difficulty(
            block.index,
            node_a.chain
        )
    )

    block_data = {
        "index": block.index,
        "timestamp": block.timestamp,
        "previous_hash": block.previous_hash,
        "transactions": block.transactions,
        "nonce": block.nonce,
        "hash": block.hash
    }

    previous_block_data = {
        "index": previous_block.index,
        "timestamp": previous_block.timestamp,
        "previous_hash": previous_block.previous_hash,
        "transactions": previous_block.transactions,
        "nonce": previous_block.nonce,
        "hash": previous_block.hash
    }

    validation_utxos = copy.deepcopy(node_b.utxos)

    from block_validator import validate_block

    valid, reason = validate_block(
        block_data,
        previous_block_data,
        validation_utxos,
        node_b.chain
    )

    assert valid, reason

    node_b.chain.append(
        Block(
            index=block_data["index"],
            timestamp=block_data["timestamp"],
            previous_hash=block_data["previous_hash"],
            transactions=block_data["transactions"],
            nonce=block_data["nonce"],
            hash=block_data["hash"]
        )
    )

    node_b.rebuild_utxos()
    node_b.save()

    assert len(node_b.chain) == len(node_a.chain) + 1

    assert node_b.chain[-1].hash == node_a.chain[-1].hash or \
           node_b.chain[-1].hash == block.hash

    chain_data = blockchain_to_dict(node_b)

    valid_chain, reason = validate_chain(chain_data)

    assert valid_chain, reason
