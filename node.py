import json
import hashlib
import time
from dataclasses import dataclass

from storage import save_json, load_json
from consensus import (
    get_block_reward,
    get_difficulty,
    MERKLE_ACTIVATION_HEIGHT
)
from merkle import merkle_root

import os


BLOCKCHAIN_FILE = os.path.join(
    os.environ.get(
        "WEED_DATA_DIR",
        "."
    ),
    "blockchain.json"
)


@dataclass
class Block:
    index: int
    timestamp: float
    previous_hash: str
    transactions: list
    nonce: int = 0
    hash: str = ""

    def merkle_root(self):

        transaction_data = [
            json.dumps(
                transaction,
                sort_keys=True,
                separators=(",", ":")
            )
            for transaction in self.transactions
        ]

        return merkle_root(
            transaction_data
        )

    def calculate_hash(self, use_merkle=True):

        data = {
            "index": self.index,
            "timestamp": self.timestamp,
            "previous_hash": self.previous_hash,
            "transactions": self.transactions,
            "nonce": self.nonce
        }


        if use_merkle:
            data["merkle_root"] = self.merkle_root()

        encoded = json.dumps(
            data,
            sort_keys=True,
            separators=(",", ":")
        ).encode()

        return hashlib.sha256(
            encoded
        ).hexdigest()
        def calculate_hash(self, use_merkle=True):

            data = {
            "index": self.index,
            "timestamp": self.timestamp,
            "previous_hash": self.previous_hash,
            "transactions": self.transactions,
            "nonce": self.nonce
        }

        if use_merkle:

            data["merkle_root"] = self.merkle_root()

        encoded = json.dumps(
            data,
            sort_keys=True,
            separators=(",", ":")
        ).encode()

        return hashlib.sha256(
            encoded
        ).hexdigest()

    def mine(self, difficulty):

        target = "0" * difficulty

        print(
            f"Mining block #{self.index}..."
        )

        while True:

            self.hash = self.calculate_hash(
    use_merkle=self.index >= MERKLE_ACTIVATION_HEIGHT
)

            if self.hash.startswith(target):

                print("Block mined!")

                print(
                    f"Nonce: {self.nonce}"
                )

                print(
                    f"Hash:  {self.hash}"
                )

                return

            self.nonce += 1


class WeedNode:

    def __init__(self):

        self.chain = []

        self.utxos = {}

        self.load_or_create_blockchain()

        self.rebuild_utxos()

    def load_or_create_blockchain(self):

        saved = load_json(
            BLOCKCHAIN_FILE,
            []
        )

        if not saved:

            genesis = Block(
                index=0,
                timestamp=time.time(),
                previous_hash="0",
                transactions=[]
            )

            genesis.hash = (
            genesis.calculate_hash(
            use_merkle=False
           )
        )

            self.chain.append(
                genesis
            )

            self.save()

            print(
                "Created new blockchain."
            )

            return

        for data in saved:

            block = Block(
                index=data["index"],
                timestamp=data["timestamp"],
                previous_hash=data["previous_hash"],
                transactions=data["transactions"],
                nonce=data["nonce"],
                hash=data["hash"]
            )

            self.chain.append(
                block
            )

        print(
            f"Loaded blockchain with "
            f"{len(self.chain)} blocks."
        )

    def rebuild_utxos(self):

        self.utxos = {}

        for block in self.chain:

            for transaction in block.transactions:

                if transaction.get(
                    "type"
                ) == "coinbase":

                    utxo_id = (
                        f"{block.hash}:0"
                    )

                    self.utxos[utxo_id] = {

                        "address":
                            transaction["receiver"],

                        "amount":
                            transaction["amount"],

                        "coinbase":
                            True,

                        "created_height":
                            block.index
                    }

                    continue

                if transaction.get(
                    "type"
                ) == "transaction":

                    txid = transaction["hash"]

                    for tx_input in transaction["inputs"]:

                        input_id = (
                            f'{tx_input["txid"]}:'
                            f'{tx_input["index"]}'
                        )

                        if input_id in self.utxos:

                            del self.utxos[
                                input_id
                            ]

                    for output_index, output in enumerate(
                        transaction["outputs"]
                    ):

                        output_id = (
                            f"{txid}:"
                            f"{output_index}"
                        )

                        self.utxos[output_id] = {

                            "address":
                                output["address"],

                            "amount":
                                output["amount"]
                        }

    def save(self):

        data = []

        for block in self.chain:

            data.append({

                "index":
                    block.index,

                "timestamp":
                    block.timestamp,

                "previous_hash":
                    block.previous_hash,

                "transactions":
                    block.transactions,

                "nonce":
                    block.nonce,

                "hash":
                    block.hash
            })

        save_json(
            BLOCKCHAIN_FILE,
            data
        )

    def latest_block(self):

        return self.chain[-1]
