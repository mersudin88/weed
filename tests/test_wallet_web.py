from __future__ import annotations

import http.client
import io
import json
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from urllib.error import URLError

import pytest

from scarletcoin.core.params import REGTEST
from scarletcoin.crypto.keys import PrivateKey
from scarletcoin.net import rpc as rpc_module
from scarletcoin.net.client import RpcClient
from scarletcoin.wallet.keystore import Keystore, WalletError
from scarletcoin.wallet.web import AUTO_LOCK_SECONDS, WalletWebApp, _handler


def test_wallet_web_creates_encrypted_wallet_and_locks(tmp_path, monkeypatch):
    password = "correct horse battery staple"
    app = WalletWebApp(tmp_path / "wallet.json", "regtest", RpcClient("http://127.0.0.1:40332"))

    result = app.create(password)
    assert len(result["mnemonic"].split()) == 12
    assert app.unlocked
    app.lock()
    assert not app.unlocked

    with pytest.raises(WalletError, match="wrong password"):
        app.unlock("incorrect password")

    app.unlock(password)
    assert app.unlocked
    monkeypatch.setattr(
        "scarletcoin.wallet.web.time.monotonic",
        lambda: app._last_activity + AUTO_LOCK_SECONDS,
    )
    assert not app.unlocked


def test_wallet_web_reads_and_sends_through_node(tmp_path, rpc):
    _, _, client = rpc
    path = tmp_path / "wallet.json"
    app = WalletWebApp(path, "regtest", client)
    app.create("correct horse battery staple")
    address = app.wallet.keystore.default_address()
    client.call("generate", 3, address)

    data = app.wallet_data()
    assert data["balance"]["spendable"] == "100"

    destination = str(PrivateKey.generate().address(REGTEST.address_version))
    result = app.send(destination, "1.25")
    assert len(result["txids"]) == 1
    assert result["fee"]
    assert client.call("gettransaction", result["txids"][0])["txid"] == result["txids"][0]


def test_wallet_web_refuses_wrong_network(tmp_path):
    path = tmp_path / "wallet.json"
    Keystore.create(path, "regtest", password="correct horse battery staple")
    app = WalletWebApp(path, "testnet", RpcClient("http://127.0.0.1:30332"))
    with pytest.raises(WalletError, match="belongs to regtest"):
        app.unlock("correct horse battery staple")


def test_wallet_web_creates_named_wallet_without_overwriting_default(tmp_path):
    path = tmp_path / "wallet.json"
    app = WalletWebApp(path, "regtest", RpcClient("http://127.0.0.1:40332"))
    app.create("default password phrase")
    default_address = app.wallet.keystore.default_address()

    created = app.create_new("savings", "savings password phrase")
    named_path = tmp_path / "wallet-savings.json"
    assert len(created["mnemonic"].split()) == 12
    assert path.is_file() and named_path.is_file()
    assert app.path == named_path
    assert app.status()["wallets"] == [
        {"file": "wallet.json", "name": "Main wallet"},
        {"file": "wallet-savings.json", "name": "savings"},
    ]

    app.select_wallet("wallet.json")
    app.unlock("default password phrase")
    assert app.wallet.keystore.default_address() == default_address
    with pytest.raises(WalletError, match="already exists"):
        app.create_new("savings", "another password phrase")
    with pytest.raises(WalletError, match="wallet name"):
        app.create_new("../outside", "another password phrase")


def test_wallet_web_http_is_local_and_same_origin(tmp_path):
    app = WalletWebApp(tmp_path / "wallet.json", "regtest", RpcClient("http://127.0.0.1:40332"))
    server = ThreadingHTTPServer(("127.0.0.1", 0), _handler(app))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    url = f"http://127.0.0.1:{server.server_address[1]}"
    try:
        with urllib.request.urlopen(url + "/api/status", timeout=5) as response:
            assert response.status == 200
            assert response.headers["Cache-Control"] == "no-store"
            assert json.load(response)["network"] == "regtest"

        request = urllib.request.Request(
            url + "/api/lock",
            data=b"{}",
            headers={
                "Content-Type": "application/json",
                "Origin": "http://attacker.example",
            },
            method="POST",
        )
        with pytest.raises(urllib.error.HTTPError) as error:
            urllib.request.urlopen(request, timeout=5)
        assert error.value.code == 403

        request = urllib.request.Request(
            url + "/api/create",
            data=json.dumps({"password": "correct horse battery staple"}).encode(),
            headers={
                "Content-Type": "application/json",
                "Origin": url,
            },
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            created = json.load(response)
        assert len(created["mnemonic"].split()) == 12

        with urllib.request.urlopen(url + "/api/status", timeout=5) as response:
            status = json.load(response)
        assert status["unlocked"]

        request = urllib.request.Request(
            url + "/api/status",
            headers={"Host": f"attacker.example:{server.server_address[1]}"},
        )
        with pytest.raises(urllib.error.HTTPError) as error:
            urllib.request.urlopen(request, timeout=5)
        assert error.value.code == 403
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()


def test_explorer_wallet_link_starts_wallet_and_redirects(rpc, monkeypatch):
    _, server, _ = rpc
    called = []
    monkeypatch.setattr(server, "_ensure_wallet_web", lambda: called.append(True))
    connection = http.client.HTTPConnection("127.0.0.1", server.port, timeout=5)
    try:
        connection.request("GET", "/wallet")
        response = connection.getresponse()
        assert response.status == 303
        assert response.getheader("Location") == rpc_module.WALLET_WEB_URL
        assert called == [True]
    finally:
        connection.close()


def test_explorer_wallet_link_rejects_nonlocal_host(rpc, monkeypatch):
    _, server, _ = rpc
    called = []
    monkeypatch.setattr(server, "_ensure_wallet_web", lambda: called.append(True))
    connection = http.client.HTTPConnection("127.0.0.1", server.port, timeout=5)
    try:
        connection.request(
            "GET",
            "/wallet",
            headers={"Host": f"attacker.example:{server.port}"},
        )
        response = connection.getresponse()
        assert response.status == 403
        assert called == []
    finally:
        connection.close()


def test_node_starts_wallet_subprocess_when_not_already_running(rpc, monkeypatch):
    node, server, _ = rpc
    responses = [URLError("not running"), b'{"network":"regtest"}']
    requests = []

    def wallet_status(url, *, timeout):
        requests.append((url, timeout))
        result = responses.pop(0)
        if isinstance(result, Exception):
            raise result
        return io.BytesIO(result)

    monkeypatch.setattr(rpc_module, "urlopen", wallet_status)
    started = []

    class Process:
        terminated = False

        def poll(self):
            return 0 if self.terminated else None

        def terminate(self):
            self.terminated = True

        def wait(self, timeout):
            return 0

    def start_process(command, *, stdin):
        started.append((command, stdin))
        return Process()

    monkeypatch.setattr(rpc_module.subprocess, "Popen", start_process)
    server._ensure_wallet_web()
    assert len(started) == 1
    command, stdin = started[0]
    assert command[command.index("--network") + 1] == "regtest"
    assert command[command.index("--datadir") + 1] == str(node.config.datadir)
    assert command[command.index("--rpc-url") + 1] == server.url
    assert "--no-browser" in command
    assert stdin == rpc_module.subprocess.DEVNULL
    assert len(requests) == 2
