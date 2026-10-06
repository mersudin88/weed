from wallet_storage import load_wallet
from wallet import Wallet
from transaction import Transaction
from node import WeedNode, Block
from mempool import Mempool

import time


def main():

    print()
    print("================================")
    print("       WEED MEMPOOL MINER")
    print("================================")

    node = WeedNode()
    mempool = Mempool()

    sender = load_wallet()
    receiver = Wallet()

    amount = 30

    selected_utxo = None

    for utxo_id, utxo in node.utxos.items():

        if utxo["address"] == sender.address:

            selected_utxo = {
                "id": utxo_id,
                "amount": utxo["amount"]
            }

            break

    if selected_utxo is None:

        print("\nNo spendable UTXO found.")

        return

    txid, index = selected_utxo["id"].rsplit(":", 1)

    change = selected_utxo["amount"] - amount

    transaction = Transaction(
        inputs=[
            {
                "txid": txid,
                "index": int(index),
                "amount": selected_utxo["amount"]
            }
        ],
        outputs=[
            {
                "address": receiver.address,
                "amount": amount
            },
            {
                "address": sender.address,
                "amount": change
            }
        ],
        public_key=sender.public_key_hex
    )

    transaction.sign(sender)

    print("\nTransaction:")
    print(transaction.transaction_hash())

    print("\nSignature valid:")
    print(transaction.verify_signature(sender))

    mempool.add_transaction(transaction)

    print("\nMempool:")
    print(mempool.count(), "transaction")

    tx_data = {
        "type": "transaction",
        "hash": transaction.transaction_hash(),
        "inputs": transaction.inputs,
        "outputs": transaction.outputs,
        "public_key": transaction.public_key,
        "signature": transaction.signature
    }

    block = Block(
        index=len(node.chain),
        timestamp=time.time(),
        previous_hash=node.latest_block().hash,
        transactions=[tx_data]
    )

    print("\nMining transaction block...")

    block.mine()

    node.chain.append(block)

    # Remove spent UTXO
    for tx_input in transaction.inputs:

        input_id = (
            f"{tx_input['txid']}:"
            f"{tx_input['index']}"
        )

        if input_id in node.utxos:

            del node.utxos[input_id]

    # Create new UTXOs
    transaction_id = transaction.transaction_hash()

    for output_index, output in enumerate(
        transaction.outputs
    ):

        output_id = (
            f"{transaction_id}:"
            f"{output_index}"
        )

        node.utxos[output_id] = {
            "address": output["address"],
            "amount": output["amount"]
        }

    mempool.clear()

    node.save()

    print("\n================================")
    print("       TRANSACTION MINED")
    print("================================")

    print("\nSender:")
    print(sender.address)

    print("\nSender balance:")
    print(
        node.get_balance(sender.address),
        "WEED"
    )

    print("\nReceiver:")
    print(receiver.address)

    print("\nReceiver balance:")
    print(
        node.get_balance(receiver.address),
        "WEED"
    )

    print("\nNew block:")
    print(block.hash)

    print("\nBlockchain saved.")


if __name__ == "__main__":

    main()
