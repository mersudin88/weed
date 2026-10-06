from node import WeedNode
from wallet_storage import load_wallet
from transaction import Transaction
from transaction_validator import validate_transaction


node = WeedNode()
wallet = load_wallet()

print()
print("================================")
print("   WEED MINER MATURITY TEST")
print("================================")
print()

coinbase_utxo_id = None
coinbase_utxo = None

for utxo_id, utxo in node.utxos.items():

    if (
        utxo.get("coinbase")
        and utxo["address"] == wallet.address
    ):
        coinbase_utxo_id = utxo_id
        coinbase_utxo = utxo
        break

if coinbase_utxo is None:

    print("No coinbase UTXO found.")
    raise SystemExit(1)


txid, index = coinbase_utxo_id.rsplit(":", 1)

transaction = Transaction(
    inputs=[
        {
            "txid": txid,
            "index": int(index),
            "amount": coinbase_utxo["amount"]
        }
    ],
    outputs=[
        {
            "address": wallet.address,
            "amount": coinbase_utxo["amount"] - 1
        }
    ],
    public_key=wallet.public_key_hex
)

transaction.sign(wallet)

next_height = len(node.chain)

valid, reason = validate_transaction(
    transaction,
    node.utxos,
    current_height=next_height
)

print(f"Current chain height: {next_height - 1}")
print(f"Next block height:    {next_height}")
print()
print(f"Coinbase created at:  {coinbase_utxo['created_height']}")
print()
print(
    f"Miner validation: "
    f"{'ACCEPTED' if valid else 'REJECTED'}"
)
print(f"Reason: {reason}")

print()
print("================================")
