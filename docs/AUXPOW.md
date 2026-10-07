# AuxPoW — Merged Mining for WEED

WEED supports **Namecoin-style AuxPoW**, so an existing SHA-256 ASIC
miner can produce WEED blocks while hashing the 80-byte headers it
already knows how to hash.

## How it works

```
          SHA-256d ASIC
               │
               │ standard Stratum V1 job
               ▼
        merged-mining pool
               │
               │ same nonce, two targets
               ▼
   WEED AuxPoW proof  (when hash ≤ WEED target)
```

The ASIC does exactly what it always does — hashes an 80-byte header. The pool
puts a WEED **commitment** into the parent coinbase before handing the
job out, and when a nonce's hash meets the WEED target it assembles an
**AuxPoW proof** and submits it to a WEED node.

### What "parent" means here

The parent coinbase is validated as an ordinary WEED
:class:`~scarletcoin.core.transaction.Transaction`, and the commitment lives in
that transaction's **`coinbase_data`** field. It is *not* a Bitcoin-format
coinbase, so a block taken from a real Bitcoin node cannot be used as a parent
proof by this implementation. The parent header is therefore supplied by the
pool (a "simulated parent chain") — the ASIC cannot tell the difference, and
WEED never inspects the parent chain's state, but no BTC is mined.

Supporting a real Bitcoin parent would mean adding a Bitcoin-format coinbase
parser to the validation path.

## Commitment format

The commitment lives in the parent coinbase's `coinbase_data` field, following
the Namecoin convention:

```
fa be 6d 6d          merged-mining magic marker (4 bytes)
⟨aux_merkle_root⟩    WEED commitment root (32 bytes)
⟨tree_size⟩          auxiliary tree size, uint32 LE (4 bytes)
⟨nonce⟩              commitment nonce, uint32 LE (4 bytes)
```

`coinbase_data` always begins with the block height as a uint32 LE, so in
practice it looks like `height ‖ extranonces ‖ commitment`.

For a single auxiliary chain (only WEED) the tree has one leaf, so:

- `tree_size = 1`
- `aux_merkle_branch = []` (empty)
- `aux_chain_index = 0` (always 0 for a height-0 tree)

## Consensus validation

A WEED node validates an AuxPoW block by proving seven things:

1. **Structural** — all branches ≤ 30 levels, all hashes 32 bytes, parent header is 80 bytes
2. **Aux block hash** — the WEED block hash itself (the 80-byte SHA-256d header)
3. **Aux Merkle root** — the block hash, passed through the auxiliary Merkle branch, reaches `aux_merkle_root`
4. **Commitment present** — exactly one `fa be 6d 6d` marker in the parent coinbase, with correct root
5. **Deterministic index** — the `aux_chain_index` matches `get_expected_index(nonce, chain_id, tree_height)`
6. **Coinbase Merkle proof** — the parent coinbase's hash, passed through the coinbase Merkle branch, reaches the parent block's `merkle_root`
7. **Parent PoW** — `SHA256d(parent_header) ≤ WEED target`

The key rule: **the parent header's hash is the proof of work for WEED.**
The WEED header's own `nonce` field is irrelevant for AuxPoW blocks.

Because the parent header is not checked against any parent-chain state, the
parent coinbase's output is never spendable. Only the commitment inside it
matters.

## Chain IDs

| Network | `auxpow_chain_id` |
|---------|-------------------|
| mainnet | 1 |
| testnet | 2 |
| regtest | 3 |

## Activation

AuxPoW is activated by a **consensus height** (`auxpow_activation_height`). Before that height, AuxPoW blocks are rejected. After activation, both native PoW and AuxPoW blocks are accepted.

Current mainnet: **not yet activated** (activation height = `None`).  
Current testnet: **not yet activated** (activation height = `None`).  
Current regtest: **activated from genesis** (activation height = 0).

## RPC

### `createauxblock <address>`

Creates a frozen AuxPoW candidate. Returns:

```json
{
  "hash": "<weed-block-hash>",
  "chainid": 1,
  "target": "<64-char-target>",
  "bits": "0x...",
  "height": 12345,
  "previousblock": "<hash>",
  "coinbasevalue": 5000000000,
  "coinbasehash": "<hash>",
  "tree_size": 1,
  "nonce": 1234567890
}
```

### `submitauxblock <hash> <auxpow_hex>`

Submits a complete AuxPoW proof. Returns the block submission result with `status: "connected"` on success.

## Block serialization

A WEED block wire format appends the AuxPoW after transactions:

```
[80-byte header]
[transaction count + transactions]
[marker: 0x00 = native, 0x01 = AuxPoW]
[if marker=0x01: varbytes(AuxPoW)]
```

The **WEED block hash is always the SHA-256d of the 80-byte header only** — the AuxPoW payload does not change the block hash.

## Deterministic index formula

From the Namecoin reference implementation:

```python
rand = nonce & 0xFFFFFFFF
rand = rand * 1103515245 + 12345
rand += chain_id
rand = rand * 1103515245 + 12345
index = rand % (1 << aux_tree_height)
```

For `aux_tree_height = 0` (single chain), the result is always 0.

## Security

- Maximum Merkle branch depth: 30 levels
- Coinbase data must contain exactly one commitment marker — duplicate markers cause rejection
- Tree size must be a power of two
- Nonce hash must not exceed the WEED target
- The parent coinbase MUST be a coinbase transaction (null outpoint)
- All consensus rules (UTXO, signatures, subsidy, timestamp, difficulty) still apply

## References

- Namecoin AuxPoW implementation: https://github.com/namecoin/namecoin-core/blob/master/src/auxpow.cpp
- Namecoin merged-mining documentation: https://github.com/vinced/namecoin/blob/master/doc/README_merged-mining.md
- WEED repository: https://github.com/alessio-ds/WEED