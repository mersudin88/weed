from node import Block
from block_validator import validate_block
from consensus import get_difficulty


previous_block = Block(
    index=0,
    timestamp=1000,
    previous_hash="0",
    transactions=[]
)

previous_block.hash = previous_block.calculate_hash()


chain = [
    previous_block
]


block = Block(
    index=1,
    timestamp=1060,
    previous_hash=previous_block.hash,
    transactions=[
        {
            "type": "coinbase",
            "receiver": "WEED1TEST",
            "amount": 50
        }
    ]
)


difficulty = get_difficulty(
    block.index,
    [
        {
            "index": previous_block.index,
            "timestamp": previous_block.timestamp
        }
    ]
)


print()
print("================================")
print("      WEED POW INTEGRATION")
print("================================")

print()
print("Difficulty:")
print(difficulty)

print()
print("Mining test block...")

block.mine(difficulty)

# Namjerno pokvari PoW
block.nonce += 1
block.hash = block.calculate_hash()

block_data = {
    "index": block.index,
    "timestamp": block.timestamp,
    "previous_hash": block.previous_hash,
    "transactions": block.transactions,
    "nonce": block.nonce,
    "hash": block.hash
}

previous_data = {
    "index": previous_block.index,
    "timestamp": previous_block.timestamp,
    "previous_hash": previous_block.previous_hash,
    "transactions": previous_block.transactions,
    "nonce": previous_block.nonce,
    "hash": previous_block.hash
}


valid, reason = validate_block(
    block_data,
    previous_data,
    {},
    chain
)


print()
print("Validator result:")
print(valid)

print()
print("Reason:")
print(reason)

print()

if valid:
    raise SystemExit(
        "TEST FAILED: invalid PoW was accepted"
    )

if reason != "Invalid Proof-of-Work":
    raise SystemExit(
        "TEST FAILED: unexpected rejection reason"
    )

print("================================")
print("     INVALID POW REJECTED")
print("        TEST PASSED")
print("================================")
