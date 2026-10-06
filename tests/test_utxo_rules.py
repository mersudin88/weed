from utxo_rules import (
    is_coinbase_mature,
    validate_coinbase_spend
)


def test_coinbase_maturity_not_active_before_height_15():

    assert is_coinbase_mature(
        14,
        14
    )


def test_coinbase_immature_at_height_15():

    assert not is_coinbase_mature(
        15,
        15
    )


def test_coinbase_mature_after_100_confirmations():

    assert is_coinbase_mature(
        114,
        15
    )


def test_coinbase_spend_rejected_when_immature():

    valid, reason = validate_coinbase_spend(
        15,
        15
    )

    assert not valid
    assert "immature" in reason


def test_coinbase_spend_accepted_when_mature():

    valid, reason = validate_coinbase_spend(
        114,
        15
    )

    assert valid