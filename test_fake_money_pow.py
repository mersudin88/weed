import copy
import hashlib
import json
import time

from node import WeedNode
from chain_validator import validate_chain
from consensus import get_difficulty


def block_hash(block):

    data = {
        "index": block["index"],
        "timestamp": block["timestamp"],
        "previous_hash": block["previous_hash"],
        "transactions": block["transactions"],
        "nonce": block["nonce"]
    }

    encoded = json.dumps(
        data,
        sort_keys=True,
        separators=(",", ":")
    ).encode()

    return hashlib.sha256(encoded).hexdigest()


def main():

    print("================================")
    print("   WEED FAKE MONEY + POW TEST")
    print("================================")

    node = WeedNode()

    chain = [
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

    valid, reason = validate_chain(chain)

    print()
    print("Original chain:")
    print("VALID =", valid)
    print("Reason =", reason)

    if not valid:
        raise SystemExit(
            "Original chain must be valid"
        )

    # Napravi kopiju bloka #15.
    fake_block = copy.deepcopy(chain[15])

    # Napadač pokušava stvoriti 1000 WEED.
    fake_block["transactions"][0]["amount"] = 1000

    # Novi timestamp i nonce.
    fake_block["timestamp"] = time.time()
    fake_block["nonce"] = 0

    difficulty = get_difficulty(
        fake_block["index"],
        chain
    )

    target = "0" * difficulty

    print()
    print("Attacker creates fake block:")
    print("Block:", fake_block["index"])
    print("Fake coinbase:", 1000, "WEED")
    print("Difficulty:", difficulty)
    print()
    print("Mining fake block...")

    while True:

        fake_block["hash"] = block_hash(
            fake_block
        )

        if fake_block["hash"].startswith(
            target
        ):
            break

        fake_block["nonce"] += 1

    print()
    print("Fake PoW found:")
    print("Nonce:", fake_block["nonce"])
    print("Hash:", fake_block["hash"])

    # Ubaci lažni blok u kopiju lanca.
    fake_chain = copy.deepcopy(chain)
    fake_chain[15] = fake_block

    valid, reason = validate_chain(
        fake_chain
    )

    print()
    print("Validator result:")
    print("VALID =", valid)
    print("Reason =", reason)

    if valid:
        raise SystemExit(
            "ERROR: Fake money with valid PoW was accepted!"
        )

    print()
    print("================================")
    print("   FAKE MONEY + POW REJECTED")
    print("================================")


if __name__ == "__main__":
    main()
