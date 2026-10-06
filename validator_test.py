from wallet_storage import load_wallet
from wallet import Wallet
from transaction import Transaction
from node import WeedNode
from transaction_validator import validate_transaction


def main():

    node = WeedNode()

    sender = load_wallet()
    receiver = Wallet()

    selected = None

    for utxo_id, utxo in node.utxos.items():

        if utxo["address"] == sender.address:

            selected = (utxo_id, utxo)
            break

    if selected is None:

        print("No UTXO found.")
        return

    utxo_id, utxo = selected

    txid, index = utxo_id.rsplit(":", 1)

    transaction = Transaction(

        inputs=[
            {
                "txid": txid,
                "index": int(index),
                "amount": utxo["amount"]
            }
        ],

        outputs=[
            {
                "address": receiver.address,
                "amount": 30
            },

            {
                "address": sender.address,
                "amount": utxo["amount"] - 30
            }
        ],

        public_key=sender.public_key_hex
    )

    transaction.sign(sender)

    valid, reason = validate_transaction(
        transaction,
        node.utxos
    )

    print()
    print("================================")
    print("       TRANSACTION VALIDATOR")
    print("================================")

    print("\nTransaction:")
    print(transaction.transaction_hash())

    print("\nSignature valid:")
    print(transaction.verify_signature(sender))

    print("\nValidator:")
    print(valid)

    print("\nReason:")
    print(reason)


if __name__ == "__main__":
    main()
