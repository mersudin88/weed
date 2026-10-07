# Running a WEED Merged-Mining Pool

This guide covers deploying the Stratum bridge on `WEED public node`
(or any server running a WEED node) so that Bitcoin ASIC miners can
mine WEED.

## Architecture

```
Internet
   │
   │ :3333 (Stratum)        :28333 (P2P)
   ▼                         ▼
┌──────────────┐    ┌─────────────────┐
│ Stratum      │    │ WEED     │
│ bridge       │───▶│ node            │
│ (port 3333)  │    │ (port 28332 RPC)│
└──────────────┘    └─────────────────┘
   │                         │
   │ localhost RPC           │ :443 (Caddy)
   │ (createauxblock,        │
   │  submitauxblock)        ▼
   ▼                 WEED public node
                     (explorer / public RPC)
```

The bridge runs as a separate OpenRC service, talks to the WEED node
over localhost RPC, and exposes a Stratum V1 TCP port for ASIC miners.

The node itself is already behind Caddy (HTTPS) for the explorer and
read-only public RPC; the bridge goes **directly to localhost:28332** with the
node's RPC token since `createauxblock`/`submitauxblock` are mining methods.

## Deployment on WEED public node (Alpine Linux)

The reference node is an Alpine server at `45.126.126.139`.  The full node
setup is documented in [RUNNING-A-NETWORK.md](RUNNING-A-NETWORK.md); this
section adds the Stratum bridge on top of that existing installation.

### 1. Pull the latest code

```sh
cd /opt/weed
git pull origin main
chmod -R a+rX /opt/weed
# The virtualenv is already built against Alpine's Python.
# If new dependencies were added (none were this release), re-run:
#   UV_PYTHON_DOWNLOADS=never uv sync --python /usr/bin/python3
```

### 2. Check the mining RPC is available

`createauxblock` and `submitauxblock` are mining methods. The reference node
already runs with `--rpc-public-mining`, so they are reachable on localhost
without a token. Confirm it:

```sh
curl -s -X POST http://127.0.0.1:28332/rpc \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"createauxblock","params":["<your-weed-address>"]}'
```

A JSON object with `hash`, `target`, `chainid` and `nonce` means you are good.
If you get an authorization error instead, the node needs `--rpc-public-mining`
in `/etc/init.d/weed-node`, or the bridge needs `--weed-token` (the token
is in `/var/lib/weed/mainnet/rpc.token`).

### 3. Test the bridge manually

```sh
su -s /bin/sh weed -c \
  'cd /opt/weed && /opt/weed/.venv/bin/python -m pool.weed_pool.server \
    --weed-url http://127.0.0.1:28332 \
    --payout-address <your-weed-address> \
    --chain-id 1'
```

You should see the listening line and a first job:

```
Stratum server listening on 0.0.0.0:3333
```

Press Ctrl-C once you have confirmed it starts. If it exits with a
`chain id` error, the node is not on the network you asked for. If it exits
with `AuxPoW is not configured`, the node predates AuxPoW.

### 4. Install as an OpenRC service

```sh
# Copy the init script
cp /opt/weed/packaging/weed-stratum.openrc /etc/init.d/weed-stratum
chmod +x /etc/init.d/weed-stratum

# Create the config file with your real values
cat > /etc/conf.d/weed-stratum <<'EOF'
# Optional. Miners are paid the address in their worker name by default.
# Set this (and allow_pool_payout="yes") only to pay miners that send no
# address to you instead of refusing them.
payout_address=""
allow_pool_payout="no"
weed_url="http://127.0.0.1:28332"
chain_id="1"
port="3333"
host="0.0.0.0"
EOF

# Enable and start
rc-update add weed-stratum default
rc-service weed-stratum start
```

Leave `weed_token` unset while the node runs `--rpc-public-mining`, and leave
`share_difficulty` unset so the share rate tracks the chain — see
[MERGED-MINING.md](MERGED-MINING.md).

### 5. Open the Stratum port

```sh
iptables -A INPUT -p tcp --dport 3333 -j ACCEPT
rc-service iptables save
```

