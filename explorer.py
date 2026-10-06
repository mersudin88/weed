import json
import os
import sys

from consensus import get_difficulty


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


def show_overview(chain):

    latest = chain[-1]

    transaction_count = 0

    for block in chain:

        for transaction in block["transactions"]:

            if transaction.get("type") == "transaction":
                transaction_count += 1

    reward = 0

    for transaction in latest["transactions"]:

        if transaction.get("type") == "coinbase":

            reward = transaction.get(
                "amount",
                0
            )

    print()
    print("================================")
    print("       WEED BLOCK EXPLORER")
    print("================================")
    print()

    print("Network:")
    print("WEED")
    print()

    print("Blockchain height:")
    print(latest["index"])
    print()

    print("Total blocks:")
    print(len(chain))
    print()

    print("Total transactions:")
    print(transaction_count)
    print()

    print("Latest block:")
    print(latest["index"])
    print()

    print("Latest hash:")
    print(latest["hash"])
    print()

    print("Previous hash:")
    print(latest["previous_hash"])
    print()

    print("Nonce:")
    print(latest["nonce"])
    print()

    print("Difficulty:")
    print(
        get_difficulty(
            latest["index"],
            chain
        )
    )
    print()

    print("Transactions in latest block:")
    print(len(latest["transactions"]))
    print()

    print("Latest block reward:")
    print(reward, "WEED")
    print()

    print("================================")


def show_block(chain, height):

    if height < 0 or height >= len(chain):

        print()
        print("Block does not exist.")
        return

    block = chain[height]

    difficulty = get_difficulty(
        height,
        chain
    )

    print()
    print("================================")
    print(f"          WEED BLOCK #{height}")
    print("================================")
    print()

    print("Index:")
    print(block["index"])
    print()

    print("Timestamp:")
    print(block["timestamp"])
    print()

    print("Previous hash:")
    print(block["previous_hash"])
    print()

    print("Hash:")
    print(block["hash"])
    print()

    print("Nonce:")
    print(block["nonce"])
    print()

    print("Difficulty:")
    print(difficulty)
    print()

    print("Transactions:")
    print(len(block["transactions"]))
    print()

    for number, transaction in enumerate(
        block["transactions"],
        start=1
    ):

        print("--------------------------------")
        print(
            f"Transaction #{number}"
        )
        print("--------------------------------")
        print()

        tx_type = transaction.get(
            "type",
            "unknown"
        )

        print("Type:")
        print(tx_type)
        print()

        if tx_type == "coinbase":

            print("Receiver:")
            print(
                transaction.get(
                    "receiver"
                )
            )
            print()

            print("Amount:")
            print(
                transaction.get(
                    "amount"
                ),
                "WEED"
            )
            print()

        elif tx_type == "transaction":

            print("TXID:")
            print(
                transaction.get(
                    "hash"
                )
            )
            print()

            print("Inputs:")
            print(
                len(
                    transaction.get(
                        "inputs",
                        []
                    )
                )
            )
            print()

            for tx_input in transaction.get(
                "inputs",
                []
            ):

                print(
                    f'  {tx_input["txid"]}:'
                    f'{tx_input["index"]}'
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

            for output in transaction.get(
                "outputs",
                []
            ):

                print(
                    f'  {output["address"]}'
                    f' -> {output["amount"]} WEED'
                )

            print()

    print("================================")


def main():

    chain = load_blockchain()

    if not chain:

        print()
        print("WEED blockchain not found.")
        return

    if len(sys.argv) == 1:

        show_overview(chain)
        return

    if len(sys.argv) != 2:

        print()
        print("Usage:")
        print("python explorer.py")
        print("python explorer.py BLOCK_HEIGHT")
        return

    try:

        height = int(sys.argv[1])

    except ValueError:

        print()
        print("Block height must be a number.")
        return

    show_block(
        chain,
        height
    )


if __name__ == "__main__":
    main()
