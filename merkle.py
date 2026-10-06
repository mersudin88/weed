import hashlib


def hash_data(data):
    return hashlib.sha256(
        data.encode()
    ).hexdigest()


def merkle_root(transactions):

    if not transactions:
        return None

    hashes = [
        hash_data(tx)
        for tx in transactions
    ]

    while len(hashes) > 1:

        if len(hashes) % 2 != 0:
            hashes.append(hashes[-1])

        new_hashes = []

        for i in range(0, len(hashes), 2):

            combined = (
                hashes[i]
                + hashes[i + 1]
            )

            new_hashes.append(
                hash_data(combined)
            )

        hashes = new_hashes

    return hashes[0]


if __name__ == "__main__":

    transactions = [
        "transaction A",
        "transaction B",
        "transaction x",
        "transaction D"
    ]

    root = merkle_root(transactions)

    print()
    print("================================")
    print("         WEED MERKLE TREE")
    print("================================")
    print()

    print("Transactions:")

    for tx in transactions:
        print("-", tx)

    print()
    print("Merkle root:")
    print(root)

    print()
    print("================================")