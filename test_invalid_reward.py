from node import Block
from block_validator import validate_block
from consensus import get_difficulty


previous_block = {
    "index": 0,
    "timestamp": 0,
    "previous_hash": "0",
    "transactions": [],
    "nonce": 0,
    "hash": "genesis"
}


block = Block(
    index=1,
    timestamp=60,
    previous_hash=previous_block["hash"],
    transactions=[
        {
            "type": "coinbase",
            "receiver": "WEED1TEST",
            "amount": 999
        }
    ]
)


difficulty = get_difficulty(
    block.index
)

print()
print("================================")
print("     WEED INVALID REWARD TEST")
print("================================")

print()
print("Mining block with invalid reward...")
print("Reward:", 999)

block.mine(difficulty)

block_data = {
    "index": block.index,
    "timestamp": block.timestamp,
    "previous_hash": block.previous_hash,
    "transactions": block.transactions,
    "nonce": block.nonce,
    "hash": block.hash
}


utxos = {}

valid, reason = validate_block(
    block_data,
    previous_block,
    utxos,
    None
)

print()
print("Validator result:")
print(valid)

print()
print("Reason:")
print(reason)

if valid:
    raise SystemExit(
        "TEST FAILED: invalid reward was accepted"
    )

if reason != "Invalid block reward":
    raise SystemExit(
        "TEST FAILED: unexpected rejection reason"
    )

print()
print("================================")
print("   INVALID REWARD REJECTED")
print("        TEST PASSED")
print("================================")
