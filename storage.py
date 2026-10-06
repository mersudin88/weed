import json
import os


DATA_DIR = os.environ.get(
    "WEED_DATA_DIR",
    "."
)


BLOCKCHAIN_FILE = os.path.join(
    DATA_DIR,
    "blockchain.json"
)

MEMPOOL_FILE = os.path.join(
    DATA_DIR,
    "mempool.json"
)


def save_json(filename, data):

    directory = os.path.dirname(filename)

    if directory:
        os.makedirs(
            directory,
            exist_ok=True
        )

    with open(
        filename,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            data,
            file,
            indent=2
        )


def load_json(filename, default):

    if not os.path.exists(filename):
        return default

    with open(
        filename,
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)


def save_blockchain(blockchain):

    data = []

    for block in blockchain.chain:

        data.append({
            "index": block.index,
            "timestamp": block.timestamp,
            "previous_hash": block.previous_hash,
            "transactions": block.transactions,
            "nonce": block.nonce,
            "hash": block.hash
        })

    save_json(
        BLOCKCHAIN_FILE,
        data
    )


def load_blockchain():

    return load_json(
        BLOCKCHAIN_FILE,
        []
    )


def save_mempool(mempool):

    data = []

    for transaction in mempool:

        data.append({
            "inputs": transaction.inputs,
            "outputs": transaction.outputs,
            "public_key": transaction.public_key,
            "signature": transaction.signature
        })

    save_json(
        MEMPOOL_FILE,
        data
    )


def load_mempool():

    return load_json(
        MEMPOOL_FILE,
        []
    )
