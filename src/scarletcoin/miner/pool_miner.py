"""Stratum V1 pool miner for the WEED 80-byte proof-of-work header."""

from __future__ import annotations

import hashlib
import json
import multiprocessing
import select
import socket
import threading
import time
from urllib.parse import urlparse

from scarletcoin.miner.solver import compile_native, scan_nonces


def _scan_nonce_task(args):
    """Scan one independent nonce range in a worker process."""
    header, target, start, count = args
    result = scan_nonces(header, target, start=start, count=count)
    return result.nonce, int(result.hashes)


DIFF1_TARGET = 0x00000000FFFF0000_000000000000000000000000000000000000000000000000


def hash256(data: bytes) -> bytes:
    return hashlib.sha256(hashlib.sha256(data).digest()).digest()


def unswap_prevhash(raw: bytes) -> bytes:
    if len(raw) != 32:
        raise ValueError(f"Stratum previous hash must be 32 bytes, got {len(raw)}")
    return b"".join(raw[i:i + 4][::-1] for i in range(0, 32, 4))


class PoolMiner:
    """A stoppable Stratum client that uses the project's existing nonce scanner."""

    def __init__(
        self,
        pool_url: str,
        payout_address: str,
        worker_name: str = "rig1",
        password: str = "x",
        on_event=None,
        batch_size: int = 65536,
        workers: int = 1,
    ):
        self.pool_url = pool_url
        self.payout_address = payout_address.strip()
        self.worker_name = worker_name.strip() or "rig1"
        self.password = password
        self.on_event = on_event or (lambda *_args, **_kwargs: None)
        self.batch_size = max(1024, int(batch_size))
        self.workers = max(1, min(64, int(workers)))
        self._stop = threading.Event()
        self._sock = None
        self._buffer = b""
        self._next_id = 0
        self._responses = {}
        self._job = None
        self._job_generation = 0
        self._difficulty = 1.0
        self._extranonce1 = ""
        self._extranonce2_size = 4
        self._extranonce_counter = 0
        self.hashes = 0
        self.accepted = 0
        self.rejected = 0
        self.last_rate = 0.0
        self.average_rate = 0.0
        self._started_at = None
        self._last_rate_at = None
        self._last_rate_hashes = 0

    def _emit(self, event: str, **data):
        try:
            self.on_event(event, **data)
        except Exception:
            pass

    def stop(self):
        self._stop.set()
        try:
            if self._sock:
                self._sock.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass

    def _send(self, method: str, params=None) -> int:
        self._next_id += 1
        msg = {
            "id": self._next_id,
            "method": method,
            "params": [] if params is None else params,
        }
        payload = (json.dumps(msg, separators=(",", ":")) + "\n").encode()
        self._sock.sendall(payload)
        return self._next_id

    def _read_messages(self, timeout=0.25):
        """Read any complete newline-delimited JSON messages without blocking long."""
        readable, _, _ = select.select([self._sock], [], [], timeout)
        if readable:
            chunk = self._sock.recv(65536)
            if not chunk:
                raise ConnectionError("Pool closed the Stratum connection")
            self._buffer += chunk

        messages = []
        while b"\n" in self._buffer:
            line, self._buffer = self._buffer.split(b"\n", 1)
            if line.strip():
                messages.append(json.loads(line))
        return messages

    def _handle_message(self, msg):
        msg_id = msg.get("id")
        if msg_id is not None:
            self._responses[msg_id] = msg
            return

        method = msg.get("method")
        params = msg.get("params") or []

        if method == "mining.set_difficulty":
            difficulty = float(params[0])
            if difficulty > 0:
                self._difficulty = difficulty
                self._emit("difficulty", difficulty=difficulty)

        elif method == "mining.notify":
            if len(params) < 9:
                self._emit("error", message="Pool sent an incomplete mining.notify job")
                return
            self._job = {
                "job_id": str(params[0]),
                "prev_hash": str(params[1]),
                "coinbase1": str(params[2]),
                "coinbase2": str(params[3]),
                "branches": list(params[4]),
                "version": str(params[5]),
                "nbits": str(params[6]),
                "ntime": str(params[7]),
                "clean": bool(params[8]),
            }
            self._job_generation += 1
            if self._job["clean"]:
                self._extranonce_counter = 0
            self._emit("job", job_id=self._job["job_id"])

        elif method == "client.show_message":
            self._emit("message", message=str(params[0]) if params else "")

    def _pump(self, timeout=0.25):
        for msg in self._read_messages(timeout):
            self._handle_message(msg)

    def _wait_response(self, wanted_id, timeout=15.0):
        deadline = time.monotonic() + timeout
        while not self._stop.is_set() and time.monotonic() < deadline:
            response = self._responses.pop(wanted_id, None)
            if response is not None:
                if response.get("error"):
                    raise RuntimeError(f"Stratum request failed: {response['error']}")
                return response
            self._pump(0.2)
        raise TimeoutError(f"Timed out waiting for Stratum response id {wanted_id}")

    def _connect(self):
        parsed = urlparse(self.pool_url)
        if parsed.scheme not in ("stratum+tcp", "stratum", "tcp"):
            raise ValueError("Pool URL must start with stratum+tcp://")
        if not parsed.hostname or not parsed.port:
            raise ValueError("Pool URL must include a hostname and port")

        self._sock = socket.create_connection(
            (parsed.hostname, parsed.port), timeout=10
        )
        self._sock.setblocking(True)
        self._emit("status", message=f"Connected to {parsed.hostname}:{parsed.port}")

        subscribe_id = self._send("mining.subscribe", ["weed-linux-miner/1.0"])
        response = self._wait_response(subscribe_id)
        result = response.get("result")
        if not isinstance(result, list) or len(result) < 3:
            raise RuntimeError(f"Unexpected mining.subscribe response: {result!r}")

        self._extranonce1 = str(result[1])
        self._extranonce2_size = int(result[2])
        if self._extranonce2_size <= 0 or self._extranonce2_size > 16:
            raise RuntimeError(f"Unsupported extranonce2 size: {self._extranonce2_size}")

        username = self.payout_address
        if "." not in username:
            username = f"{username}.{self.worker_name}"

        auth_id = self._send("mining.authorize", [username, self.password])
        auth_response = self._wait_response(auth_id)
        if auth_response.get("result") is not True:
            raise RuntimeError(f"Pool rejected worker authorization: {auth_response!r}")

        self._emit("status", message=f"Authorized worker {username}")

    def _make_header_prefix(self, job, extranonce2, ntime):
        coinbase = bytes.fromhex(
            job["coinbase1"] + self._extranonce1 + extranonce2 + job["coinbase2"]
        )
        root = hash256(coinbase)
        for sibling_hex in job["branches"]:
            sibling = bytes.fromhex(sibling_hex)
            if len(sibling) != 32:
                raise ValueError("Pool supplied an invalid Merkle branch")
            root = hash256(root + sibling)

        prefix = (
            int(job["version"], 16).to_bytes(4, "little")
            + unswap_prevhash(bytes.fromhex(job["prev_hash"]))
            + root
            + ntime.to_bytes(4, "little")
            + int(job["nbits"], 16).to_bytes(4, "little")
        )
        if len(prefix) != 76:
            raise ValueError(f"Invalid block header prefix length: {len(prefix)}")
        return prefix

    def _update_rate(self):
        now = time.monotonic()
        if self._started_at is None:
            self._started_at = now
            self._last_rate_at = now
            return

        elapsed = now - self._last_rate_at
        if elapsed >= 1.0:
            delta = self.hashes - self._last_rate_hashes
            self.last_rate = delta / elapsed
            total_elapsed = max(now - self._started_at, 0.001)
            self.average_rate = self.hashes / total_elapsed
            self._last_rate_at = now
            self._last_rate_hashes = self.hashes
            self._emit(
                "rate",
                hashes=self.hashes,
                last_rate=self.last_rate,
                average_rate=self.average_rate,
                accepted=self.accepted,
                rejected=self.rejected,
            )

    def _run_session(self, worker_pool):
        self._connect()
        self._emit("status", message="Waiting for a mining job")
        nonce = 0
        generation = -1
        extranonce2_value = 0
        prefix = None
        job = None
        ntime = 0

        while not self._stop.is_set():
            self._pump(0.05)
            if self._job is None:
                continue

            if generation != self._job_generation:
                job = dict(self._job)
                generation = self._job_generation
                nonce = 0
                extranonce2_value = self._extranonce_counter
                ntime = int(job["ntime"], 16)
                prefix = self._make_header_prefix(
                    job,
                    extranonce2_value.to_bytes(
                        self._extranonce2_size, "big"
                    ).hex(),
                    ntime,
                )
                self._emit("status", message=f"Mining job {job['job_id']}")

            if prefix is None or job is None:
                continue

            target = max(1, int(DIFF1_TARGET / self._difficulty))
            count = min(self.batch_size, 0x100000000 - nonce)
            if count <= 0:
                self._extranonce_counter += 1
                extranonce2_value = self._extranonce_counter
                nonce = 0
                prefix = self._make_header_prefix(
                    job,
                    extranonce2_value.to_bytes(
                        self._extranonce2_size, "big"
                    ).hex(),
                    ntime,
                )
                continue

            header = prefix + bytes(4)
            if worker_pool is None:
                result = scan_nonces(header, target, start=nonce, count=count)
                hashes_done = int(result.hashes)
                found_nonce = result.nonce
            else:
                workers = min(self.workers, count)
                base, extra = divmod(count, workers)
                tasks = []
                offset = nonce
                for i in range(workers):
                    size = base + (1 if i < extra else 0)
                    tasks.append((header, target, offset, size))
                    offset += size
                results = worker_pool.map(_scan_nonce_task, tasks)
                hashes_done = sum(item[1] for item in results)
                found = [item[0] for item in results if item[0] is not None]
                found_nonce = min(found) if found else None

            self.hashes += hashes_done
            nonce = nonce + count if found_nonce is None else int(found_nonce) + 1
            self._update_rate()

            # Process notifications before submitting work for an old job.
            self._pump(0.0)
            if generation != self._job_generation:
                continue
            if found_nonce is None:
                continue

            nonce_found = int(found_nonce)
            extranonce2_hex = extranonce2_value.to_bytes(
                self._extranonce2_size, "big"
            ).hex()
            submit_id = self._send(
                "mining.submit",
                [
                    self.payout_address + "." + self.worker_name,
                    job["job_id"],
                    extranonce2_hex,
                    f"{ntime:08x}",
                    f"{nonce_found:08x}",
                ],
            )
            response = self._wait_response(submit_id, timeout=20)
            if response.get("result") is True:
                self.accepted += 1
                self._emit(
                    "accepted",
                    job_id=job["job_id"],
                    nonce=f"{nonce_found:08x}",
                    accepted=self.accepted,
                    rejected=self.rejected,
                )
            else:
                self.rejected += 1
                self._emit(
                    "rejected",
                    job_id=job["job_id"],
                    nonce=f"{nonce_found:08x}",
                    error=response.get("error"),
                    accepted=self.accepted,
                    rejected=self.rejected,
                )

    def run(self):
        worker_pool = None
        delay = 1
        try:
            if self.workers > 1:
                compile_native()
                worker_pool = multiprocessing.get_context("spawn").Pool(
                    self.workers
                )

            while not self._stop.is_set():
                try:
                    self._run_session(worker_pool)
                    if self._stop.is_set():
                        break
                    raise ConnectionError("Stratum session ended")
                except Exception as exc:
                    if self._stop.is_set():
                        break
                    self._emit(
                        "error",
                        message=f"Pool connection lost: {exc}. "
                                f"Reconnecting in {delay}s",
                    )
                    try:
                        if self._sock:
                            self._sock.close()
                    except OSError:
                        pass
                    self._sock = None
                    self._buffer = b""
                    self._responses.clear()
                    self._job = None
                    self._job_generation = 0
                    self._difficulty = 1.0

                    # Wait interruptibly so Stop still works.
                    if self._stop.wait(delay):
                        break
                    delay = min(delay * 2, 30)
                else:
                    delay = 1
        except Exception as exc:
            if not self._stop.is_set():
                self._emit("error", message=str(exc))
        finally:
            if worker_pool is not None:
                worker_pool.terminate()
                worker_pool.join()
            try:
                if self._sock:
                    self._sock.close()
            except OSError:
                pass
            self._emit(
                "stopped",
                hashes=self.hashes,
                accepted=self.accepted,
                rejected=self.rejected,
            )
