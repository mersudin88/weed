from wallet import Wallet
from wallet_storage import load_wallet
from transaction import Transaction


def main():

    print()
    print("================================")
    print("       WEED TRANSFER TEST")
    print("================================")

    sender = load_wallet()
    receiver = Wallet()

    print("\nSender:")
    print(sender.address)

    print("\nReceiver:")
    print(receiver.address)

    amount = 30

    transaction = Transaction(
        inputs=[
            {
                "txid": "TEST_UTXO",
                "index": 0,
                "amount": 50
            }
        ],
        outputs=[
            {
                "address": receiver.address,
                "amount": amount
            },
            {
                "address": sender.address,
                "amount": 20
            }
        ],
        public_key=sender.public_key_hex
    )

    transaction.sign(sender)

    print("\n========== TRANSACTION ==========")

    print("\nTransaction hash:")
    print(transaction.transaction_hash())

    print("\nSignature:")
    print(transaction.signature)

    print("\nSignature valid:")

    print(
        transaction.verify_signature(sender)
    )


if __name__ == "__main__":
    main()