If your VPS provider has its own firewall / security group, open TCP 3333 there too.

### 6. Verify

```sh
# Check the service is running
rc-service weed-stratum status
tail -f /var/log/weed/stratum.log

# From your local machine, test Stratum connectivity
echo '{"id":1,"method":"mining.subscribe","params":["cpuminer/test"]}' \
  | nc -w3 WEED public node 3333
```

You should get back a JSON response with subscription details and a
`mining.set_difficulty` notification.

### Prove it end to end

`tools/stratum_probe.py` does what an ASIC does — subscribe, authorize, build
the coinbase, fold the Merkle branch, grind a nonce against the real block
target, submit — and reports whether the chain advanced:

```sh
python tools/stratum_probe.py \
    --host WEED public node --port 3333 \
    --payout-address <your-weed-address>
```

It exits 0 only when a block was accepted. Run it from a machine with several
cores: it needs roughly `2^256 / target` hashes, which on this chain is a few
seconds of pure Python, but the tip can move while it grinds, so it retries
across jobs. Each attempt is reported, including the pool's refusal.

To confirm a block really was merged-mined rather than found natively:

```sh
curl -s -X POST http://127.0.0.1:28332/rpc -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"getblock","params":["<block-hash>"]}' \
  | python3 -c 'import sys,json; print(json.load(sys.stdin)["result"]["proof_type"])'
```

`auxpow` means the proof of work came from a parent header, and the WEED header
nonce will be 0.

## Miner instructions

Give miners this info:

```
URL:    stratum+tcp://WEED public node:3333
Worker: <your-weed-address>            (add ".rig1" to name a rig)
Pass:   x  (ignored)
```

Any Bitcoin ASIC (Antminer, Whatsminer, Avalon) or CPU miner that speaks
Stratum V1 can connect.

## This bridge mines WEED only

`SimulatedParentChain` generates the parent header the ASIC hashes. That is not
a shortcut — it is what the consensus rules require: WEED validates the
parent coinbase as one of its **own** transactions, with the commitment in that
transaction's `coinbase_data` field, so a coinbase taken from a real `bitcoind`
would not parse. No BTC is mined and no BTC reward exists.

The ASIC cannot tell the difference, so this is exactly what you want for
mining WEED with Bitcoin hardware. Supporting a genuine Bitcoin parent
would mean adding a Bitcoin-format coinbase parser to the consensus validation
path — a consensus change, not a configuration option.

## Monitoring

- **Prometheus metrics** at `https://WEED public node/metrics`:
  - `weed_auxpow_blocks_total`
  - `weed_auxpow_rejections_total`
  - `weed_auxpow_submissions_total`
  - `weed_auxpow_templates_created_total`

- **Bridge logs:** `tail -f /var/log/weed/stratum.log`

- **Explorer:** AuxPoW blocks show "Proof: AuxPoW (merged-mined)" with full
  parent Bitcoin header details.

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| Bridge exits immediately | Wrong RPC token | Check `/var/lib/weed/mainnet/rpc.token` |
| "AuxPoW is not configured" | Wrong chain-id | Use `chain_id="1"` for mainnet |
| "put your WEED address in the worker name" | The miner authorised with no payout address | Use `ADDRESS` or `ADDRESS.rig1` as the username, or set `allow_pool_payout="yes"` to pay those miners the pool address |
| Miners connect but get no jobs | RPC connection lost | Check `weed_url` is reachable from localhost |
| Port 3333 closed | Firewall | `iptables -A INPUT -p tcp --dport 3333 -j ACCEPT` |

## Security notes

- **The RPC port (28332) is NOT exposed to the internet** — only Caddy (443) and localhost can reach it.  This is already the setup on the reference server.
- The bridge talks to the node directly on `127.0.0.1:28332` with the RPC token — it does not go through Caddy.
- `createauxblock` and `submitauxblock` require the token because they are MINING_METHODS, even though the node runs `--rpc-public`.
- The bridge runs as the unprivileged `weed` user.
- The OpenRC service uses `supervise-daemon` — it restarts automatically if it ever dies.