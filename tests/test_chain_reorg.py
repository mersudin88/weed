from node import Block, WeedNode
from p2p import P2PNode


def make_block(index, previous_hash, receiver):
    block = Block(
        index=index,
        timestamp=1000 + index,
        previous_hash=previous_hash,
        transactions=[
            {
                "type": "coinbase",
                "receiver": receiver,
                "amount": 50
            }
        ]
    )

    block.mine(4)

    return block


def block_to_dict(block):
    return {
        "index": block.index,
        "timestamp": block.timestamp,
        "previous_hash": block.previous_hash,
        "transactions": block.transactions,
        "nonce": block.nonce,
        "hash": block.hash
    }


def test_receive_longer_chain_reorganizes():
    node = WeedNode()

    genesis_block = node.chain[0]

    genesis_data = {
        "index": genesis_block.index,
        "timestamp": genesis_block.timestamp,
        "previous_hash": genesis_block.previous_hash,
        "transactions": genesis_block.transactions,
        "nonce": genesis_block.nonce,
        "hash": genesis_block.hash
    }

    genesis_hash = genesis_block.hash

    # -------------------------------------------------
    # Lokalni lanac:
    #
    # Genesis -> A1 -> A2
    # -------------------------------------------------

    a1 = make_block(
        1,
        genesis_hash,
        "WEED1local"
    )

    a2 = make_block(
        2,
        a1.hash,
        "WEED1local"
    )

    local_chain = [
        genesis_data,
        block_to_dict(a1),
        block_to_dict(a2)
    ]

    # -------------------------------------------------
    # Duži lanac:
    #
    # Genesis -> B1 -> B2 -> B3
    # -------------------------------------------------

    b1 = make_block(
        1,
        genesis_hash,
        "WEED1remote"
    )

    b2 = make_block(
        2,
        b1.hash,
        "WEED1remote"
    )

    b3 = make_block(
        3,
        b2.hash,
        "WEED1remote"
    )

    longer_chain = [
        genesis_data,
        block_to_dict(b1),
        block_to_dict(b2),
        block_to_dict(b3)
    ]

    # -------------------------------------------------
    # Node počinje na kraćem lancu.
    # -------------------------------------------------

    p2p = P2PNode(
        local_chain,
        host="127.0.0.1",
        port=5999
    )

    assert len(p2p.blockchain) == 3

    # -------------------------------------------------
    # Prima duži lanac.
    # -------------------------------------------------

    accepted = p2p.receive_chain(
        longer_chain
    )

    assert accepted is True

    # -------------------------------------------------
    # Provjera REORGA.
    # -------------------------------------------------

    assert len(p2p.blockchain) == 4

    assert (
        p2p.blockchain[-1]["hash"]
        == b3.hash
    )

    assert (
        p2p.blockchain[1]["hash"]
        == b1.hash
    )

    assert (
        p2p.blockchain[2]["hash"]
        == b2.hash
    )

    assert (
        p2p.blockchain[3]["hash"]
        == b3.hash
    )
    
    def test_utxo_rebuild_after_reorg():
         node = WeedNode()

         genesis_block = node.chain[0]

         genesis_data = {
        "index": genesis_block.index,
        "timestamp": genesis_block.timestamp,
        "previous_hash": genesis_block.previous_hash,
        "transactions": genesis_block.transactions,
        "nonce": genesis_block.nonce,
        "hash": genesis_block.hash
    }

    genesis_hash = genesis_block.hash

    # -------------------------------------------------
    # Fork A
    #
    # Genesis -> A1 -> A2
    # -------------------------------------------------

    a1 = make_block(
        1,
        genesis_hash,
        "WEED1local"
    )

    a2 = make_block(
        2,
        a1.hash,
        "WEED1local"
    )

    local_chain = [
        genesis_data,
        block_to_dict(a1),
        block_to_dict(a2)
    ]

    # -------------------------------------------------
    # Fork B
    #
    # Genesis -> B1 -> B2 -> B3
    # -------------------------------------------------

    b1 = make_block(
        1,
        genesis_hash,
        "WEED1remote"
    )

    b2 = make_block(
        2,
        b1.hash,
        "WEED1remote"
    )

    b3 = make_block(
        3,
        b2.hash,
        "WEED1remote"
    )

    longer_chain = [
        genesis_data,
        block_to_dict(b1),
        block_to_dict(b2),
        block_to_dict(b3)
    ]

    # -------------------------------------------------
    # Početno stanje = lokalni fork A.
    # -------------------------------------------------

    p2p = P2PNode(
        local_chain,
        host="127.0.0.1",
        port=5998
    )

    assert p2p.receive_chain(longer_chain) is True

    assert len(p2p.blockchain) == 4

    # -------------------------------------------------
    # Pretvori novi chain nazad u Block objekte.
    # -------------------------------------------------

    node.chain = []

    for block_data in p2p.blockchain:
        block = Block(
            index=block_data["index"],
            timestamp=block_data["timestamp"],
            previous_hash=block_data["previous_hash"],
            transactions=block_data["transactions"],
            nonce=block_data["nonce"],
            hash=block_data["hash"]
        )

        node.chain.append(block)

    # -------------------------------------------------
    # Ponovo izgradi UTXO stanje iz NOVOG chaina.
    # -------------------------------------------------

    node.rebuild_utxos()

    # -------------------------------------------------
    # Stari fork A ne smije ostati u UTXO setu.
    # -------------------------------------------------

    old_a1_utxo = f"{a1.hash}:0"
    old_a2_utxo = f"{a2.hash}:0"

    assert old_a1_utxo not in node.utxos
    assert old_a2_utxo not in node.utxos

    # -------------------------------------------------
    # Novi fork B mora imati svoje UTXO-e.
    # -------------------------------------------------

    new_b1_utxo = f"{b1.hash}:0"
    new_b2_utxo = f"{b2.hash}:0"
    new_b3_utxo = f"{b3.hash}:0"

    assert new_b1_utxo in node.utxos
    assert new_b2_utxo in node.utxos
    assert new_b3_utxo in node.utxos

    assert node.utxos[new_b1_utxo]["address"] == "WEED1remote"
    assert node.utxos[new_b2_utxo]["address"] == "WEED1remote"
    assert node.utxos[new_b3_utxo]["address"] == "WEED1remote"

