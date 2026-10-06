import json
import socket
import hashlib
import time

from node import WeedNode


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
    print("       WEED P2P FAKE BLOCK")
    print("================================")

    node = WeedNode()

    latest = node.latest_block()

    fake_block = {
        "index": latest.index + 1,
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

    fake_block["hash"] = calculate_block_hash(
        fake_block
    )

    print()
    print("Fake block:")
    print(fake_block["index"])

    print()
    print("Fake reward:")
    print("1000 WEED")

    print()
    print("Fake hash:")
    print(fake_block["hash"])

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
    print("Node B should reject the block.")
    print("================================")


if __name__ == "__main__":
    main()
