import json
import socket
import threading

from chain_validator import validate_chain

BUFFER_SIZE = 65536
DISCOVERY_INTERVAL = 30


class P2PNode:

    def __init__(
        self,
        blockchain,
        host="127.0.0.1",
        port=None
    ):

        self.blockchain = blockchain
        self.host = host
        self.port = port
        self.peers = []
        self.lock = threading.Lock()

    def add_peer(self, host, port):

        peer = (host, port)

        # Never add ourselves as a peer
        if self.port is not None:
            if peer == (self.host, self.port):
                return

        with self.lock:

            if peer not in self.peers:

                self.peers.append(peer)

                print()
                print("Peer added:")
                print(f"{host}:{port}")

    def remove_peer(self, host, port):

        peer = (host, port)

        with self.lock:

            if peer in self.peers:
                self.peers.remove(peer)

    def get_peers(self):

        with self.lock:
            return list(self.peers)

    def discover_peers(self, host, port):

        try:

            connection = socket.socket(
                socket.AF_INET,
                socket.SOCK_STREAM
            )

            connection.settimeout(5)

            connection.connect(
                (host, port)
            )

            message = {
                "type": "get_peers"
            }

            connection.sendall(
                json.dumps(message).encode()
            )

            data = connection.recv(
                BUFFER_SIZE
            )

            if not data:

                connection.close()
                return

            response = json.loads(
                data.decode()
            )

            if response.get("type") != "peers":

                connection.close()
                return

            peers = response.get(
                "peers",
                []
            )

            for peer in peers:

                peer_host = peer[0]
                peer_port = int(peer[1])

                if (
                    peer_host == host
                    and peer_port == port
                ):
                    continue

                before = self.get_peers()

                self.add_peer(
                    peer_host,
                    peer_port
                )

                if (
                    peer_host,
                    peer_port
                ) not in before:

                    self.share_peer(
                        peer_host,
                        peer_port
                    )

            connection.close()

        except Exception as error:

            print()
            print("Peer discovery failed:")
            print(error)

    def start_peer_discovery(self):

        def discovery_loop():

            while True:

                peers = self.get_peers()

                for host, port in peers:

                    self.discover_peers(
                        host,
                        port
                    )

                threading.Event().wait(
                    DISCOVERY_INTERVAL
                )

        thread = threading.Thread(
            target=discovery_loop,
            daemon=True
        )

        thread.start()

    def share_peer(self, host, port):

        message = {
            "type": "new_peer",
            "peer": [host, port]
        }

        self.broadcast(
            message
        )

    def receive_chain(self, chain):

        valid, reason = validate_chain(
            chain
        )

        if not valid:

            print()
            print("Rejected blockchain:")
            print(reason)

            return False

        if len(chain) <= len(
            self.blockchain
        ):

            print()
            print("Received chain is not longer.")

            return False

        self.blockchain = chain

        print()
        print("New blockchain accepted.")
        print("Blocks:", len(self.blockchain))

        return True

    def request_chain(
        self,
        host,
        port
    ):

        self.add_peer(
            host,
            port
        )

        connection = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM
        )

        connection.settimeout(10)

        try:

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

            if not data:
                return False

            message = json.loads(
                data.decode()
            )

            if message.get(
                "type"
            ) == "chain":

                return self.receive_chain(
                    message["chain"]
                )

            return False

        except Exception as error:

            print()
            print("Connection error:")
            print(error)

            return False

        finally:

            connection.close()

    def broadcast(
        self,
        message
    ):

        encoded = json.dumps(
            message
        ).encode()

        peers = self.get_peers()

        print()
        print(
            "Broadcasting to",
            len(peers),
            "peer(s)..."
        )

        for host, port in peers:

            try:

                connection = socket.socket(
                    socket.AF_INET,
                    socket.SOCK_STREAM
                )

                connection.settimeout(5)

                connection.connect(
                    (host, port)
                )

                connection.sendall(
                    encoded
                )

                connection.close()

                print(
                    f"Sent to {host}:{port}"
                )

            except Exception as error:

                print(
                    f"Failed {host}:{port}:",
                    error
                )

                self.remove_peer(
                    host,
                    port
                )

    def broadcast_transaction(self, transaction):

        message = {
            "type": "new_transaction",
            "transaction": transaction
        }

        self.broadcast(message)

    def broadcast_block(self, block):

        message = {
            "type": "new_block",
            "block": block
        }

        self.broadcast(message)

    def discover_from_peer(self, host, port):

        try:

            connection = socket.socket(
                socket.AF_INET,
                socket.SOCK_STREAM
            )

            connection.settimeout(5)

            connection.connect(
                (host, port)
            )

            message = {
                "type": "get_peers"
            }

            connection.sendall(
                json.dumps(message).encode()
            )

            data = connection.recv(
                BUFFER_SIZE
            )

            connection.close()

            if not data:
                return False

            response = json.loads(
                data.decode()
            )

            if response.get("type") != "peers":
                return False

            for peer in response.get("peers", []):

                peer_host = peer[0]
                peer_port = int(peer[1])

                self.add_peer(
                    peer_host,
                    peer_port
                )

            return True

        except Exception as error:

            print()
            print("Peer discovery failed:")
            print(error)

            return False
if __name__ == "__main__":

    print("P2P module loaded.")