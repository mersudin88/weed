from wallet import Wallet


def test_wallet_address():

    wallet = Wallet()

    assert wallet.address.startswith("WEED1")
    assert len(wallet.address) == 45


def test_wallet_signature():

    wallet = Wallet()

    message = "WEED test message"

    signature = wallet.sign(message)

    assert wallet.verify(
        message,
        signature
    )


def test_wallet_rejects_changed_message():

    wallet = Wallet()

    message = "WEED test message"

    signature = wallet.sign(message)

    assert not wallet.verify(
        "Changed message",
        signature
    )