import json
import hashlib


FILE = "blockchain_corruption_test.json"


with open(FILE, "r", encoding="utf-8") as file:
    chain = json.load(file)


original = chain[1]["nonce"]

chain[1]["nonce"] = original + 1


data = {
    "index": chain[1]["index"],
    "timestamp": chain[1]["timestamp"],
    "previous_hash": chain[1]["previous_hash"],
    "transactions": chain[1]["transactions"],
    "nonce": chain[1]["nonce"]
}

encoded = json.dumps(
    data,
    sort_keys=True,
    separators=(",", ":")
).encode()

calculated_hash = hashlib.sha256(
    encoded
).hexdigest()


print()
print("================================")
print("     CORRUPTION TEST")
print("================================")

print()
print("Original nonce:")
print(original)

print()
print("Modified nonce:")
print(chain[1]["nonce"])

print()
print("Stored hash:")
print(chain[1]["hash"])

print()
print("Calculated hash:")
print(calculated_hash)

print()

if calculated_hash != chain[1]["hash"]:

    print("CORRUPTION DETECTED")

else:

    print("ERROR: corruption was not detected")
