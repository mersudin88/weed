import json
import socket

from chain_validator import validate_chain


HOST = "127.0.0.1"
PORT = 5000


def main():

    print()
    print("================================")
    print("        WEED P2P SYNC TEST")
    print("================================")

    connection = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM
    )

    connection.connect(
        (HOST, PORT)
    )

    message = {
        "type": "get_chain"
    }

    connection.sendall(
        json.dumps(message).encode()
    )

    data = connection.recv(65536)

    connection.close()

    response = json.loads(
        data.decode()
    )

    print()
    print("Message received:")
    print(response["type"])

    chain = response["chain"]

    print()
    print("Blocks received:")
    print(len(chain))

    valid, reason = validate_chain(
        chain
    )

    print()

    if valid:

        print("CHAIN VALID")
        print(reason)

    else:

        print("CHAIN INVALID")
        print(reason)


if __name__ == "__main__":
    main()
