import json
import socket
import sys

from mempool import Mempool
from p2p import P2PNode
from transaction_service import accept_transaction, transaction_to_dict

from node import WeedNode


HOST = "127.0.0.1"


def block_to_dict(block):
    return {
        "index": block.index,
        "timestamp": block.timestamp,
        "previous_hash": block.previous_hash,
        "transactions": block.transactions,
        "nonce": block.nonce,
        "hash": block.hash
    }


def handle_request(node, request, mempool=None, p2p=None):
    if mempool is None:
        mempool = Mempool()

    method = request.get("method")

    if method == "get_info":
        return {
            "success": True,
            "height": len(node.chain) - 1,
            "blocks": len(node.chain)
        }

    if method == "get_blockchain":
        return {
            "success": True,
            "blockchain": [
                block_to_dict(block)
                for block in node.chain
            ]
        }

    if method == "get_block":
        index = request.get("index")

        if not isinstance(index, int):
            return {
                "success": False,
                "error": "Invalid block index"
            }

        if index < 0 or index >= len(node.chain):
            return {
                "success": False,
                "error": "Block not found"
            }

        return {
            "success": True,
            "block": block_to_dict(node.chain[index])
        }

    if method == "send_transaction":
        transaction_data = request.get("transaction")

        if not isinstance(transaction_data, dict):
            return {
                "success": False,
                "error": "Missing transaction"
            }

        accepted, reason, txid = accept_transaction(
            node,
            mempool,
            transaction_data
        )

        if accepted and p2p is not None:
            p2p.broadcast({
                "type": "new_transaction",
                "transaction": transaction_data
            })

        return {
            "success": accepted,
            "message": reason,
            "txid": txid
        }

    return {
        "success": False,
        "error": "Unknown method"
    }


def start_server(port):
    node = WeedNode()
    mempool = Mempool()
    p2p = P2PNode(
        [
            {
                "index": block.index,
                "timestamp": block.timestamp,
                "previous_hash": block.previous_hash,
                "transactions": block.transactions,
                "nonce": block.nonce,
                "hash": block.hash
            }
            for block in node.chain
        ],
        host=HOST,
        port=port,
    )
    server = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM
    )
    p2p.start_peer_discovery()

    if port == 7000:
        p2p.add_peer("127.0.0.1", 7001)
    elif port == 7001:
        p2p.add_peer("127.0.0.1", 7000)

    server.setsockopt(
        socket.SOL_SOCKET,
        socket.SO_REUSEADDR,
        1
    )

    server.bind((HOST, port))
    server.listen()

    print()
    print("================================")
    print("          WEED RPC SERVER")
    print("================================")
    print()
    print(f"Listening on {HOST}:{port}")
    print()
    print(f"Blockchain height: {len(node.chain) - 1}")
    print()

    while True:
        connection, address = server.accept()

        try:
            data = connection.recv(65536)

            if not data:
                continue

            request = json.loads(
                data.decode()
            )

            response = handle_request(
                node,
                request,
                mempool,
                p2p,
            )

            connection.sendall(
                json.dumps(response).encode()
            )

        except Exception as error:
            response = {
                "success": False,
                "error": str(error)
            }

            connection.sendall(
                json.dumps(response).encode()
            )

        finally:
            connection.close()


def main():
    if len(sys.argv) != 2:
        print(
            "Usage: python rpc_server.py PORT"
        )
        return

    port = int(sys.argv[1])

    start_server(port)


if __name__ == "__main__":
    main()