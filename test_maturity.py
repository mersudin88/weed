from utxo_rules import validate_coinbase_spend


print()
print("================================")
print("       WEED MATURITY TEST")
print("================================")
print()

tests = [
    (14, 14),
    (15, 15),
    (15, 14),
    (114, 15),
    (115, 15),
]

for current_height, created_height in tests:

    valid, reason = validate_coinbase_spend(
        current_height,
        created_height
    )

    print(
        f"Current: {current_height:>3} | "
        f"Created: {created_height:>3} | "
        f"Allowed: {valid} | "
        f"{reason}"
    )

print()
print("================================")
