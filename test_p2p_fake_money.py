import json
import socket
import hashlib
import time
import os

os.environ["WEED_DATA_DIR"] = "node_b"

from node import WeedNode
from consensus import get_difficulty


HOST = "127.0.0.1"
PORT = 5001


def calculate_block_hash(block):

    data = {
        "index": block["index"],
        "timestamp": block["timestamp"],
        "previous_hash": block["previous_hash"],
        "transactions": block["transactions"],
        "nonce": block["nonce"]
    }

    encoded = json.dumps(
        data,
        sort_keys=True,
        separators=(",", ":")
    ).encode()

    return hashlib.sha256(encoded).hexdigest()


def main():

    print("================================")
    print("      WEED P2P FAKE MONEY")
    print("================================")

    node = WeedNode()

    latest = node.latest_block()

    block_index = latest.index + 1

    difficulty = get_difficulty(
        block_index,
        node.chain
    )

    print()
    print("Current chain:")
    print(len(node.chain), "blocks")

    print()
    print("Fake block:")
    print(block_index)

    print()
    print("Difficulty:")
    print(difficulty)

    fake_block = {
        "index": block_index,
        "timestamp": time.time(),
        "previous_hash": latest.hash,
        "transactions": [
            {
                "type": "coinbase",
                "receiver": (
                    "WEED1ad21400034cebc71616d4de82957970b378ae541"
                ),
                "amount": 1000
            }
        ],
        "nonce": 0
    }

    print()
    print("Mining fake block PoW...")

    target = "0" * difficulty

    while True:

        fake_block["hash"] = calculate_block_hash(
            fake_block
        )

        if fake_block["hash"].startswith(target):
            break

        fake_block["nonce"] += 1

    print()
    print("Fake block mined.")

    print()
    print("Hash:")
    print(fake_block["hash"])

    print()
    print("Fake reward:")
    print("1000 WEED")

    message = {
        "type": "new_block",
        "block": fake_block
    }

    connection = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM
    )

    connection.connect(
        (HOST, PORT)
    )

    connection.sendall(
        json.dumps(message).encode()
    )

    connection.close()

    print()
    print("Fake block sent to Node B.")

    print()
    print("Node B MUST reject it.")
    print("================================")


if __name__ == "__main__":
    main()
