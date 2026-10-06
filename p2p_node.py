import json
import socket
import sys

from chain_validator import validate_chain
from storage import save_json


BUFFER_SIZE = 65536


def load_chain(filename):

    with open(
        filename,
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)


def request_chain(host, port):

    connection = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM
    )

    connection.settimeout(10)

    print()
    print("Connecting to peer:")
    print(f"{host}:{port}")

    connection.connect(
        (host, port)
    )

    message = {
        "type": "get_chain"
    }

    connection.sendall(
        json.dumps(message).encode()
    )

    data = connection.recv(
        BUFFER_SIZE
    )

    connection.close()

    response = json.loads(
        data.decode()
    )

    if response.get("type") != "chain":

        raise ValueError(
            "Peer did not send blockchain"
        )

    return response["chain"]


def main():

    if len(sys.argv) != 4:

        print(
            "Usage:"
        )

        print(
            "python p2p_node.py HOST PORT BLOCKCHAIN_FILE"
        )

        return

    host = sys.argv[1]
    port = int(sys.argv[2])
    blockchain_file = sys.argv[3]

    local_chain = load_chain(
        blockchain_file
    )

    print()
    print("================================")
    print("        WEED P2P SYNC")
    print("================================")

    print()
    print("Local blocks:")
    print(len(local_chain))

    remote_chain = request_chain(
        host,
        port
    )

    print()
    print("Remote blocks:")
    print(len(remote_chain))

    valid, reason = validate_chain(
        remote_chain
    )

    if not valid:

        print()
        print("REMOTE CHAIN REJECTED")
        print(reason)

        return

    print()
    print("Remote chain is valid.")

    if len(remote_chain) <= len(local_chain):

        print()
        print(
            "Local chain is already equal or longer."
        )

        return

    save_json(
        blockchain_file,
        remote_chain
    )

    print()
    print("================================")
    print("       CHAIN SYNCHRONIZED")
    print("================================")

    print()
    print("Old blocks:")
    print(len(local_chain))

    print()
    print("New blocks:")
    print(len(remote_chain))


if __name__ == "__main__":
    main()
