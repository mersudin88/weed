import json

from chain_validator import validate_chain


def load_blockchain(directory):

    filename = f"{directory}/blockchain.json"

    with open(
        filename,
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)


def test_real_node_a_blockchain_is_valid():

    chain = load_blockchain(
        "node_a"
    )

    valid, reason = validate_chain(
        chain
    )

    assert valid
    assert reason == "Blockchain is valid"


def test_node_b_blockchain_is_valid():

    chain = load_blockchain(
        "node_b"
    )

    valid, reason = validate_chain(
        chain
    )

    assert valid
    assert reason == "Blockchain is valid"