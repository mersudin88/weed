from p2p import P2PNode
import sys
import time
import copy

from wallet_storage import load_wallet
from transaction import Transaction
from node import WeedNode, Block
from mempool import Mempool
from transaction_validator import (
    validate_transaction,
    calculate_transaction_fee
)
from consensus import (
    get_block_reward,
    get_difficulty
)
from utxo_rules import is_coinbase_mature


def find_utxos(node, address, amount):

    selected = []
    total = 0

    current_height = node.latest_block().index + 1

    for utxo_id, utxo in node.utxos.items():

        if utxo["address"] != address:
            continue

        if utxo.get("coinbase"):

            created_height = utxo.get(
                "created_height"
            )

            if created_height is None:
                continue

            if not is_coinbase_mature(
                current_height,
                created_height
            ):
                continue

        selected.append(
            (utxo_id, utxo)
        )

        total += utxo["amount"]

        if total >= amount:
            break

    if total < amount:
        return None, 0

    return selected, total


def create_transaction(
    node,
    sender,
    receiver_address,
    amount,
    fee=0
):

    if amount <= 0:
        raise ValueError(
            "Amount must be greater than 0"
        )

    if fee < 0:
        raise ValueError(
            "Fee cannot be negative"
        )

    if not receiver_address.startswith("WEED1"):
        raise ValueError(
            "Invalid WEED address"
        )

    current_height = node.latest_block().index + 1

    required_amount = amount + fee

    selected, total = find_utxos(
        node,
        sender.address,
        required_amount
    )

    if selected is None:
        raise ValueError(
            "Not enough spendable WEED"
        )

    inputs = []

    for utxo_id, utxo in selected:

        txid, index = utxo_id.rsplit(
            ":",
            1
        )

        inputs.append({
            "txid": txid,
            "index": int(index),
            "amount": utxo["amount"]
        })

    outputs = [
        {
            "address": receiver_address,
            "amount": amount
        }
    ]

    change = total - amount - fee

    if change > 0:
        outputs.append({
            "address": sender.address,
            "amount": change
        })

    transaction = Transaction(
        inputs=inputs,
        outputs=outputs,
        public_key=sender.public_key_hex
    )

    transaction.sign(sender)

    valid, reason = validate_transaction(
        transaction,
        node.utxos,
        current_height=current_height
    )

    if not valid:
        raise ValueError(reason)

    actual_fee = calculate_transaction_fee(
        transaction,
        node.utxos
    )

    if actual_fee != fee:
        raise ValueError(
            "Transaction fee mismatch"
        )

    return transaction


def command_address(wallet):

    print("\nWEED address:")
    print(wallet.address)


def command_balance(node, wallet):

    balance = 0

    for utxo in node.utxos.values():

        if utxo["address"] == wallet.address:
            balance += utxo["amount"]

    print("\nBalance:")
    print(balance, "WEED")


def command_send(
    node,
    wallet,
    address,
    amount,
    fee
):

    transaction = create_transaction(
        node,
        wallet,
        address,
        amount,
        fee
    )

    mempool = Mempool()

    mempool.add_transaction(
        transaction
    )

    actual_fee = calculate_transaction_fee(
        transaction,
        node.utxos
    )

    txid = transaction.transaction_hash()

    print(
        "\nTransaction created successfully."
    )

    print("\nTransaction ID:")
    print(txid)

    print("\nAmount:")
    print(amount, "WEED")

    print("\nFee:")
    print(actual_fee, "WEED")

    print("\nTotal input cost:")
    print(amount + actual_fee, "WEED")

    print("\nReceiver:")
    print(address)

    print("\nMempool:")
    print(
        mempool.count(),
        "transaction(s)"
    )

    print(
        "\nTransaction is waiting for mining."
    )
    
def command_status(node):

    p2p = P2PNode(
        node.chain
    )

    p2p.discover_from_peer(
        "127.0.0.1",
        5000
    )

    peers = p2p.get_peers()

    mempool = Mempool()

    latest_block = node.latest_block()

    print("\n================================")
    print("          WEED STATUS")
    print("================================")

    print("\nBlockchain:")
    print("Blocks:", len(node.chain))
    print("Height:", latest_block.index)

    print("\nLatest block:")
    print(latest_block.hash)

    print("\nUTXO:")
    print("UTXOs:", len(node.utxos))

    print("\nMempool:")
    print("Transactions:", mempool.count())

    print("\nP2P:")
    print("Peers:", len(peers))

    for host, port in peers:
        print(f"  {host}:{port}")

    print("\n================================")

