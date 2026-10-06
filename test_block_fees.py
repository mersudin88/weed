from transaction import Transaction
from block_validator import calculate_block_fees


transactions = [
    {
        "type": "transaction",
        "inputs": [
            {
                "txid": "tx1",
                "index": 0
            }
        ],
        "outputs": [
            {
                "address": "WEED1A",
                "amount": 98
            }
        ],
        "public_key": "",
        "signature": "",
        "hash": "tx1"
    },
    {
        "type": "transaction",
        "inputs": [
            {
                "txid": "tx2",
                "index": 0
            }
        ],
        "outputs": [
            {
                "address": "WEED1B",
                "amount": 47
            }
        ],
        "public_key": "",
        "signature": "",
        "hash": "tx2"
    }
]


utxos = {
    "tx1:0": {
        "address": "WEED1A",
        "amount": 100
    },
    "tx2:0": {
        "address": "WEED1B",
        "amount": 50
    }
}


fees = calculate_block_fees(
    transactions,
    utxos
)


print()
print("================================")
print("      WEED BLOCK FEE TEST")
print("================================")

print()
print("Transaction 1 fee:")
print("2 WEED")

print()
print("Transaction 2 fee:")
print("3 WEED")

print()
print("Total fees:")
print(fees, "WEED")


if fees != 5:
    raise SystemExit(
        "TEST FAILED: incorrect total fees"
    )


print()
print("================================")
print("         TEST PASSED")
print("================================")
