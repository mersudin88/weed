import copy

from node import WeedNode
from chain_validator import validate_chain


def test_original_chain():

    node = WeedNode()

    chain = [
        {
            "index": block.index,
            "timestamp": block.timestamp,
            "previous_hash": block.previous_hash,
            "transactions": copy.deepcopy(block.transactions),
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
            "Original chain should be valid"
        )

    return chain


def test_genesis_tampering(chain):

    tampered = copy.deepcopy(chain)

    tampered[0]["transactions"] = [
        {
            "type": "coinbase",
            "receiver": "WEED1TAMPERED",
            "amount": 999999
        }
    ]

    valid, reason = validate_chain(tampered)

    print()
    print("Genesis tampering:")
    print("VALID =", valid)
    print("Reason =", reason)

    if valid:
        raise SystemExit(
            "ERROR: Tampered genesis was accepted!"
        )


def test_block_one_tampering(chain):

    if len(chain) < 2:
        raise SystemExit(
            "Blockchain must contain block #1"
        )

    tampered = copy.deepcopy(chain)

    tampered[1]["transactions"].append(
        {
            "type": "transaction",
            "hash": "TAMPERED",
            "inputs": [],
            "outputs": [],
            "public_key": "",
            "signature": ""
        }
    )

    valid, reason = validate_chain(tampered)

    print()
    print("Block #1 tampering:")
    print("VALID =", valid)
    print("Reason =", reason)

    if valid:
        raise SystemExit(
            "ERROR: Tampered block #1 was accepted!"
        )


def main():

    print("================================")
    print("      WEED TAMPERING TEST")
    print("================================")

    chain = test_original_chain()

    test_genesis_tampering(chain)

    test_block_one_tampering(chain)

    print()
    print("================================")
    print("       ALL TESTS PASSED")
    print("================================")


if __name__ == "__main__":
    main()