def command_peers(node):

    p2p = P2PNode(
        node.chain
    )

    p2p.discover_from_peer(
        "127.0.0.1",
        5000
    )

    peers = p2p.get_peers()

    print("\n================================")
    print("          WEED PEERS")
    print("================================")

    if not peers:
        print("\nNo peers found.")
        print("\nTotal peers: 0")
        return

    print("\nConnected peers:")

    for host, port in peers:
        print(f"\n{host}:{port}")

    print("\nTotal peers:", len(peers))

    


def command_mempool():

    mempool = Mempool()

    print("\n========== MEMPOOL ==========")

    print(
        "\nTransactions:",
        mempool.count()
    )

    for transaction in mempool.get_transactions():

        print()

        print(
            "TXID:",
            transaction.transaction_hash()
        )

    print("\n=============================")


def command_sync(node):

    p2p = P2PNode(node.chain)

    print("\n================================")
    print("          WEED P2P SYNC")
    print("================================")

    print("\nSynchronizing with Node A...")
    print("Peer: 127.0.0.1:5000")

    accepted = p2p.request_chain(
        "127.0.0.1",
        5000
    )

    if not accepted:
        print(
            "\nSynchronization failed "
            "or chain is not longer."
        )
        return

    new_chain = []

    for block_data in p2p.blockchain:

        if isinstance(block_data, Block):
            new_chain.append(block_data)
            continue

        new_block = Block(
            index=block_data["index"],
            timestamp=block_data["timestamp"],
            previous_hash=block_data["previous_hash"],
            transactions=block_data["transactions"],
            nonce=block_data["nonce"],
            hash=block_data["hash"]
        )

        new_chain.append(new_block)

    node.chain = new_chain

    node.rebuild_utxos()
    node.save()

    print("\nSynchronization successful.")
    print("Blocks:", len(node.chain))
    print("Height:", node.latest_block().index)


def apply_transaction_to_utxos(
    transaction_data,
    utxos
):

    for tx_input in transaction_data["inputs"]:

        input_id = (
            f"{tx_input['txid']}:"
            f"{tx_input['index']}"
        )

        if input_id not in utxos:
            return False

        del utxos[input_id]

    txid = transaction_data["hash"]

    for index, output in enumerate(
        transaction_data["outputs"]
    ):

        output_id = (
            f"{txid}:{index}"
        )

        utxos[output_id] = {
            "address": output["address"],
            "amount": output["amount"]
        }

    return True


def command_mine(node, wallet):

    mempool = Mempool()

    print(
        "\nPending transactions:",
        mempool.count()
    )

    temp_utxos = copy.deepcopy(
        node.utxos
    )

    transactions = []
    total_fees = 0

    for transaction in mempool.get_transactions():

        valid, reason = validate_transaction(
            transaction,
            temp_utxos,
            current_height=len(node.chain)
        )

        if not valid:

            print(
                "\nSkipping invalid transaction:"
            )

            print(
                transaction.transaction_hash()
            )

            print(
                "Reason:",
                reason
            )

            continue

        fee = calculate_transaction_fee(
            transaction,
            temp_utxos
        )

        transaction_data = {
            "type": "transaction",
            "hash": transaction.transaction_hash(),
            "inputs": transaction.inputs,
            "outputs": transaction.outputs,
            "public_key": transaction.public_key,
            "signature": transaction.signature
        }

        applied = apply_transaction_to_utxos(
            transaction_data,
            temp_utxos
        )

        if not applied:

            print(
                "\nSkipping double-spend:"
            )

            print(
                transaction.transaction_hash()
            )

            continue

        transactions.append(
            transaction_data
        )

        total_fees += fee

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

    print("\nMining block...")

    block.mine(
            get_difficulty(
            block.index,
            node.chain
        )
    )

    node.chain.append(block)

    node.utxos = temp_utxos

    coinbase_id = f"{block.hash}:0"

    node.utxos[coinbase_id] = {
        "address": wallet.address,
        "amount": miner_reward,
        "coinbase": True,
        "created_height": block.index
    }

    node.save()
    try:

        p2p = P2PNode(
            node.chain
        )

        p2p.discover_from_peer(
            "127.0.0.1",
            5000
        )

        if not p2p.get_peers():

            print(
                "\nNo P2P peers discovered."
            )

            return

        block_data = {
            "index": block.index,
            "timestamp": block.timestamp,
            "previous_hash": block.previous_hash,
            "transactions": block.transactions,
            "nonce": block.nonce,
            "hash": block.hash
        }

        p2p.broadcast_block(
            block_data
        )

        print(
            "\nBlock broadcast through P2P network."
        )

    except Exception as error:

        print("\nP2P block broadcast failed:")
        print(error)

    for transaction_data in transactions:
        txid = transaction_data["hash"]
        mempool.remove_transaction(txid)

    print(
        "\n================================"
    )

    print(
        "          BLOCK MINED"
    )

    print(
        "================================"
    )

    print("\nBlock:")
    print(block.index)

    print("\nHash:")
    print(block.hash)

    print("\nTransactions:")
    print(
        len(transactions),
        "normal transaction(s)"
    )

    print("\nTransaction fees:")
    print(
        total_fees,
        "WEED"
    )

    print("\nBlock subsidy:")
    print(
        subsidy,
        "WEED"
    )

    print("\nMining reward:")
    print(
        miner_reward,
        "WEED"
    )

    print("\nMiner:")
    print(wallet.address)


