from wallet import address_from_public_key
from utxo_rules import validate_coinbase_spend

import hashlib
import ecdsa


def verify_transaction_signature(transaction):

    try:

        public_key_bytes = bytes.fromhex(
            transaction.public_key
        )

        verifying_key = ecdsa.VerifyingKey.from_string(
            public_key_bytes,
            curve=ecdsa.SECP256k1
        )

        message_hash = hashlib.sha256(
            transaction.signing_data().encode()
        ).digest()

        signature_bytes = bytes.fromhex(
            transaction.signature
        )

        return verifying_key.verify_digest(
            signature_bytes,
            message_hash
        )

    except Exception:

        return False


def validate_transaction(
    transaction,
    utxos,
    current_height=None
):

    if not transaction.public_key:
        return False, "Missing public key"

    if not transaction.signature:
        return False, "Missing signature"

    sender_address = address_from_public_key(
        transaction.public_key
    )

    if not transaction.inputs:
        return False, "No inputs"

    if not transaction.outputs:
        return False, "No outputs"

    if not verify_transaction_signature(
        transaction
    ):
        return False, "Invalid transaction signature"

    seen_inputs = set()
    total_inputs = 0

    for tx_input in transaction.inputs:

        txid = tx_input.get("txid")
        index = tx_input.get("index")

        if txid is None or index is None:
            return False, "Invalid input"

        input_id = f"{txid}:{index}"

        if input_id in seen_inputs:
            return False, "Duplicate input"

        seen_inputs.add(input_id)

        if input_id not in utxos:
            return False, "UTXO does not exist"

        utxo = utxos[input_id]

        if utxo["address"] != sender_address:
            return False, "UTXO does not belong to signer"

        if tx_input.get("amount") != utxo["amount"]:
            return False, "Input amount mismatch"

        if utxo["amount"] <= 0:
            return False, "Invalid UTXO amount"

        if (
            current_height is not None
            and utxo.get("coinbase")
        ):

            created_height = utxo.get(
                "created_height"
            )

            if created_height is None:
                return False, (
                    "Coinbase UTXO missing "
                    "creation height"
                )

            mature, reason = validate_coinbase_spend(
                current_height,
                created_height
            )

            if not mature:
                return False, reason

        total_inputs += utxo["amount"]

    total_outputs = 0

    for output in transaction.outputs:

        address = output.get("address")
        amount = output.get("amount")

        if not address:
            return False, "Missing output address"

        if not address.startswith("WEED1"):
            return False, "Invalid WEED address"

        if not isinstance(amount, int):
            return False, "Output amount must be integer"

        if amount <= 0:
            return False, "Output amount must be positive"

        total_outputs += amount

    if total_outputs > total_inputs:
        return False, "Outputs exceed inputs"

    return True, "Transaction valid"


def calculate_transaction_fee(
    transaction,
    utxos
):

    total_inputs = 0
    total_outputs = 0

    for tx_input in transaction.inputs:

        input_id = (
            f"{tx_input['txid']}:"
            f"{tx_input['index']}"
        )

        if input_id not in utxos:

            raise ValueError(
                "UTXO does not exist"
            )

        total_inputs += utxos[input_id]["amount"]

    for output in transaction.outputs:

        total_outputs += output["amount"]

    fee = total_inputs - total_outputs

    if fee < 0:

        raise ValueError(
            "Transaction outputs exceed inputs"
        )

    return fee
