"""Native WEED SHA-256 Stratum job manager; separate from AuxPoW."""
from dataclasses import dataclass
from types import SimpleNamespace
import time

from scarletcoin.core.template import BlockTemplate
from scarletcoin.crypto.keys import Address
from .jobs import ShareResult
from .coinbase import coinbase_merkle_branch

_DIFF1_TARGET = 0xFFFF * (1 << 208)


@dataclass
class NativeCoinbase:
    coinbase1: str
    coinbase2: str


@dataclass
class NativeJob:
    job_id: str
    template: BlockTemplate
    parent: object
    weed: object
    coinbase: NativeCoinbase
    merkle_branches: list[str]
    created: float
    ntime: int
    clean: bool = True
    payout_hash: bytes = b""


class NativeJobManager:
    """Creates standard WEED block templates and validates native PoW shares."""

    def __init__(self, *, weed, payout_address: str, share_difficulty=None, **kwargs):
        self._weed = weed
        self._payout_address = payout_address
        self._fixed_share_target = (
            max(1, int(_DIFF1_TARGET / share_difficulty))
            if share_difficulty is not None and share_difficulty > 0
            else None
        )
        self.current = None
        self._counter = 0
        self._jobs = {}

    @property
    def share_target(self):
        if self._fixed_share_target is not None:
            return self._fixed_share_target
        if self.current is None:
            return 1
        return self.current.template.target

    @share_target.setter
    def share_target(self, value):
        self._fixed_share_target = max(1, int(value))

    @property
    def share_difficulty(self):
        return _DIFF1_TARGET / self.share_target

    def refresh(self, payout_address=None):
        address_text = payout_address or self._payout_address
        address = Address.decode(address_text)
        template = BlockTemplate.from_dict(self._weed.getblocktemplate())

        # Build a coinbase with an eight-byte placeholder for extranonce1/2.
        placeholder = bytes.fromhex("a1b2c3d4e5f60718")
        block = template.build_block(pubkey_hash=address.hash, extra=placeholder)
        coinbase = block.transactions[0]
        raw = coinbase.serialize_body()
        marker = raw.rfind(placeholder)
        if marker < 0:
            raise RuntimeError("Could not locate native coinbase extranonce placeholder")
        coinbase1 = raw[:marker].hex()
        coinbase2 = raw[marker + len(placeholder):].hex()

        txids = [tx.txid() for tx in template.transactions]
        branches = coinbase_merkle_branch(txids)

        self._counter += 1
        job = NativeJob(
            job_id=f"n{self._counter:x}",
            template=template,
            parent=SimpleNamespace(
                prev_hash=template.prev_hash.hex(),
                version=template.version,
                nbits=template.bits,
            ),
            weed=SimpleNamespace(height=template.height),
            coinbase=NativeCoinbase(coinbase1, coinbase2),
            merkle_branches=branches,
            created=time.time(),
            ntime=max(template.current_time, template.min_time + 1),
            payout_hash=address.hash,
        )
        self._jobs[job.job_id] = job
        self.current = job
        return job

    def process_share(self, job, extranonce1_hex, extranonce2_hex, ntime, nonce):
        try:
            if len(extranonce1_hex) != 8 or len(extranonce2_hex) != 8:
                return ShareResult(False, "invalid extranonce length")
            if ntime < job.template.min_time + 1:
                return ShareResult(False, "timestamp below minimum")
            block = job.template.build_block(
                pubkey_hash=job.payout_hash,
                extra=bytes.fromhex(extranonce1_hex + extranonce2_hex),
                timestamp=ntime,
                nonce=nonce,
            )
            digest = block.hash()
            value = int.from_bytes(digest, "little")
            meets_network = value <= job.template.target
            meets_share = value <= self.share_target
            return ShareResult(
                accepted=meets_share,
                reason="" if meets_share else "low difficulty share",
                hash_hex=digest[::-1].hex(),
                meets_weed_target=meets_network,
                meets_btc_target=False,
            )
        except (ValueError, TypeError, OverflowError) as exc:
            return ShareResult(False, f"invalid share: {exc}")

    def submit_weed_block(self, job, extranonce1_hex, extranonce2_hex, ntime, nonce):
        block = job.template.build_block(
            pubkey_hash=job.payout_hash,
            extra=bytes.fromhex(extranonce1_hex + extranonce2_hex),
            timestamp=ntime,
            nonce=nonce,
        )
        digest = block.hash()
        if int.from_bytes(digest, "little") > job.template.target:
            return {"status": "rejected", "reason": "hash does not meet WEED target"}
        return self._weed.submitblock(block.serialize().hex())
