from node import Block
from wallet import Wallet
from transaction import Transaction
from block_validator import validate_block
from consensus import get_block_reward, get_difficulty


wallet = Wallet()


previous_block = {
    "index": 0,
    "timestamp": 0,
    "previous_hash": "0",
    "transactions": [],
    "nonce": 0,
    "hash": "genesis"
}


# Napravi UTXO od 100 WEED.
utxos = {
    "funding:0": {
        "address": wallet.address,
        "amount": 100
    }
}


# 100 input -> 98 output = 2 WEED fee.
transaction = Transaction(
    inputs=[
        {
            "txid": "funding",
            "index": 0,
            "amount": 100
        }
    ],
    outputs=[
        {
            "address": wallet.address,
            "amount": 98
        }
    ],
    public_key=wallet.public_key_hex
)

transaction.sign(wallet)

transaction_data = {
    "type": "transaction",
    "inputs": transaction.inputs,
    "outputs": transaction.outputs,
    "public_key": transaction.public_key,
    "signature": transaction.signature,
    "hash": transaction.transaction_hash()
}


subsidy = get_block_reward(1)
fee = 2
maximum_reward = subsidy + fee


def make_block(coinbase_amount):

    block = Block(
        index=1,
        timestamp=60,
        previous_hash=previous_block["hash"],
        transactions=[
            {
                "type": "coinbase",
                "receiver": wallet.address,
                "amount": coinbase_amount
            },
            transaction_data
        ]
    )

    difficulty = get_difficulty(1)

    print()
    print(
        f"Mining test block with coinbase "
        f"{coinbase_amount} WEED..."
    )

    block.mine(difficulty)

    return {
        "index": block.index,
        "timestamp": block.timestamp,
        "previous_hash": block.previous_hash,
        "transactions": block.transactions,
        "nonce": block.nonce,
        "hash": block.hash
    }


print()
print("================================")
print("   WEED COINBASE FEE VALIDATION")
print("================================")

print()
print("Subsidy:")
print(subsidy, "WEED")

print()
print("Transaction fee:")
print(fee, "WEED")

print()
print("Maximum allowed coinbase:")
print(maximum_reward, "WEED")


# --------------------------------
# TEST 1: 52 WEED - should pass
# --------------------------------

valid_block = make_block(
    maximum_reward
)

valid_utxos = {
    key: value.copy()
    for key, value in utxos.items()
}

valid, reason = validate_block(
    valid_block,
    previous_block,
    valid_utxos,
    None
)

print()
print("Testing maximum allowed coinbase...")
print("Result:", valid)
print("Reason:", reason)

if not valid:
    raise SystemExit(
        "TEST FAILED: valid coinbase was rejected"
    )


# --------------------------------
# TEST 2: 53 WEED - should fail
# --------------------------------

invalid_block = make_block(
    maximum_reward + 1
)

invalid_utxos = {
    key: value.copy()
    for key, value in utxos.items()
}

valid, reason = validate_block(
    invalid_block,
    previous_block,
    invalid_utxos,
    None
)

print()
print("Testing excessive coinbase...")
print("Result:", valid)
print("Reason:", reason)

if valid:
    raise SystemExit(
        "TEST FAILED: excessive coinbase was accepted"
    )

if reason != "Coinbase reward exceeds allowed amount":
    raise SystemExit(
        "TEST FAILED: unexpected rejection reason"
    )


print()
print("================================")
print("        TEST PASSED")
print("================================")
