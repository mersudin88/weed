import json
import hashlib

from transaction import Transaction
from transaction_validator import (
    validate_transaction,
    calculate_transaction_fee
)
from consensus import (
    get_block_reward,
    get_difficulty,
    MERKLE_ACTIVATION_HEIGHT
)


def calculate_block_hash(block):

    data = {
        "index": block["index"],
        "timestamp": block["timestamp"],
        "previous_hash": block["previous_hash"],
        "transactions": block["transactions"],
        "nonce": block["nonce"]
    }

    if block["index"] >= MERKLE_ACTIVATION_HEIGHT:

        transaction_data = [
            json.dumps(
                transaction,
                sort_keys=True,
                separators=(",", ":")
            )
            for transaction in block["transactions"]
        ]

        from merkle import merkle_root

        data["merkle_root"] = merkle_root(
            transaction_data
        )

    encoded = json.dumps(
        data,
        sort_keys=True,
        separators=(",", ":")
    ).encode()

    return hashlib.sha256(
        encoded
    ).hexdigest()


def calculate_block_fees(
    transactions,
    utxos
):

    total_fees = 0

    for transaction in transactions:

        if transaction.get("type") != "transaction":
            continue

        tx = Transaction(
            inputs=transaction["inputs"],
            outputs=transaction["outputs"],
            public_key=transaction["public_key"],
            signature=transaction["signature"]
        )

        total_fees += calculate_transaction_fee(
            tx,
            utxos
        )

    return total_fees


def validate_block(
    block,
    previous_block,
    utxos,
    chain=None
):

    if block["index"] != previous_block["index"] + 1:
        return False, "Invalid block index"

    if block["previous_hash"] != previous_block["hash"]:
        return False, "Invalid previous hash"

    calculated_hash = calculate_block_hash(block)

    if calculated_hash != block["hash"]:
        return False, "Invalid block hash"

    transactions = block["transactions"]

    if not transactions:
        return False, "Block has no transactions"

    if chain is not None:

        difficulty = get_difficulty(
            block["index"],
            chain
        )

    else:

        difficulty = get_difficulty(
            block["index"]
        )

    if not block["hash"].startswith(
        "0" * difficulty
    ):
        return False, "Invalid Proof-of-Work"

    transaction_start = 0

    if transactions[0].get("type") == "coinbase":
        transaction_start = 1

    # Napravi kopiju UTXO seta za validaciju.
    validation_utxos = {
        key: value.copy()
        for key, value in utxos.items()
    }

    total_fees = 0

    # Prvo validiramo normalne transakcije
    # i računamo njihove fee-jeve.
    for transaction in transactions[transaction_start:]:

        if transaction.get("type") != "transaction":
            return False, "Invalid transaction type"

        tx = Transaction(
            inputs=transaction["inputs"],
            outputs=transaction["outputs"],
            public_key=transaction["public_key"],
            signature=transaction["signature"]
        )

        if tx.transaction_hash() != transaction["hash"]:
            return False, "Invalid transaction hash"

        fee = calculate_transaction_fee(
            tx,
            validation_utxos
        )

        valid, reason = validate_transaction(
    tx,
    validation_utxos,
    current_height=block["index"]
)

        if not valid:
            return False, reason

        total_fees += fee

        # Potroši inpute.
        for tx_input in transaction["inputs"]:

            input_id = (
                f"{tx_input['txid']}:"
                f"{tx_input['index']}"
            )

            if input_id not in validation_utxos:
                return False, "Double-spend detected"

            del validation_utxos[input_id]

        # Dodaj outpute.
        txid = transaction["hash"]

        for output_index, output in enumerate(
            transaction["outputs"]
        ):

            output_id = (
                f"{txid}:{output_index}"
            )

            validation_utxos[output_id] = {
                "address": output["address"],
                "amount": output["amount"]
            }

    # Coinbase se provjerava NAKON fee-jeva.
    if transactions[0].get("type") == "coinbase":

        coinbase = transactions[0]

        if not coinbase.get("receiver"):
            return False, "Invalid coinbase receiver"

        subsidy = get_block_reward(
            block["index"]
        )

        maximum_reward = (
            subsidy + total_fees
        )

        coinbase_amount = coinbase.get(
            "amount"
        )

        if not isinstance(
            coinbase_amount,
            int
        ):
            return False, "Invalid coinbase amount"

        if coinbase_amount < 0:
            return False, "Invalid coinbase amount"

        if coinbase_amount > maximum_reward:
            return False, "Coinbase reward exceeds allowed amount"

        coinbase_id = f"{block['hash']}:0"

        validation_utxos[coinbase_id] = {
            "address": coinbase["receiver"],
            "amount": coinbase_amount
        }

    # Sve je validno.
    return True, "Block is valid"
