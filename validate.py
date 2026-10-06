import json
import os

from chain_validator import validate_chain
from utxo import build_utxos


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


def main():

    chain = load_blockchain()

    print()
    print("================================")
    print("       WEED VALIDATION")
    print("================================")
    print()

    if not chain:

        print("Blockchain:")
        print("NOT FOUND")
        return

    valid, reason = validate_chain(
        chain
    )

    print("Blockchain:")
    print(
        "VALID"
        if valid
        else "INVALID"
    )

    print()

    print("Result:")
    print(reason)

    print()

    print("Blocks:")
    print(len(chain))

    print()

    print("Height:")
    print(chain[-1]["index"])

    print()

    utxos = build_utxos(
        chain
    )

    print("UTXO set:")
    print("VALID")

    print()

    print("UTXOs:")
    print(len(utxos))

    print()

    print("================================")


if __name__ == "__main__":
    main()