def test_utxo_rebuild_after_reorg():
    node = WeedNode()

    genesis_block = node.chain[0]

    genesis_data = {
        "index": genesis_block.index,
        "timestamp": genesis_block.timestamp,
        "previous_hash": genesis_block.previous_hash,
        "transactions": genesis_block.transactions,
        "nonce": genesis_block.nonce,
        "hash": genesis_block.hash
    }

    genesis_hash = genesis_block.hash

    a1 = make_block(
        1,
        genesis_hash,
        "WEED1local"
    )

    a2 = make_block(
        2,
        a1.hash,
        "WEED1local"
    )

    local_chain = [
        genesis_data,
        block_to_dict(a1),
        block_to_dict(a2)
    ]

    b1 = make_block(
        1,
        genesis_hash,
        "WEED1remote"
    )

    b2 = make_block(
        2,
        b1.hash,
        "WEED1remote"
    )

    b3 = make_block(
        3,
        b2.hash,
        "WEED1remote"
    )

    longer_chain = [
        genesis_data,
        block_to_dict(b1),
        block_to_dict(b2),
        block_to_dict(b3)
    ]

    p2p = P2PNode(
        local_chain,
        host="127.0.0.1",
        port=5998
    )

    assert p2p.receive_chain(longer_chain) is True

    node.chain = []

    for block_data in p2p.blockchain:
        block = Block(
            index=block_data["index"],
            timestamp=block_data["timestamp"],
            previous_hash=block_data["previous_hash"],
            transactions=block_data["transactions"],
            nonce=block_data["nonce"],
            hash=block_data["hash"]
        )

        node.chain.append(block)

    node.rebuild_utxos()

    assert f"{a1.hash}:0" not in node.utxos
    assert f"{a2.hash}:0" not in node.utxos

    assert f"{b1.hash}:0" in node.utxos
    assert f"{b2.hash}:0" in node.utxos
    assert f"{b3.hash}:0" in node.utxos

    assert node.utxos[f"{b1.hash}:0"]["address"] == "WEED1remote"
    assert node.utxos[f"{b2.hash}:0"]["address"] == "WEED1remote"
    assert node.utxos[f"{b3.hash}:0"]["address"] == "WEED1remote"