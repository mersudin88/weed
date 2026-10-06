from wallet import Wallet
from transaction import Transaction
from mempool import Mempool


def test_wallet_transaction_mempool_flow():

    sender = Wallet()
    receiver = Wallet()

    transaction = Transaction(
        inputs=[
            {
                "txid": "integration-test-utxo",
                "index": 0
            }
        ],
        outputs=[
            {
                "address": receiver.address,
                "amount": 10
            }
        ],
        public_key=sender.public_key_hex
    )

    transaction.sign(sender)

    assert transaction.signature is not None
    assert transaction.verify_signature(sender)

    mempool = Mempool()
    mempool.clear()

    mempool.add_transaction(transaction)

    assert mempool.count() == 1

    txid = transaction.transaction_hash()

    assert len(txid) == 64

    mempool.remove_transaction(txid)

    assert mempool.count() == 0