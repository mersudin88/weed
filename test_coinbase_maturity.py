from transaction import Transaction
from transaction_validator import validate_transaction
from wallet import Wallet


wallet = Wallet()

tx = Transaction(
    inputs=[
        {
            "txid": "fake_coinbase",
            "index": 0,
            "amount": 50
        }
    ],
    outputs=[
        {
            "address": wallet.address,
            "amount": 49
        }
    ],
    public_key=wallet.public_key_hex
)

tx.sign(wallet)

utxo = {
    "fake_coinbase:0": {
        "address": wallet.address,
        "amount": 50,
        "coinbase": True,
        "created_height": 15
    }
}


print()
print("================================")
print("     WEED COINBASE MATURITY")
print("================================")
print()


for height in [15, 50, 114, 115]:

    valid, reason = validate_transaction(
        tx,
        utxo,
        current_height=height
    )

    print(
        f"Height {height}: "
        f"{'ACCEPTED' if valid else 'REJECTED'}"
    )

    print(
        f"Reason: {reason}"
    )

    print()


print("================================")
