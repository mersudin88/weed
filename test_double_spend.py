import copy

from node import WeedNode
from wallet_storage import load_wallet
from cli import create_transaction
from transaction_validator import validate_transaction


def main():

    print("================================")
    print("       WEED DOUBLE-SPEND TEST")
    print("================================")

    node = WeedNode()
    wallet = load_wallet()

    # Napravi prvu transakciju.
    tx1 = create_transaction(
        node,
        wallet,
        "WEED162bb8f78b8d7b6e94a5d2cf853767f4329bf56e3",
        5,
        0
    )

    print()
    print("Transaction 1:")
    print(tx1.transaction_hash())

    valid, reason = validate_transaction(
        tx1,
        node.utxos
    )

    print("VALID =", valid)
    print("Reason =", reason)

    if not valid:
        raise SystemExit(
            "Transaction 1 should be valid"
        )

    # Napravi kopiju istog inputa.
    # To simulira pokušaj potrošnje istog UTXO-a
    # kroz drugu transakciju.
    tx2 = copy.deepcopy(tx1)

    # Promijeni output tako da dobije drugi TXID,
    # ali input ostane isti.
    tx2.outputs = [
        {
            "address": wallet.address,
            "amount": 5
        }
    ]

    # Ponovo potpiši izmijenjenu transakciju.
    tx2.signature = None
    tx2.sign(wallet)

    print()
    print("Transaction 2:")
    print(tx2.transaction_hash())

    valid, reason = validate_transaction(
        tx2,
        node.utxos
    )

    print("VALID =", valid)
    print("Reason =", reason)

    if not valid:
        raise SystemExit(
            "Transaction 2 should initially be valid "
            "against the untouched UTXO set"
        )

    # Sada simuliramo potvrđivanje prve transakcije:
    # potrošeni UTXO uklanjamo iz UTXO seta.
    spent_utxos = {
        key: value.copy()
        for key, value in node.utxos.items()
    }

    for tx_input in tx1.inputs:

        input_id = (
            f"{tx_input['txid']}:"
            f"{tx_input['index']}"
        )

        del spent_utxos[input_id]

    print()
    print("Trying Transaction 2 after")
    print("Transaction 1 spent the UTXO...")

    valid, reason = validate_transaction(
        tx2,
        spent_utxos
    )

    print()
    print("Transaction 2 after TX1:")
    print("VALID =", valid)
    print("Reason =", reason)

    if valid:
        raise SystemExit(
            "ERROR: Double-spend was accepted!"
        )

    print()
    print("================================")
    print("     DOUBLE-SPEND REJECTED")
    print("================================")


if __name__ == "__main__":
    main()
