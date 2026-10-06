from transaction import Transaction
from transaction_validator import calculate_transaction_fee


transaction = Transaction(
    inputs=[
        {
            "txid": "previous_tx",
            "index": 0,
            "amount": 100
        }
    ],
    outputs=[
        {
            "address": "WEED1TEST",
            "amount": 98
        }
    ],
    public_key="",
    signature=None
)


utxos = {
    "previous_tx:0": {
        "address": "WEED1TEST",
        "amount": 100
    }
}


fee = calculate_transaction_fee(
    transaction,
    utxos
)


print()
print("================================")
print("       WEED FEE TEST")
print("================================")

print()
print("Input:")
print("100 WEED")

print()
print("Output:")
print("98 WEED")

print()
print("Transaction fee:")
print(fee, "WEED")


if fee != 2:
    raise SystemExit(
        "TEST FAILED: incorrect fee"
    )


print()
print("================================")
print("         TEST PASSED")
print("================================")
