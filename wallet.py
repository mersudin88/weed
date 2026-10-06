import hashlib
import ecdsa


def address_from_public_key(public_key_hex):
    public_key_bytes = bytes.fromhex(public_key_hex)
    address_hash = hashlib.sha256(public_key_bytes).hexdigest()
    return "WEED1" + address_hash[:40]


class Wallet:

    def __init__(self):

        self.private_key = ecdsa.SigningKey.generate(
            curve=ecdsa.SECP256k1
        )

        self.public_key = self.private_key.get_verifying_key()

        self.public_key_hex = (
            self.public_key.to_string().hex()
        )

        self.address = address_from_public_key(
            self.public_key_hex
        )

    def sign(self, message):

        message_hash = hashlib.sha256(
            message.encode()
        ).digest()

        signature = self.private_key.sign_digest(
            message_hash
        )

        return signature.hex()

    def verify(self, message, signature):

        try:

            message_hash = hashlib.sha256(
                message.encode()
            ).digest()

            return self.public_key.verify_digest(
                bytes.fromhex(signature),
                message_hash
            )

        except Exception:

            return False

    def save_info(self):

        print("\n========== WEED WALLET ==========")

        print("\nAddress:")
        print(self.address)

        print("\nPublic key:")
        print(self.public_key_hex)

        print("\nPrivate key:")
        print(self.private_key.to_string().hex())

        print("\n=================================")


if __name__ == "__main__":

    wallet = Wallet()

    wallet.save_info()

    message = "WEED TEST TRANSACTION"

    signature = wallet.sign(message)

    print("\nSignature:")
    print(signature)

    print("\nSignature valid:")
    print(wallet.verify(message, signature))
