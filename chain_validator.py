import hashlib
import json

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


def validate_chain(chain):

    if not chain:
        return False, "Blockchain is empty"

    utxos = {}

    for index, block in enumerate(chain):

        if block["index"] != index:
            return False, (
                f"Invalid block index at block {index}"
            )

        calculated_hash = calculate_block_hash(block)

        if calculated_hash != block["hash"]:
            return False, (
                f"Invalid hash at block {index}"
            )

        if index == 0:

            if block["previous_hash"] != "0":
                return False, (
                    "Genesis block has invalid previous hash"
                )

        else:

            previous_block = chain[index - 1]

            if block["previous_hash"] != previous_block["hash"]:
                return False, (
                    f"Invalid previous hash at block {index}"
                )

            difficulty = get_difficulty(
                block["index"],
                chain
            )

            if not block["hash"].startswith(
                "0" * difficulty
            ):
                return False, (
                    f"Invalid Proof-of-Work at block {index}"
                )

        transactions = block["transactions"]

        if not transactions:
            continue

        transaction_start = 0
        total_fees = 0

        # Coinbase je opcionalan.
        # Ako postoji, privremeno ga preskačemo
        # dok ne izračunamo fees iz običnih transakcija.
        if transactions[0].get("type") == "coinbase":

            coinbase = transactions[0]

            if not coinbase.get("receiver"):
                return False, (
                    f"Invalid coinbase receiver at block {index}"
                )

            coinbase_amount = coinbase.get("amount")

            if not isinstance(
                coinbase_amount,
                int
            ):
                return False, (
                    f"Invalid coinbase amount at block {index}"
                )

            if coinbase_amount < 0:
                return False, (
                    f"Invalid coinbase amount at block {index}"
                )

            transaction_start = 1

        # Validiraj sve obične transakcije
        # i obračunaj njihove fees.
        for transaction in transactions[transaction_start:]:

            if transaction.get("type") != "transaction":
                return False, (
                    f"Invalid transaction type in block {index}"
                )

            tx = Transaction(
                inputs=transaction["inputs"],
                outputs=transaction["outputs"],
                public_key=transaction["public_key"],
                signature=transaction["signature"]
            )

            if tx.transaction_hash() != transaction["hash"]:
                return False, (
                    f"Invalid transaction hash in block {index}"
                )

            fee = calculate_transaction_fee(
                tx,
                utxos
            )

            valid, reason = validate_transaction(
    tx,
    utxos,
    current_height=index
)

            if not valid:
                return False, (
                    f"Invalid transaction in block {index}: "
                    f"{reason}"
                )

            total_fees += fee

            # Potroši input UTXO-e.
            for tx_input in transaction["inputs"]:

                input_id = (
                    f"{tx_input['txid']}:"
                    f"{tx_input['index']}"
                )

                if input_id not in utxos:
                    return False, (
                        f"Double-spend in block {index}"
                    )

                del utxos[input_id]

            # Dodaj output UTXO-e.
            txid = transaction["hash"]

            for output_index, output in enumerate(
                transaction["outputs"]
            ):

                output_id = (
                    f"{txid}:{output_index}"
                )

                utxos[output_id] = {
                    "address": output["address"],
                    "amount": output["amount"]
                }

        # Sada možemo provjeriti coinbase,
        # jer znamo koliko fees blok sadrži.
        if transaction_start == 1:

            coinbase = transactions[0]

            subsidy = get_block_reward(
                block["index"]
            )

            maximum_reward = (
                subsidy + total_fees
            )

            coinbase_amount = coinbase["amount"]

            if coinbase_amount > maximum_reward:
                return False, (
                    f"Invalid block reward at block {index}: "
                    f"maximum allowed is "
                    f"{maximum_reward}, "
                    f"got {coinbase_amount}"
                )

            coinbase_id = f"{block['hash']}:0"

            utxos[coinbase_id] = {
                "address": coinbase["receiver"],
                "amount": coinbase_amount
            }

    return True, "Blockchain is valid"


def main():

    with open(
        "blockchain.json",
        "r",
        encoding="utf-8"
    ) as file:

        chain = json.load(file)

    valid, reason = validate_chain(chain)

    print()
    print("================================")
    print("       WEED CHAIN VALIDATOR")
    print("================================")

    print()
    print("Valid:", valid)

    print()
    print("Result:")
    print(reason)


if __name__ == "__main__":
    main()
