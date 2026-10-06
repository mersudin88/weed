from merkle import merkle_root


def test_merkle_root_four_transactions():

    transactions = [
        "tx1",
        "tx2",
        "tx3",
        "tx4"
    ]

    root = merkle_root(transactions)

    assert root == (
        "773bc304a3b0a626a520a8d6eacc36809ac18c0b174f3ff3cdaf0a4e9c64433d"
    )


def test_merkle_root_changes_when_transaction_changes():

    transactions = [
        "tx1",
        "tx2",
        "tx3",
        "tx4"
    ]

    root1 = merkle_root(transactions)

    transactions[2] = "changed"

    root2 = merkle_root(transactions)

    assert root1 != root2


def test_merkle_root_empty_transactions():

    assert merkle_root([]) is None