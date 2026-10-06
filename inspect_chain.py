from node import WeedNode


def main():

    node = WeedNode()

    print()
    print("================================")
    print("       CHAIN TRANSACTION AUDIT")
    print("================================")

    for block in node.chain:

        print()
        print(f"Block #{block.index}")
        print(f"Hash: {block.hash}")

        for i, tx in enumerate(block.transactions):

            print()
            print(f"  Transaction {i}")
            print(f"  Type: {tx.get('type')}")

            if tx.get("type") == "coinbase":

                print(
                    f"  Receiver: {tx['receiver']}"
                )

                print(
                    f"  Amount: {tx['amount']}"
                )

            elif tx.get("type") == "transaction":

                print(
                    f"  TXID: {tx['hash']}"
                )

                print(
                    f"  Inputs: {len(tx['inputs'])}"
                )

                print(
                    f"  Outputs: {len(tx['outputs'])}"
                )

                for tx_input in tx["inputs"]:

                    print(
                        "    INPUT:",
                        tx_input["txid"],
                        tx_input["index"],
                        tx_input["amount"]
                    )

                for output in tx["outputs"]:

                    print(
                        "    OUTPUT:",
                        output["address"],
                        output["amount"]
                    )

    print()
    print("================================")


if __name__ == "__main__":
    main()
