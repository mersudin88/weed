import sys
import threading
import json
import socket

from node import WeedNode, Block
from mempool import Mempool
from transaction import Transaction
from transaction_validator import validate_transaction
from block_validator import validate_block
from p2p import P2PNode


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


def apply_chain_to_node(node, chain):
    new_chain = []

    for block_data in chain:
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

    print()
    print("Local blockchain synchronized.")
    print("Blocks:", len(node.chain))
    print("Height:", node.chain[-1].index)


def main():
    if len(sys.argv) != 2:
        print("Usage: python p2p_server.py PORT")
        return

    port = int(sys.argv[1])

    node = WeedNode()
    mempool = Mempool()

    p2p = P2PNode(
        blockchain_to_dict(node),
        host="127.0.0.1",
        port=port,
    )

    p2p.start_peer_discovery()

    if port == 5000:
        p2p.add_peer("127.0.0.1", 5001)
        synced = p2p.request_chain("127.0.0.1", 5001)
        if synced:
            apply_chain_to_node(node, p2p.blockchain)

    elif port == 5001:
        p2p.add_peer("127.0.0.1", 5000)
        synced = p2p.request_chain("127.0.0.1", 5000)
        if synced:
            apply_chain_to_node(node, p2p.blockchain)

    def handle_transaction(data):
        transaction = Transaction(
            inputs=data["inputs"],
            outputs=data["outputs"],
            public_key=data["public_key"],
            signature=data["signature"]
        )

        txid = transaction.transaction_hash()

        for existing in mempool.get_transactions():
            if existing.transaction_hash() == txid:
                print()
                print("Transaction already known.")
                return

        valid, reason = validate_transaction(
            transaction,
            node.utxos,
            current_height=node.chain[-1].index + 1
        )

        if not valid:
            print()
            print("Transaction rejected:")
            print(reason)
            return

        try:
            mempool.add_transaction(transaction)
        except ValueError as error:
            print()
            print("Transaction rejected:")
            print(error)
            return

        print()
        print("Transaction accepted:")
        print(txid)

        p2p.broadcast({
            "type": "new_transaction",
            "transaction": transaction_to_dict(transaction)
        })

    def handle_block(block):
        print()
        print("Received block:")
        print(block["index"])

        if block["index"] < len(node.chain):
            local_block = node.chain[block["index"]]

            if local_block.hash == block["hash"]:
                print()
                print("Block already known.")
                return

            print()
            print("Block rejected:")
            print("Conflicting block at same height.")
            return

        if block["index"] > len(node.chain):
            print()
            print("Block rejected:")
            print("Unexpected future block index.")
            return

        previous_block = node.chain[-1]

        previous_block_data = {
            "index": previous_block.index,
            "timestamp": previous_block.timestamp,
            "previous_hash": previous_block.previous_hash,
            "transactions": previous_block.transactions,
            "nonce": previous_block.nonce,
            "hash": previous_block.hash
        }

        validation_utxos = {
            key: value.copy()
            for key, value in node.utxos.items()
        }

        valid, reason = validate_block(
            block,
            previous_block_data,
            validation_utxos,
            node.chain
        )

        if not valid:
            print()
            print("Block rejected:")
            print(reason)
            return

        new_block = Block(
            index=block["index"],
            timestamp=block["timestamp"],
            previous_hash=block["previous_hash"],
            transactions=block["transactions"],
            nonce=block["nonce"],
            hash=block["hash"]
        )

        node.chain.append(new_block)
        node.rebuild_utxos()
        node.save()

        for transaction in block["transactions"]:
            if transaction.get("type") != "transaction":
                continue

            txid = transaction["hash"]
            mempool.remove_transaction(txid)

        print()
        print("Block accepted:")
        print(block["index"])

        p2p.blockchain = blockchain_to_dict(node)

        p2p.broadcast({
            "type": "new_block",
            "block": block
        })

    def handle_peer(connection, address):
        try:
            data = connection.recv(65536)

            if not data:
                return

            message = json.loads(data.decode())
            message_type = message.get("type")

            print()
            print("Peer connected:")
            print(address)

            print()
            print("Received message:")
            print(message_type)

            if message_type == "new_transaction":
                handle_transaction(message["transaction"])

            elif message_type == "new_block":
                handle_block(message["block"])

            elif message_type == "get_chain":
                response = {
                    "type": "chain",
                    "chain": blockchain_to_dict(node)
                }

                connection.sendall(json.dumps(response).encode())

            elif message_type == "chain":
                received_chain = message["chain"]

                if len(received_chain) > len(node.chain):
                    valid = p2p.receive_chain(received_chain)

                    if valid:
                        apply_chain_to_node(node, p2p.blockchain)
                        print()
                        print("Chain synchronization complete.")

            elif message_type == "get_peers":
                peers = p2p.get_peers()

                response = {
                    "type": "peers",
                    "peers": peers
                }

                connection.sendall(json.dumps(response).encode())

            elif message_type == "peers":
                peers = message.get("peers", [])
                if peers:
                    for host, port_ in peers:
                        p2p.add_peer(host, port_)

        except Exception as error:
            print(error)

        finally:
            connection.close()

    def server_loop():
        server = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM
        )

        server.setsockopt(
            socket.SOL_SOCKET,
            socket.SO_REUSEADDR,
            1
        )

        server.bind(
            ("127.0.0.1", port)
        )

        server.listen()

        print()
        print("================================")
        print("          WEED P2P NODE")
        print("================================")
        print()

        print("Listening on:")
        print(f"127.0.0.1:{port}")

        print()
        print("Blocks:")
        print(len(node.chain))

        print()
        print("Mempool:")
        print(mempool.count())

        print()
        print("Peers:")

        for peer in p2p.get_peers():
            print(
                f"{peer[0]}:{peer[1]}"
            )

        while True:
            connection, address = server.accept()

            thread = threading.Thread(
                target=handle_peer,
                args=(connection, address),
                daemon=True
            )

            thread.start()

    server_loop()


if __name__ == "__main__":
    main()