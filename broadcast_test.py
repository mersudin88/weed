from p2p import P2PNode

node = P2PNode([])

node.add_peer(
    "127.0.0.1",
    5000
)

node.broadcast({
    "type": "test",
    "message": "HELLO FROM NODE B"
})
