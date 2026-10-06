import json
import os
import sys


def load_blockchain():

    data_dir = os.environ.get(
        "WEED_DATA_DIR",
        "."
    )

    filename = os.path.join(
        data_dir,
        "blockchain.json"
    )

    if not os.path.exists(filename):
        return []

    with open(
        filename,
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)


def build_utxos(chain):

    utxos = {}

    for block in chain:

        for transaction in block["transactions"]:

            if transaction.get("type") == "coinbase":

                utxo_id = f'{block["hash"]}:0'

                utxos[utxo_id] = {
                    "address": transaction["receiver"],
                    "amount": transaction["amount"],
                    "block": block["index"]
                }

                continue

            if transaction.get("type") != "transaction":
                continue

            txid = transaction["hash"]

            for tx_input in transaction.get(
                "inputs",
                []
            ):

                input_id = (
                    f'{tx_input["txid"]}:'
                    f'{tx_input["index"]}'
                )

                utxos.pop(
                    input_id,
                    None
                )

            for index, output in enumerate(
                transaction.get(
                    "outputs",
                    []
                )
            ):

                output_id = f"{txid}:{index}"

                utxos[output_id] = {
                    "address": output["address"],
                    "amount": output["amount"],
                    "block": block["index"]
                }

    return utxos


def main():

    if len(sys.argv) != 2:

        print()
        print("Usage:")
        print("python utxo.py ADDRESS")
        return

    address = sys.argv[1]

    if not address.startswith("WEED1"):

        print()
        print("Invalid WEED address.")
        return

    chain = load_blockchain()

    if not chain:

        print()
        print("WEED blockchain not found.")
        return

    utxos = build_utxos(chain)

    owned = []

    for utxo_id, utxo in utxos.items():

        if utxo["address"] == address:

            owned.append(
                (
                    utxo_id,
                    utxo
                )
            )

    total = sum(
        utxo["amount"]
        for _, utxo in owned
    )

    print()
    print("================================")
    print("          WEED UTXO")
    print("================================")
    print()

    print("Address:")
    print(address)
    print()

    print("UTXOs:")
    print(len(owned))
    print()

    for number, (utxo_id, utxo) in enumerate(
        owned,
        start=1
    ):

        print("--------------------------------")
        print(
            f"UTXO #{number}"
        )
        print("--------------------------------")
        print()

        print("UTXO ID:")
        print(utxo_id)
        print()

        print("Amount:")
        print(utxo["amount"], "WEED")
        print()

        print("Created in block:")
        print(utxo["block"])
        print()

    print("================================")
    print("Total:")
    print(total, "WEED")
    print("================================")


if __name__ == "__main__":
    main()
