from types import SimpleNamespace

from wallet import Wallet
from transaction import Transaction
from transaction_service import transaction_to_dict
from rpc_server import handle_request


class FakeMempool:

    def __init__(self):
        self.transactions = []

    def get_transactions(self):
        return self.transactions

    def add_transaction(self, transaction):
        self.transactions.append(transaction)


def test_rpc_send_transaction_accepts_real_transaction():

    sender = Wallet()
    receiver = Wallet()

    funding_txid = "funding_tx"

    node = SimpleNamespace()

    node.chain = [
        SimpleNamespace(index=0)
    ]

    node.utxos = {
        f"{funding_txid}:0": {
            "address": sender.address,
            "amount": 50
        }
    }

    mempool = FakeMempool()

    transaction = Transaction(
        inputs=[
            {
                "txid": funding_txid,
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

    request = {
        "method": "send_transaction",
        "transaction": transaction_to_dict(transaction)
    }

    response = handle_request(
        node,
        request,
        mempool
    )

    assert response["success"] is True
    assert response["message"] == "Transaction accepted"
    assert response["txid"] == transaction.transaction_hash()

    assert len(mempool.transactions) == 1
    assert (
        mempool.transactions[0].transaction_hash()
        == transaction.transaction_hash()
    )