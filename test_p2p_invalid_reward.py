from node import Block
from block_validator import validate_block
from consensus import get_block_reward, get_difficulty


previous_block = {
    "index": 0,
    "timestamp": 0,
    "previous_hash": "0",
    "transactions": [],
    "nonce": 0,
    "hash": "genesis"
}


correct_reward = get_block_reward(1)

block = Block(
    index=1,
    timestamp=60,
    previous_hash=previous_block["hash"],
    transactions=[
        {
            "type": "coinbase",
            "receiver": "WEED1TEST",
            "amount": correct_reward + 100
        }
    ]
)


difficulty = get_difficulty(
    block.index
)

print()
print("================================")
print("   WEED P2P INVALID BLOCK TEST")
print("================================")

print()
print("Correct reward:")
print(correct_reward)

print()
print("Fake reward:")
print(correct_reward + 100)

print()
print("Mining invalid block...")

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
print("P2P validator result:")
print(valid)

print()
print("Reason:")
print(reason)


if valid:
    raise SystemExit(
        "TEST FAILED: invalid P2P block was accepted"
    )

if reason != "Invalid block reward":
    raise SystemExit(
        "TEST FAILED: unexpected rejection reason"
    )


print()
print("================================")
print("      INVALID BLOCK REJECTED")
print("          TEST PASSED")
print("================================")
