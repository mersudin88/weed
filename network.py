import json
import os

from chain_validator import validate_chain


def load_chain(data_dir):

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
                    "amount": transaction["amount"]
                }

            elif transaction.get("type") == "transaction":

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

                for output_index, output in enumerate(
                    transaction["outputs"]
                ):

                    output_id = (
                        f"{txid}:"
                        f"{output_index}"
                    )

                    utxos[output_id] = {
                        "address": output["address"],
                        "amount": output["amount"]
                    }

    return utxos


def get_balance(utxos, address):

    total = 0

    for utxo in utxos.values():

        if utxo["address"] == address:

            total += utxo["amount"]

    return total


def show_node(name, data_dir):

    chain = load_chain(
        data_dir
    )

    print()
    print("--------------------------------")
    print(name)
    print("--------------------------------")

    if not chain:

        print("Status: NOT FOUND")
        return None

    valid, reason = validate_chain(
        chain
    )

    utxos = build_utxos(
        chain
    )

    latest = chain[-1]

    print("Status:", "VALID" if valid else "INVALID")
    print("Blocks:", len(chain))
    print("Height:", latest["index"])
    print("UTXOs:", len(utxos))
    print("Latest hash:")
    print(latest["hash"])

    return {
        "chain": chain,
        "utxos": utxos,
        "valid": valid
    }


def main():

    print()
    print("================================")
    print("       WEED NETWORK STATUS")
    print("================================")

    node_a = show_node(
        "NODE A",
        "node_a"
    )

    node_b = show_node(
        "NODE B",
        "node_b"
    )

    print()
    print("================================")
    print("          CONSENSUS")
    print("================================")

    if node_a and node_b:

        chain_a = node_a["chain"]
        chain_b = node_b["chain"]

        same_height = (
            len(chain_a) == len(chain_b)
        )

        same_tip = (
            chain_a[-1]["hash"]
            == chain_b[-1]["hash"]
        )

        both_valid = (
            node_a["valid"]
            and node_b["valid"]
        )

        print()
        print(
            "Both chains valid:",
            "YES" if both_valid else "NO"
        )

        print(
            "Same height:",
            "YES" if same_height else "NO"
        )

        print(
            "Same latest block:",
            "YES" if same_tip else "NO"
        )

        if same_height and same_tip and both_valid:

            print()
            print("NETWORK CONSENSUS: OK")

        else:

            print()
            print("NETWORK CONSENSUS: WARNING")

    print()
    print("================================")


if __name__ == "__main__":
    main()
