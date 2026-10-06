import sys
import time

from node import WeedNode, Block
from wallet_storage import load_wallet
from mempool import Mempool
from transaction_validator import (
    validate_transaction,
    calculate_transaction_fee
)
from p2p import P2PNode
from consensus import get_block_reward, get_difficulty
from block_validator import validate_block


def blockchain_to_dict(node):

    return [
        {
            "index": block.index,
            "timestamp": block.timestamp,
            "previous_hash": block.previous_hash,
            "transactions": block.transactions,
            "nonce": block.nonce,
            "hash": block.hash
        }
        for block in node.chain
    ]


def transaction_to_dict(transaction):

    return {
        "type": "transaction",
        "hash": transaction.transaction_hash(),
        "inputs": transaction.inputs,
        "outputs": transaction.outputs,
        "public_key": transaction.public_key,
        "signature": transaction.signature
    }


def main():

    if len(sys.argv) != 2:

        print("Usage: python p2p_mine.py PORT")

        return

    port = int(sys.argv[1])

    node = WeedNode()
    wallet = load_wallet()
    mempool = Mempool()

    p2p = P2PNode(
        blockchain_to_dict(node)
    )

    if port == 5000:

        p2p.add_peer(
            "127.0.0.1",
            5001
        )

    elif port == 5001:

        p2p.add_peer(
            "127.0.0.1",
            5000
        )

    transactions = []

    total_fees = 0

    temp_utxos = {
        key: value.copy()
        for key, value in node.utxos.items()
    }

    for transaction in mempool.get_transactions():

        valid, reason = validate_transaction(
    transaction,
    temp_utxos,
    current_height=len(node.chain)
)

        if not valid:

            print()
            print("Skipping invalid transaction:")
            print(transaction.transaction_hash())
            print(reason)

            continue

        transaction_valid = True

        for tx_input in transaction.inputs:

            input_id = (
                f"{tx_input['txid']}:"
                f"{tx_input['index']}"
            )

            if input_id not in temp_utxos:

                print()
                print("Skipping double-spend:")
                print(
                    transaction.transaction_hash()
                )

                transaction_valid = False

                break

        if not transaction_valid:

            continue

        fee = calculate_transaction_fee(
            transaction,
            temp_utxos
        )

        total_fees += fee

        for tx_input in transaction.inputs:

            input_id = (
                f"{tx_input['txid']}:"
                f"{tx_input['index']}"
            )

            del temp_utxos[input_id]

        tx_data = transaction_to_dict(
            transaction
        )

        transactions.append(
            tx_data
        )

        txid = transaction.transaction_hash()

        for output_index, output in enumerate(
            transaction.outputs
        ):

            output_id = (
                f"{txid}:{output_index}"
            )

            temp_utxos[output_id] = {
                "address": output["address"],
                "amount": output["amount"]
            }

    subsidy = get_block_reward(
        len(node.chain)
    )

    miner_reward = (
        subsidy + total_fees
    )

    reward = {
        "type": "coinbase",
        "receiver": wallet.address,
        "amount": miner_reward
    }

    block_transactions = [
        reward
    ] + transactions

    block = Block(
        index=len(node.chain),
        timestamp=time.time(),
        previous_hash=node.latest_block().hash,
        transactions=block_transactions
    )

    print()
    print("================================")
    print("       WEED P2P MINING")
    print("================================")

    print()
    print("Block:")
    print(block.index)

    print()
    print("Transactions:")
    print(len(transactions))

    print()
    print("Transaction fees:")
    print(total_fees, "WEED")

    print()
    print("Block subsidy:")
    print(subsidy, "WEED")

    print()
    print("Miner reward:")
    print(miner_reward, "WEED")

    print()
    print("Mining...")

    block.mine(
        get_difficulty(
            block.index,
            node.chain
        )
    )

    block_data = {
        "index": block.index,
        "timestamp": block.timestamp,
        "previous_hash": block.previous_hash,
        "transactions": block.transactions,
        "nonce": block.nonce,
        "hash": block.hash
    }

    previous_block = {
        "index": node.latest_block().index,
        "timestamp": node.latest_block().timestamp,
        "previous_hash": node.latest_block().previous_hash,
        "transactions": node.latest_block().transactions,
        "nonce": node.latest_block().nonce,
        "hash": node.latest_block().hash
    }

    validation_utxos = {
        key: value.copy()
        for key, value in node.utxos.items()
    }

    valid, reason = validate_block(
        block_data,
        previous_block,
        validation_utxos,
        node.chain
    )

    if not valid:

        print()
        print("BLOCK REJECTED")
        print(reason)

        return

    node.chain.append(block)

    node.rebuild_utxos()

    node.save()

    confirmed_txids = {
        tx["hash"]
        for tx in transactions
    }

    for transaction in mempool.get_transactions():

        if transaction.transaction_hash() in confirmed_txids:

            mempool.remove_transaction(
                transaction.transaction_hash()
            )

    print()
    print("================================")
    print("          BLOCK ACCEPTED")
    print("================================")

    print()
    print("Block:")
    print(block.index)

    print()
    print("Hash:")
    print(block.hash)

    print()
    print("Transactions:")
    print(len(transactions))

    print()
    print("Transaction fees:")
    print(total_fees, "WEED")

    print()
    print("Block subsidy:")
    print(subsidy, "WEED")

    print()
    print("Mining reward:")
    print(miner_reward, "WEED")

    print()
    print("Broadcasting block...")

    p2p.broadcast({
        "type": "new_block",
        "block": block_data
    })

    print()
    print("Block broadcast complete.")


if __name__ == "__main__":

    main()
