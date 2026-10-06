from wallet import Wallet
from transaction import Transaction


def main():

    wallet_a = Wallet()
    wallet_b = Wallet()

    print("Wallet A:")
    print(wallet_a.address)

    print("\nWallet B:")
    print(wallet_b.address)

    transaction = Transaction(

        inputs=[
            {
                "txid": "TEST_UTXO",
                "index": 0,
                "amount": 100
            }
        ],

        outputs=[
            {
                "address": wallet_b.address,
                "amount": 30
            },

            {
                "address": wallet_a.address,
                "amount": 70
            }
        ],

        public_key=wallet_a.public_key_hex
    )

    transaction.sign(wallet_a)

    print("\n========== TRANSACTION ==========")

    print("\nTransaction hash:")
    print(transaction.transaction_hash())

    print("\nSignature:")
    print(transaction.signature)

    print("\nSignature valid:")
    print(transaction.verify_signature(wallet_a))


if __name__ == "__main__":
    main()