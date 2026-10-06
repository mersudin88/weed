from wallet import Wallet
from transaction import Transaction


def test_transaction_hash_is_stable():

    wallet = Wallet()

    transaction = Transaction(
        inputs=[
            {
                "txid": "abc123",
                "index": 0
            }
        ],
        outputs=[
            {
                "address": wallet.address,
                "amount": 10
            }
        ],
        public_key=wallet.public_key_hex
    )

    hash1 = transaction.transaction_hash()
    hash2 = transaction.transaction_hash()

    assert hash1 == hash2
    assert len(hash1) == 64


def test_transaction_signature():

    wallet = Wallet()

    transaction = Transaction(
        inputs=[
            {
                "txid": "abc123",
                "index": 0
            }
        ],
        outputs=[
            {
                "address": wallet.address,
                "amount": 10
            }
        ],
        public_key=wallet.public_key_hex
    )

    transaction.sign(wallet)

    assert transaction.signature is not None
    assert transaction.verify_signature(wallet)


def test_transaction_rejects_changed_output():

    wallet = Wallet()

    transaction = Transaction(
        inputs=[
            {
                "txid": "abc123",
                "index": 0
            }
        ],
        outputs=[
            {
                "address": wallet.address,
                "amount": 10
            }
        ],
        public_key=wallet.public_key_hex
    )

    transaction.sign(wallet)

    transaction.outputs[0]["amount"] = 100

    assert not transaction.verify_signature(wallet)