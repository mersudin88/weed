import os
import json
import socket

from wallet_storage import load_wallet
from node import WeedNode
from cli import create_transaction
from transaction_validator import calculate_transaction_fee


HOST = "127.0.0.1"


def get_balance(node, address):

    balance = 0

    for utxo in node.utxos.values():

        if utxo["address"] == address:
            balance += utxo["amount"]

    return balance


def send_transaction(wallet, node):

    print()
    print("================================")
    print("          SEND WEED")
    print("================================")
    print()

    receiver = input(
        "Receiver address: "
    ).strip()

    if not receiver.startswith("WEED1"):

        print()
        print("Invalid WEED address.")
        return

    try:

        amount = int(
            input("Amount: ").strip()
        )

        fee = int(
            input("Fee: ").strip()
        )

    except ValueError:

        print()
        print("Amount and fee must be numbers.")
        return

    if amount <= 0:

        print()
        print("Amount must be positive.")
        return

    if fee < 0:

        print()
        print("Fee cannot be negative.")
        return

    try:

        transaction = create_transaction(
            node,
            wallet,
            receiver,
            amount,
            fee
        )

    except Exception as error:

        print()
        print("Transaction failed:")
        print(error)
        return

    actual_fee = calculate_transaction_fee(
        transaction,
        node.utxos
    )

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
    print("Total:")
    print(amount + actual_fee, "WEED")

    print()

    confirm = input(
        "Send transaction? [y/N]: "
    ).strip().lower()

    if confirm != "y":

        print()
        print("Transaction cancelled.")
        return

    message = {
        "type": "new_transaction",
        "transaction": {
            "inputs": transaction.inputs,
            "outputs": transaction.outputs,
            "public_key": transaction.public_key,
            "signature": transaction.signature
        }
    }

    port = 5000

    connection = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM
    )

    try:

        connection.connect(
            (HOST, port)
        )

        connection.sendall(
            json.dumps(message).encode()
        )

    finally:

        connection.close()

    print()
    print("Transaction sent successfully.")


def main():

    wallet = load_wallet()
    node = WeedNode()

    while True:

        print()
        print("================================")
        print("          WEED WALLET")
        print("================================")
        print()
        print("Address:")
        print(wallet.address)
        print()
        print("Balance:")
        print(
            get_balance(
                node,
                wallet.address
            ),
            "WEED"
        )
        print()
        print("1. Balance")
        print("2. Send")
        print("3. Address")
        print("4. Exit")
        print()

        choice = input(
            "Choose: "
        ).strip()

        if choice == "1":

            node = WeedNode()

            balance = get_balance(
                node,
                wallet.address
            )

            print()
            print("Balance:")
            print(balance, "WEED")

        elif choice == "2":

            node = WeedNode()

            send_transaction(
                wallet,
                node
            )

        elif choice == "3":

            print()
            print("Your WEED address:")
            print(wallet.address)

        elif choice == "4":

            print()
            print("Goodbye.")
            break

        else:

            print()
            print("Invalid choice.")


if __name__ == "__main__":
    main()
