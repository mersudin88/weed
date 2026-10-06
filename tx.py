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


def find_transaction(chain, txid):

    for block in chain:

        for transaction in block["transactions"]:

            if transaction.get("type") != "transaction":
                continue

            if transaction.get("hash") == txid:

                return block, transaction

    return None, None


def find_input_utxo(chain, txid, index):

    for block in chain:

        for transaction in block["transactions"]:

            if transaction.get("type") == "coinbase":

                if txid == block["hash"] and index == 0:

                    return {
                        "address": transaction["receiver"],
                        "amount": transaction["amount"]
                    }

            elif transaction.get("type") == "transaction":

                if transaction.get("hash") != txid:
                    continue

                outputs = transaction.get(
                    "outputs",
                    []
                )

                if index >= len(outputs):
                    return None

                output = outputs[index]

                return {
                    "address": output["address"],
                    "amount": output["amount"]
                }

    return None


def main():

    if len(sys.argv) != 2:

        print()
        print("Usage:")
        print("python tx.py TXID")
        return

    txid = sys.argv[1]

    chain = load_blockchain()

    if not chain:

        print()
        print("WEED blockchain not found.")
        return

    block, transaction = find_transaction(
        chain,
        txid
    )

    if transaction is None:

        print()
        print("Transaction not found.")
        return

    total_input = 0
    total_output = 0

    input_details = []

    for tx_input in transaction.get(
        "inputs",
        []
    ):

        input_txid = tx_input["txid"]
        input_index = tx_input["index"]

        utxo = find_input_utxo(
            chain,
            input_txid,
            input_index
        )

        if utxo is not None:

            total_input += utxo["amount"]

            input_details.append({
                "txid": input_txid,
                "index": input_index,
                "address": utxo["address"],
                "amount": utxo["amount"]
            })

    for output in transaction.get(
        "outputs",
        []
    ):

        total_output += output["amount"]

    fee = total_input - total_output

    print()
    print("================================")
    print("       WEED TRANSACTION")
    print("================================")
    print()

    print("TXID:")
    print(transaction["hash"])
    print()

    print("Block:")
    print(block["index"])
    print()

    print("Block hash:")
    print(block["hash"])
    print()

    print("Inputs:")
    print(len(input_details))
    print()

    for item in input_details:

        print(
            f'  {item["txid"]}:{item["index"]}'
        )

        print(
            f'  Address: {item["address"]}'
        )

        print(
            f'  Amount: {item["amount"]} WEED'
        )

        print()

    print("Outputs:")
    print(
        len(
            transaction.get(
                "outputs",
                []
            )
        )
    )
    print()

    for output in transaction["outputs"]:

        print(
            f'  Address: {output["address"]}'
        )

        print(
            f'  Amount: {output["amount"]} WEED'
        )

        print()

    print("Total input:")
    print(total_input, "WEED")
    print()

    print("Total output:")
    print(total_output, "WEED")
    print()

    print("Transaction fee:")
    print(fee, "WEED")
    print()

    print("================================")


if __name__ == "__main__":
    main()
