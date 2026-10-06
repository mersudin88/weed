from wallet import Wallet
import json

wallet = Wallet()

data = {
    "private_key": wallet.private_key.to_string().hex(),
    "public_key": wallet.public_key_hex,
    "address": wallet.address
}

with open(
    "wallet_b.json",
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        data,
        file,
        indent=2
    )

print()
print("================================")
print("          WEED WALLET B")
print("================================")

print()
print("Address:")
print(wallet.address)

print()
print("Wallet saved to:")
print("wallet_b.json")
