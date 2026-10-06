from mempool import Mempool
from transaction import Transaction
from transaction_validator import validate_transaction


def transaction_from_dict(data):
    return Transaction(
        inputs=data["inputs"],
        outputs=data["outputs"],
        public_key=data["public_key"],
        signature=data["signature"]
    )


def transaction_to_dict(transaction):
    return {
        "inputs": transaction.inputs,
        "outputs": transaction.outputs,
        "public_key": transaction.public_key,
        "signature": transaction.signature
    }


def accept_transaction(node, mempool, data):
    transaction = transaction_from_dict(data)

    txid = transaction.transaction_hash()

    for existing in mempool.get_transactions():

        if existing.transaction_hash() == txid:
            return False, "Transaction already known", txid

    valid, reason = validate_transaction(
        transaction,
        node.utxos,
        current_height=node.chain[-1].index + 1
    )

    if not valid:
        return False, reason, txid

    try:
        mempool.add_transaction(transaction)

    except ValueError as error:
        return False, str(error), txid

    return True, "Transaction accepted", txid