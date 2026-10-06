from rpc_server import handle_request


class FakeNode:
    def __init__(self):
        self.chain = []


class FakeBlock:
    def __init__(
        self,
        index,
        timestamp,
        previous_hash,
        transactions,
        nonce,
        hash_value
    ):
        self.index = index
        self.timestamp = timestamp
        self.previous_hash = previous_hash
        self.transactions = transactions
        self.nonce = nonce
        self.hash = hash_value


def create_fake_node():
    node = FakeNode()

    node.chain = [
        FakeBlock(
            index=0,
            timestamp=1000,
            previous_hash="0",
            transactions=[],
            nonce=0,
            hash_value="genesis_hash"
        ),
        FakeBlock(
            index=1,
            timestamp=1060,
            previous_hash="genesis_hash",
            transactions=[
                {
                    "type": "coinbase",
                    "receiver": "WEED_TEST",
                    "amount": 50
                }
            ],
            nonce=123,
            hash_value="block_1_hash"
        )
    ]

    return node


def test_get_info():
    node = create_fake_node()

    response = handle_request(
        node,
        {
            "method": "get_info"
        }
    )

    assert response["success"] is True
    assert response["height"] == 1
    assert response["blocks"] == 2


def test_get_blockchain():
    node = create_fake_node()

    response = handle_request(
        node,
        {
            "method": "get_blockchain"
        }
    )

    assert response["success"] is True
    assert len(response["blockchain"]) == 2
    assert response["blockchain"][1]["index"] == 1
    assert response["blockchain"][1]["hash"] == "block_1_hash"


def test_get_block():
    node = create_fake_node()

    response = handle_request(
        node,
        {
            "method": "get_block",
            "index": 1
        }
    )

    assert response["success"] is True
    assert response["block"]["index"] == 1
    assert response["block"]["nonce"] == 123


def test_get_block_invalid_index():
    node = create_fake_node()

    response = handle_request(
        node,
        {
            "method": "get_block",
            "index": 99
        }
    )

    assert response["success"] is False
    assert response["error"] == "Block not found"


def test_get_block_invalid_type():
    node = create_fake_node()

    response = handle_request(
        node,
        {
            "method": "get_block",
            "index": "1"
        }
    )

    assert response["success"] is False
    assert response["error"] == "Invalid block index"


def test_unknown_method():
    node = create_fake_node()

    response = handle_request(
        node,
        {
            "method": "does_not_exist"
        }
    )

    assert response["success"] is False
    assert response["error"] == "Unknown method"
def test_rpc_methods_with_real_node():
    from node import WeedNode

    node = WeedNode()

    info = handle_request(
        node,
        {
            "method": "get_info"
        }
    )

    assert info["success"] is True
    assert info["height"] == len(node.chain) - 1
    assert info["blocks"] == len(node.chain)

    blockchain = handle_request(
        node,
        {
            "method": "get_blockchain"
        }
    )

    assert blockchain["success"] is True
    assert len(blockchain["blockchain"]) == len(node.chain)

    last_index = len(node.chain) - 1

    block = handle_request(
        node,
        {
            "method": "get_block",
            "index": last_index
        }
    )

    assert block["success"] is True
    assert block["block"]["index"] == last_index
    assert block["block"]["hash"] == node.chain[-1].hash    