from wallet import Wallet
from transaction import Transaction
from mempool import Mempool


def make_transaction(wallet, txid, index=0):

    transaction = Transaction(
        inputs=[
            {
                "txid": txid,
                "index": index
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

    return transaction


def test_mempool_add_transaction():

    wallet = Wallet()
    mempool = Mempool()
    mempool.clear()

    transaction = make_transaction(
        wallet,
        "test-tx-1"
    )

    mempool.add_transaction(transaction)

    assert mempool.count() == 1

    mempool.clear()


def test_mempool_rejects_duplicate_transaction():

    wallet = Wallet()
    mempool = Mempool()
    mempool.clear()

    transaction = make_transaction(
        wallet,
        "test-tx-2"
    )

    mempool.add_transaction(transaction)

    try:
        mempool.add_transaction(transaction)
        assert False
    except ValueError:
        pass

    mempool.clear()


def test_mempool_rejects_conflicting_input():

    wallet = Wallet()
    mempool = Mempool()
    mempool.clear()

    transaction1 = make_transaction(
        wallet,
        "same-utxo"
    )

    transaction2 = make_transaction(
        wallet,
        "same-utxo"
    )

    mempool.add_transaction(transaction1)

    try:
        mempool.add_transaction(transaction2)
        assert False
    except ValueError:
        pass

    mempool.clear()