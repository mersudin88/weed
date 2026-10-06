from p2p import P2PNode


chain_a = [
    {
        "index": 0,
        "timestamp": 0,
        "previous_hash": "0",
        "transactions": [],
        "nonce": 0,
        "hash": ""
    }
]


node_a = P2PNode(chain_a)

node_b = P2PNode(chain_a.copy())

print()
print("================================")
print("          P2P TEST")
print("================================")

print()
print("Node A blocks:", len(node_a.blockchain))
print("Node B blocks:", len(node_b.blockchain))

print()
print("P2P module working.")
