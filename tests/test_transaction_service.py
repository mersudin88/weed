from transaction_service import (
    accept_transaction,
    transaction_from_dict,
    transaction_to_dict
)


def test_transaction_conversion():
    data = {
        "inputs": [
            {
                "txid": "abc",
                "index": 0,
                "amount": 50
            }
        ],
        "outputs": [
            {
                "address": "WEED1TEST",
                "amount": 40
            }
        ],
        "public_key": "public_key",
        "signature": "signature"
    }

    transaction = transaction_from_dict(data)

    result = transaction_to_dict(transaction)

    assert result == data


def test_accept_transaction_rejects_invalid_signature():
    class FakeNode:
        chain = [
            type(
                "Block",
                (),
                {
                    "index": 0
                }
            )()
        ]

        utxos = {}

    class FakeMempool:
        def get_transactions(self):
            return []

    data = {
        "inputs": [
            {
                "txid": "abc",
                "index": 0,
                "amount": 50
            }
        ],
        "outputs": [
            {
                "address": "WEED1TEST",
                "amount": 40
            }
        ],
        "public_key": "00",
        "signature": "invalid"
    }

    accepted, reason, txid = accept_transaction(
        FakeNode(),
        FakeMempool(),
        data
    )

    assert accepted is False
    assert reason == "Invalid transaction signature"
    assert txid


def test_accept_transaction_rejects_missing_input():
    class FakeNode:
        chain = [
            type(
                "Block",
                (),
                {
                    "index": 0
                }
            )()
        ]

        utxos = {}

    class FakeMempool:
        def get_transactions(self):
            return []

    data = {
        "inputs": [
            {
                "txid": "does-not-exist",
                "index": 0,
                "amount": 50
            }
        ],
        "outputs": [
            {
                "address": "WEED1TEST",
                "amount": 40
            }
        ],
        "public_key": "00",
        "signature": "00"
    }

    accepted, reason, txid = accept_transaction(
        FakeNode(),
        FakeMempool(),
        data
    )

    assert accepted is False
    assert reason == "Invalid transaction signature"
    assert txid
def test_accept_real_signed_transaction():
    from wallet import Wallet
    from transaction import Transaction
    from mempool import Mempool

    class FakeBlock:
        index = 0

    class TestNode:
        chain = [FakeBlock()]
        utxos = {}

    sender = Wallet()
    receiver = Wallet()

    transaction = Transaction(
        inputs=[
            {
                "txid": "funding_tx",
                "index": 0,
                "amount": 50
            }
        ],
        outputs=[
            {
                "address": receiver.address,
                "amount": 40
            }
        ],
        public_key=sender.public_key_hex
    )

    transaction.sign(sender)

    sender_address = sender.address

    TestNode.utxos = {
        "funding_tx:0": {
            "address": sender_address,
            "amount": 50
        }
    }

    mempool = Mempool()

    mempool.clear()

    accepted, reason, txid = accept_transaction(
        TestNode(),
        mempool,
        transaction_to_dict(transaction)
    )

    assert accepted is True
    assert reason == "Transaction accepted"
    assert txid == transaction.transaction_hash()

    transactions = mempool.get_transactions()

    assert len(transactions) == 1
    assert transactions[0].transaction_hash() == txid

    mempool.clear()    