import hashlib
import json


class Transaction:

    def __init__(
        self,
        inputs,
        outputs,
        public_key,
        signature=None
    ):

        self.inputs = inputs
        self.outputs = outputs
        self.public_key = public_key
        self.signature = signature

    def signing_data(self):

        data = {
            "inputs": self.inputs,
            "outputs": self.outputs,
            "public_key": self.public_key
        }

        return json.dumps(
            data,
            sort_keys=True,
            separators=(",", ":")
        )

    def transaction_hash(self):

        data = self.signing_data().encode()

        return hashlib.sha256(data).hexdigest()

    def sign(self, wallet):

        message = self.signing_data()

        self.signature = wallet.sign(message)

    def verify_signature(self, wallet):

        if self.signature is None:
            return False

        return wallet.verify(
            self.signing_data(),
            self.signature
        )