def command_chain(node):

    print("\n========== BLOCKCHAIN ==========")

    for block in node.chain:

        print()

        print(
            "Block:",
            block.index
        )

        print(
            "Hash:",
            block.hash
        )

        print(
            "Previous:",
            block.previous_hash
        )

        print(
            "Transactions:",
            len(block.transactions)
        )

    print("\n================================")


def command_utxos(node):

    print("\n========== UTXO SET ==========")

    for utxo_id, utxo in node.utxos.items():

        print()

        print(
            "UTXO:",
            utxo_id
        )

        print(
            "Address:",
            utxo["address"]
        )

        print(
            "Amount:",
            utxo["amount"],
            "WEED"
        )

        print(
            "Coinbase:",
            utxo.get("coinbase", False)
        )

        print(
            "Created height:",
            utxo.get(
                "created_height",
                "N/A"
            )
        )

    print("\n==============================")


def print_help():

    print()

    print(
        "================================"
    )

    print(
        "             WEED CLI"
    )

    print(
        "================================"
    )

    print()

    print("Commands:")

    print()

    print(
        "  python cli.py address"
    )

    print(
        "  python cli.py balance"
    )

    print(
        "  python cli.py send ADDRESS AMOUNT [FEE]"
    )

    print(
        "  python cli.py mempool"
    )

    print(
        "  python cli.py mine"
    )

    print(
        "  python cli.py chain"
    )

    print(
        "  python cli.py utxos"
    )

    print(
        "  python cli.py sync"
    )


def main():

    wallet = load_wallet()

    node = WeedNode()

    if len(sys.argv) < 2:

        print_help()

        return

    command = sys.argv[1].lower()

    try:

        if command == "address":

            command_address(
                wallet
            )

        elif command == "balance":

            command_balance(
                node,
                wallet
            )

        elif command == "send":

            if len(sys.argv) not in (4, 5):

                print("Usage:")

                print(
                    "python cli.py send "
                    "ADDRESS AMOUNT [FEE]"
                )

                return

            address = sys.argv[2]

            amount = int(
                sys.argv[3]
            )

            fee = 0

            if len(sys.argv) == 5:

                fee = int(
                    sys.argv[4]
                )

            command_send(
                node,
                wallet,
                address,
                amount,
                fee
            )

        elif command == "mempool":

            command_mempool()

        elif command == "peers":
            command_peers(node) 

        elif command == "status":
             command_status(node)       

        elif command == "mine":

            command_mine(
                node,
                wallet
            )

        elif command == "chain":

            command_chain(
                node
            )

        elif command == "utxos":

            command_utxos(
                node
            )

        elif command == "sync":

            command_sync(
                node
            )

        else:

            print_help()

    except ValueError as error:

        print("\nERROR:")
        print(error)


if __name__ == "__main__":

    main()