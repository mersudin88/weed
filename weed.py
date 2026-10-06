import hashlib
import json
import time

from dataclasses import dataclass

from wallet import Wallet
from transaction import Transaction


COIN_NAME = "Weed"
SYMBOL = "WEED"

BLOCK_REWARD = 50
DIFFICULTY = 4


@dataclass
class Block:

    index: int
    timestamp: float
    previous_hash: str
    transactions: list
    nonce: int = 0
    hash: str = ""

    def calculate_hash(self):

        data = {
            "index": self.index,
            "timestamp": self.timestamp,
            "previous_hash": self.previous_hash,
            "transactions": self.transactions,
            "nonce": self.nonce
        }

        encoded = json.dumps(
            data,
            sort_keys=True,
            separators=(",", ":")
        ).encode()

        return hashlib.sha256(encoded).hexdigest()

    def mine(self):

        target = "0" * DIFFICULTY

        print(f"Mining block #{self.index}...")

        while True:

            self.hash = self.calculate_hash()

            if self.hash.startswith(target):

                print("Block mined!")
                print(f"Nonce: {self.nonce}")
                print(f"Hash:  {self.hash}")

                return

            self.nonce += 1


class Blockchain:

    def __init__(self):

        self.chain = []

        self.utxos = {}

        self.create_genesis_block()

    def create_genesis_block(self):

        genesis = Block(
            index=0,
            timestamp=time.time(),
            previous_hash="0",
            transactions=[]
        )

        genesis.hash = genesis.calculate_hash()

        self.chain.append(genesis)

    def latest_block(self):

        return self.chain[-1]

    def get_balance(self, address):

        total = 0

        for utxo in self.utxos.values():

            if utxo["address"] == address:
                total += utxo["amount"]

        return total

    def mine_block(self, miner_address):

        reward = {
            "type": "coinbase",
            "receiver": miner_address,
            "amount": BLOCK_REWARD
        }

        block = Block(
            index=len(self.chain),
            timestamp=time.time(),
            previous_hash=self.latest_block().hash,
            transactions=[reward]
        )

        block.mine()

        self.chain.append(block)

        utxo_id = f"{block.hash}:0"

        self.utxos[utxo_id] = {
            "address": miner_address,
            "amount": BLOCK_REWARD
        }

        return block

    def create_transaction(
        self,
        wallet,
        receiver,
        amount
    ):

        available = []

        total = 0

        for utxo_id, utxo in self.utxos.items():

            if utxo["address"] == wallet.address:

                available.append(
                    {
                        "id": utxo_id,
                        "amount": utxo["amount"]
                    }
                )

                total += utxo["amount"]

                if total >= amount:
                    break

        if total < amount:

            raise ValueError(
                f"Insufficient balance. "
                f"Balance: {total} WEED"
            )

        inputs = []

        for item in available:

            txid, index = item["id"].rsplit(":", 1)

            inputs.append(
                {
                    "txid": txid,
                    "index": int(index),
                    "amount": item["amount"]
                }
            )

        outputs = [
            {
                "address": receiver,
                "amount": amount
            }
        ]

        change = total - amount

        if change > 0:

            outputs.append(
                {
                    "address": wallet.address,
                    "amount": change
                }
            )

        transaction = Transaction(
            inputs=inputs,
            outputs=outputs,
            public_key=wallet.public_key_hex
        )

        transaction.sign(wallet)

        return transaction

    def verify_transaction(self, transaction):

        if not transaction.verify_signature(
            wallet_from_public_key(transaction.public_key)
        ):

            return False

        total_input = 0

        for tx_input in transaction.inputs:

            utxo_id = (
                f"{tx_input['txid']}:"
                f"{tx_input['index']}"
            )

            if utxo_id not in self.utxos:

                return False

            utxo = self.utxos[utxo_id]

            if utxo["amount"] != tx_input["amount"]:

                return False

            total_input += utxo["amount"]

        total_output = sum(
            output["amount"]
            for output in transaction.outputs
        )

        if total_output > total_input:

            return False

        return True

    def apply_transaction(self, transaction):

        if not self.verify_transaction(transaction):

            raise ValueError(
                "Invalid transaction"
            )

        # Remove spent UTXOs

        for tx_input in transaction.inputs:

            utxo_id = (
                f"{tx_input['txid']}:"
                f"{tx_input['index']}"
            )

            del self.utxos[utxo_id]

        # Create new UTXOs

        txid = transaction.transaction_hash()

        for index, output in enumerate(
            transaction.outputs
        ):

            utxo_id = f"{txid}:{index}"

            self.utxos[utxo_id] = {
                "address": output["address"],
                "amount": output["amount"]
            }

    def print_utxos(self):

        print("\n========== UTXO SET ==========")

        for utxo_id, utxo in self.utxos.items():

            print(f"\n{utxo_id}")
            print(f"Address: {utxo['address']}")
            print(f"Amount: {utxo['amount']} WEED")

        print("\n==============================")

    def is_valid(self):

        for i in range(1, len(self.chain)):

            current = self.chain[i]
            previous = self.chain[i - 1]

            if current.hash != current.calculate_hash():

                return False

            if current.previous_hash != previous.hash:

                return False

            if not current.hash.startswith(
                "0" * DIFFICULTY
            ):

                return False

        return True


