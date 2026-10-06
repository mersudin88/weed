import copy
import socket
import json

from node import WeedNode
from wallet_storage import load_wallet
from cli import create_transaction
from transaction_validator import validate_transaction


HOST = "127.0.0.1"
PORT = 5001


def send_transaction(transaction):

    message = {
        "type": "new_transaction",
        "transaction": {
            "inputs": transaction.inputs,
            "outputs": transaction.outputs,
            "public_key": transaction.public_key,
            "signature": transaction.signature
        }
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


def main():

    print("================================")
    print("     WEED P2P DOUBLE-SPEND")
    print("================================")

    node = WeedNode()
    wallet = load_wallet()

    # Napravi prvu transakciju.
    tx1 = create_transaction(
        node,
        wallet,
        "WEED162bb8f78b8d7b6e94a5d2cf853767f4329bf56e3",
        5,
        0
    )

    # Napravi drugu transakciju sa ISTIM inputom.
    tx2 = copy.deepcopy(tx1)

    tx2.outputs = [
        {
            "address": wallet.address,
            "amount": 5
        }
    ]

    tx2.signature = None
    tx2.sign(wallet)

    print()
    print("TX1:")
    print(tx1.transaction_hash())

    print()
    print("TX2:")
    print(tx2.transaction_hash())

    # Provjera da su obje različite.
    if tx1.transaction_hash() == tx2.transaction_hash():

        raise SystemExit(
            "ERROR: TX1 and TX2 are identical"
        )

    print()
    print("TX1 and TX2 are different.")

    print()
    print("Sending TX1 to Node B...")

    send_transaction(tx1)

    print("TX1 sent.")

    # Malo vremena da Node B obradi TX1.
    import time
    time.sleep(1)

    print()
    print("Sending TX2 to Node B...")

    send_transaction(tx2)

    print("TX2 sent.")

    print()
    print("================================")
    print(" Both transactions were sent.")
    print(" Node B should accept TX1")
    print(" and reject TX2.")
    print("================================")


if __name__ == "__main__":
    main()
