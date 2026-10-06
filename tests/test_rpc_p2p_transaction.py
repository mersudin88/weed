import socket
import time
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


class FakeP2P:

    def __init__(self):
        self.messages = []

    def broadcast(self, message):
        self.messages.append(message)


def test_rpc_transaction_broadcasts_to_p2p():

    sender = Wallet()
    receiver = Wallet()

    node = SimpleNamespace()

    node.chain = [
        SimpleNamespace(index=0)
    ]

    node.utxos = {
        "funding_tx:0": {
            "address": sender.address,
            "amount": 50
        }
    }

    mempool = FakeMempool()
    p2p = FakeP2P()

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

    request = {
        "method": "send_transaction",
        "transaction": transaction_to_dict(transaction)
    }

    response = handle_request(
        node,
        request,
        mempool,
        p2p
    )

    assert response["success"] is True

    assert len(mempool.transactions) == 1

    assert len(p2p.messages) == 1

    message = p2p.messages[0]

    assert message["type"] == "new_transaction"

    assert (
        message["transaction"]["signature"]
        == transaction.signature
    )

    assert (
        message["transaction"]["public_key"]
        == transaction.public_key
    )