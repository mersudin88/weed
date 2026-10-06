from node import WeedNode
from wallet_storage import load_wallet


def rebuild_utxos_until(node, block_count):

    utxos = {}

    for block in node.chain[:block_count]:

        for transaction in block.transactions:

            if transaction.get("type") == "coinbase":

                utxo_id = f"{block.hash}:0"

                utxos[utxo_id] = {
                    "address": transaction["receiver"],
                    "amount": transaction["amount"]
                }

                continue

            if transaction.get("type") != "transaction":
                continue

            for tx_input in transaction["inputs"]:

                input_id = (
                    f"{tx_input['txid']}:"
                    f"{tx_input['index']}"
                )

                if input_id in utxos:
                    del utxos[input_id]

            txid = transaction["hash"]

            for index, output in enumerate(
                transaction["outputs"]
            ):

                output_id = f"{txid}:{index}"

                utxos[output_id] = {
                    "address": output["address"],
                    "amount": output["amount"]
                }

    return utxos


def main():

    node = WeedNode()

    if len(node.chain) < 2:

        print("Nothing to repair.")
        return

    block = node.chain[-1]

    print()
    print("================================")
    print("       WEED CHAIN REPAIR")
    print("================================")

    print("\nChecking block:", block.index)

    # UTXO stanje PRIJE zadnjeg bloka
    previous_utxos = rebuild_utxos_until(
        node,
        len(node.chain) - 1
    )

    valid_transactions = []

    # Coinbase uvijek ostaje
    for transaction in block.transactions:

        if transaction.get("type") == "coinbase":

            valid_transactions.append(transaction)

            continue

        if transaction.get("type") != "transaction":

            continue

        valid = True

        for tx_input in transaction["inputs"]:

            input_id = (
                f"{tx_input['txid']}:"
                f"{tx_input['index']}"
            )

            # Ako UTXO više ne postoji,
            # transakcija je double-spend ili nevažeća
            if input_id not in previous_utxos:

                valid = False

                print()
                print("INVALID TRANSACTION")
                print("TXID:")
                print(transaction["hash"])
                print()
                print("Spent UTXO:")
                print(input_id)
                print()
                print("Reason:")
                print("Double-spend / UTXO does not exist")

                break

        if valid:

            valid_transactions.append(transaction)

            # Privremeno potroši UTXO
            for tx_input in transaction["inputs"]:

                input_id = (
                    f"{tx_input['txid']}:"
                    f"{tx_input['index']}"
                )

                if input_id in previous_utxos:
                    del previous_utxos[input_id]

            # Dodaj nove UTXO-e
            txid = transaction["hash"]

            for index, output in enumerate(
                transaction["outputs"]
            ):

                output_id = f"{txid}:{index}"

                previous_utxos[output_id] = {
                    "address": output["address"],
                    "amount": output["amount"]
                }

    removed = len(block.transactions) - len(valid_transactions)

    block.transactions = valid_transactions

    # Ponovo mine-amo popravljeni block
    block.nonce = 0
    block.hash = ""

    print()
    print("Removed transactions:", removed)
    print("Remaining transactions:", len(block.transactions))

    print()
    print("Re-mining repaired block...")

    block.mine()

    # Ponovo izgradi kompletan UTXO set
    node.rebuild_utxos()

    node.save()

    wallet = load_wallet()

    print()
    print("================================")
    print("       REPAIR COMPLETE")
    print("================================")

    print()
    print("New block hash:")
    print(block.hash)

    print()
    print("Wallet balance:")
    print(node.get_balance(wallet.address), "WEED")


if __name__ == "__main__":
    main()