def wallet_from_public_key(public_key_hex):

    wallet = Wallet.__new__(Wallet)

    wallet.public_key_hex = public_key_hex

    wallet.public_key = __import__(
        "ecdsa"
    ).VerifyingKey.from_string(
        bytes.fromhex(public_key_hex),
        curve=__import__("ecdsa").SECP256k1
    )

    return wallet


def main():

    print()
    print("====================================")
    print("          WEED COIN v3")
    print("    SHA-256 + UTXO + SIGNATURES")
    print("====================================")

    blockchain = Blockchain()

    wallet_a = Wallet()
    wallet_b = Wallet()

    print("\nWallet A:")
    print(wallet_a.address)

    print("\nWallet B:")
    print(wallet_b.address)

    # ==================================
    # Mining
    # ==================================

    print("\nMining first reward...")

    blockchain.mine_block(wallet_a.address)

    print("\nMining second reward...")

    blockchain.mine_block(wallet_a.address)

    print(
        "\nWallet A balance:",
        blockchain.get_balance(
            wallet_a.address
        ),
        "WEED"
    )

    # ==================================
    # Transaction
    # ==================================

    print("\nCreating transaction...")

    transaction = blockchain.create_transaction(
        wallet=wallet_a,
        receiver=wallet_b.address,
        amount=30
    )

    print("\nTransaction hash:")
    print(transaction.transaction_hash())

    print("\nSignature:")
    print(transaction.signature)

    print("\nSignature valid:")

    print(
        transaction.verify_signature(
            wallet_a
        )
    )

    # ==================================
    # Apply transaction
    # ==================================

    blockchain.apply_transaction(
        transaction
    )

    print("\nTransaction accepted!")

    print(
        "\nWallet A:",
        blockchain.get_balance(
            wallet_a.address
        ),
        "WEED"
    )

    print(
        "Wallet B:",
        blockchain.get_balance(
            wallet_b.address
        ),
        "WEED"
    )

    # ==================================
    # Mine transaction block
    # ==================================

    print("\nMining transaction confirmation...")

    block = Block(
        index=len(blockchain.chain),
        timestamp=time.time(),
        previous_hash=blockchain.latest_block().hash,
        transactions=[
            {
                "type": "transaction",
                "hash": transaction.transaction_hash()
            }
        ]
    )

    block.mine()

    blockchain.chain.append(block)

    # ==================================
    # Results
    # ==================================

    blockchain.print_utxos()

    print(
        "\nBlockchain valid:",
        blockchain.is_valid()
    )


if __name__ == "__main__":

    main()