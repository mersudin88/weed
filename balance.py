import json
import os
import sys


def get_blockchain_file():
    data_dir = os.environ.get(
        "WEED_DATA_DIR",
        "."
    )

    return os.path.join(
        data_dir,
        "blockchain.json"
    )


def calculate_balances(chain):
    utxos = {}

    for block in chain:

        for transaction in block["transactions"]:

            if transaction.get("type") == "coinbase":

                utxo_id = f'{block["hash"]}:0'

                utxos[utxo_id] = {
                    "address": transaction["receiver"],
                    "amount": transaction["amount"]
                }

                continue

            if transaction.get("type") != "transaction":
                continue

            txid = transaction["hash"]

            for tx_input in transaction["inputs"]:

                input_id = (
                    f'{tx_input["txid"]}:'
                    f'{tx_input["index"]}'
                )

                utxos.pop(
                    input_id,
                    None
                )

            for index, output in enumerate(
                transaction["outputs"]
            ):

                output_id = f"{txid}:{index}"

                utxos[output_id] = {
                    "address": output["address"],
                    "amount": output["amount"]
                }

    balances = {}

    for utxo in utxos.values():

        address = utxo["address"]
        amount = utxo["amount"]

        balances[address] = (
            balances.get(address, 0)
            + amount
        )

    return balances


def main():

    if len(sys.argv) != 2:

        print(
            "Usage: python balance.py ADDRESS"
        )

        return

    address = sys.argv[1]

    blockchain_file = get_blockchain_file()

    if not os.path.exists(blockchain_file):

        print("Blockchain not found.")

        return

    with open(
        blockchain_file,
        "r",
        encoding="utf-8"
    ) as file:

        chain = json.load(file)

    balances = calculate_balances(chain)

    balance = balances.get(
        address,
        0
    )

    print()
    print("================================")
    print("          WEED BALANCE")
    print("================================")
    print()
    print("Address:")
    print(address)
    print()
    print("Balance:")
    print(balance, "WEED")
    print()
    print("================================")


if __name__ == "__main__":
    main()
