import json
import os

from wallet import Wallet


WALLET_FILE = os.environ.get(
    "WEED_WALLET_FILE",
    "wallet.json"
)


def create_wallet():

    wallet = Wallet()

    data = {
        "private_key": wallet.private_key.to_string().hex(),
        "public_key": wallet.public_key_hex,
        "address": wallet.address
    }

    with open(
        WALLET_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            data,
            file,
            indent=2
        )

    return wallet


def load_wallet():

    if not os.path.exists(WALLET_FILE):
        return create_wallet()

    with open(
        WALLET_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        data = json.load(file)

    wallet = Wallet.__new__(Wallet)

    import ecdsa

    wallet.private_key = ecdsa.SigningKey.from_string(
        bytes.fromhex(data["private_key"]),
        curve=ecdsa.SECP256k1
    )

    wallet.public_key = (
        wallet.private_key.get_verifying_key()
    )

    wallet.public_key_hex = (
        wallet.public_key.to_string().hex()
    )

    wallet.address = data["address"]

    return wallet
