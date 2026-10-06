import copy

from node import WeedNode
from wallet_storage import load_wallet
from cli import create_transaction
from mempool import Mempool


def main():

    print("================================")
    print("   WEED MEMPOOL DOUBLE-SPEND")
    print("================================")

    node = WeedNode()
    wallet = load_wallet()

    mempool = Mempool()
    mempool.clear()

    # Prva transakcija.
    tx1 = create_transaction(
        node,
        wallet,
        "WEED162bb8f78b8d7b6e94a5d2cf853767f4329bf56e3",
        5,
        0
    )

    # Druga transakcija koristi ISTI input.
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

    # Prva mora biti prihvaćena.
    print()
    print("Adding TX1...")

    mempool.add_transaction(tx1)

    if mempool.count() != 1:
        raise SystemExit(
            "ERROR: TX1 was not added"
        )

    print("TX1 accepted.")

    # Druga mora biti odbijena.
    print()
    print("Adding TX2...")

    try:

        mempool.add_transaction(tx2)

    except ValueError as error:

        print()
        print("TX2 rejected:")
        print(error)

    else:

        raise SystemExit(
            "ERROR: Mempool accepted double-spend!"
        )

    # Mora ostati samo jedna transakcija.
    print()
    print("Mempool transactions:")
    print(mempool.count())

    if mempool.count() != 1:

        raise SystemExit(
            "ERROR: Mempool contains unexpected transactions"
        )

    print()
    print("================================")
    print("   MEMPOOL DOUBLE-SPEND BLOCKED")
    print("================================")


if __name__ == "__main__":
    main()
