from transaction import Transaction
from storage import save_mempool, load_mempool


class Mempool:

    def __init__(self):

        self.transactions = []

        self.load()

    def load(self):

        saved = load_mempool()

        self.transactions = []

        for data in saved:

            transaction = Transaction(
                inputs=data["inputs"],
                outputs=data["outputs"],
                public_key=data["public_key"],
                signature=data["signature"]
            )

            self.transactions.append(
                transaction
            )

    def save(self):

        save_mempool(
            self.transactions
        )

    def add_transaction(self, transaction):

        if transaction.signature is None:

            raise ValueError(
                "Transaction has no signature"
            )

        txid = transaction.transaction_hash()

        for existing in self.transactions:

            if existing.transaction_hash() == txid:

                raise ValueError(
                    "Transaction already in mempool"
                )

        new_inputs = set()

        for tx_input in transaction.inputs:

            txid_input = tx_input.get("txid")
            index_input = tx_input.get("index")

            if txid_input is None or index_input is None:

                raise ValueError(
                    "Invalid transaction input"
                )

            input_id = (
                f"{txid_input}:"
                f"{index_input}"
            )

            if input_id in new_inputs:

                raise ValueError(
                    "Transaction contains duplicate input"
                )

            new_inputs.add(input_id)

        for existing in self.transactions:

            for tx_input in existing.inputs:

                existing_txid = tx_input.get("txid")
                existing_index = tx_input.get("index")

                existing_input_id = (
                    f"{existing_txid}:"
                    f"{existing_index}"
                )

                if existing_input_id in new_inputs:

                    raise ValueError(
                        "Transaction conflicts with "
                        "existing mempool transaction"
                    )

        self.transactions.append(
            transaction
        )

        self.save()

        print()
        print("Transaction added to mempool:")
        print(txid)

    def get_transactions(self):

        return self.transactions

    def remove_transaction(self, txid):

        self.transactions = [
            tx
            for tx in self.transactions
            if tx.transaction_hash() != txid
        ]

        self.save()

    def clear(self):

        self.transactions = []

        self.save()

    def count(self):

        return len(self.transactions)
