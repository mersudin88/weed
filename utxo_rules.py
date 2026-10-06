from consensus import (
    COINBASE_MATURITY,
    COINBASE_MATURITY_HEIGHT
)


def is_coinbase_mature(
    current_height,
    created_height
):

    if current_height < COINBASE_MATURITY_HEIGHT:

        return True

    confirmations = (
        current_height
        - created_height
        + 1
    )

    return confirmations >= COINBASE_MATURITY


def validate_coinbase_spend(
    current_height,
    created_height
):

    if current_height < COINBASE_MATURITY_HEIGHT:

        return (
            True,
            "Coinbase maturity not active yet"
        )

    confirmations = (
        current_height
        - created_height
        + 1
    )

    if confirmations < COINBASE_MATURITY:

        return (
            False,
            "Coinbase UTXO is immature: "
            f"{confirmations}/"
            f"{COINBASE_MATURITY} confirmations"
        )

    return (
        True,
        "Coinbase UTXO is mature"
    )
