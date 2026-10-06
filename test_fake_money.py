import copy

from node import WeedNode
from chain_validator import validate_chain


def node_chain_to_dict(node):

    return [
        {
            "index": block.index,
            "timestamp": block.timestamp,
            "previous_hash": block.previous_hash,
            "transactions": copy.deepcopy(
                block.transactions
            ),
            "nonce": block.nonce,
            "hash": block.hash
        }
        for block in node.chain
    ]


def main():

    print("================================")
    print("       WEED FAKE MONEY TEST")
    print("================================")

    node = WeedNode()

    chain = node_chain_to_dict(node)

    print()
    print("Original chain:")

    valid, reason = validate_chain(chain)

    print("VALID =", valid)
    print("Reason =", reason)

    if not valid:
        raise SystemExit(
            "Original chain must be valid"
        )

    # Kopija lanca za napad.
    fake_chain = copy.deepcopy(chain)

    # Blok #15 ima coinbase od 52 WEED.
    # Pokušavamo ga promijeniti na 1000 WEED.
    fake_chain[15]["transactions"][0]["amount"] = 1000

    print()
    print("Trying fake coinbase:")
    print("Block: 15")
    print("Fake reward: 1000 WEED")

    valid, reason = validate_chain(fake_chain)

    print()
    print("VALID =", valid)
    print("Reason =", reason)

    if valid:
        raise SystemExit(
            "ERROR: Fake money was accepted!"
        )

    print()
    print("================================")
    print("       FAKE MONEY REJECTED")
    print("================================")


if __name__ == "__main__":
    main()
