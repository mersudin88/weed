import json
import socket
import sys

from wallet_storage import load_wallet
from node import WeedNode
from cli import create_transaction
from transaction_validator import calculate_transaction_fee


HOST = "127.0.0.1"


def main():

    if len(sys.argv) not in (4, 5):

        print(
            "Usage: python p2p_send_transaction.py "
            "PORT ADDRESS AMOUNT [FEE]"
        )

        return

    port = int(sys.argv[1])
    receiver = sys.argv[2]
    amount = int(sys.argv[3])

    fee = 0

    if len(sys.argv) == 5:
        fee = int(sys.argv[4])

    wallet = load_wallet()
    node = WeedNode()

    transaction = create_transaction(
        node,
        wallet,
        receiver,
        amount,
        fee
    )

    actual_fee = calculate_transaction_fee(
        transaction,
        node.utxos
    )

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
        (HOST, port)
    )

    connection.sendall(
        json.dumps(message).encode()
    )

    connection.close()

    print()
    print("================================")
    print("    WEED TRANSACTION BROADCAST")
    print("================================")

    print()
    print("TXID:")
    print(transaction.transaction_hash())

    print()
    print("Amount:")
    print(amount, "WEED")

    print()
    print("Fee:")
    print(actual_fee, "WEED")

    print()
    print("Total input cost:")
    print(
        amount + actual_fee,
        "WEED"
    )

    print()
    print("Receiver:")
    print(receiver)

    print()
    print("Transaction sent to:")
    print(f"{HOST}:{port}")


if __name__ == "__main__":
    main()
