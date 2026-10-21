"""A loopback-only browser interface for the encrypted WEED wallet."""

from __future__ import annotations

import argparse
import json
import logging
import re
import threading
import time
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from scarletcoin.cli_common import DEFAULT_DATADIR, make_client
from scarletcoin.core.params import get_params, network_names
from scarletcoin.net.client import RpcClient, RpcClientError
from scarletcoin.units import format_amount, parse_amount
from scarletcoin.wallet.builder import InsufficientFundsError
from scarletcoin.wallet.cli import default_wallet_path
from scarletcoin.wallet.keystore import Keystore, WalletError
from scarletcoin.wallet.wallet import Wallet

logger = logging.getLogger(__name__)
AUTO_LOCK_SECONDS = 10 * 60
MAX_REQUEST_BYTES = 64 * 1024
WEB_PORT = 28444

_PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>WEED Wallet</title>
<style>
:root{color-scheme:dark;--bg:#0b120d;--panel:#142019;--line:#2a4131;--text:#e5f0e7;
--muted:#91a895;--green:#58d66b;--danger:#ff9a9a}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);
font:15px/1.5 system-ui,sans-serif}main{width:min(960px,calc(100% - 32px));margin:36px auto}
h1,h2{color:var(--green)}h1{margin-bottom:4px}.muted,.note{color:var(--muted)}
.panel{background:var(--panel);border:1px solid var(--line);border-radius:10px;
padding:20px;margin:16px 0}label{display:block;margin:12px 0 5px}
input,textarea,button{font:inherit;border-radius:6px;padding:10px}
input,textarea{width:100%;background:#0b120d;color:var(--text);border:1px solid var(--line)}
textarea{min-height:78px}button{border:0;background:var(--green);color:#0b120d;
font-weight:700;cursor:pointer;margin:8px 8px 0 0}
button.secondary{background:#263b2b;color:var(--text)}
button.danger{background:#6e3434;color:#fff}button:disabled{opacity:.5;cursor:wait}
.row{display:flex;gap:14px;flex-wrap:wrap}.row>*{flex:1;min-width:200px}
.notice{padding:12px;border:1px solid var(--line);border-radius:6px;white-space:pre-wrap}
.error{color:var(--danger)}.secret{border-color:#9d8b35;background:#262411}
table{width:100%;border-collapse:collapse}
th,td{text-align:left;padding:8px;border-bottom:1px solid var(--line);overflow-wrap:anywhere}
th{color:var(--muted)}
.actions{display:flex;justify-content:space-between;align-items:center}
a{color:var(--green)}
</style>
</head>
<body><main>
<h1>WEED Wallet</h1><div class="muted" id="network"></div>
<div id="notice" class="notice" hidden></div>
<section id="secret"></section>
<section id="locked"></section><section id="dashboard" hidden></section>
<script>
const $=s=>document.querySelector(s), locked=$("#locked"), dashboard=$("#dashboard");
function notice(text,error=false){const e=$("#notice");e.hidden=!text;e.textContent=text;
e.className="notice"+(error?" error":"")}
async function api(path,data){
  const options={method:data?"POST":"GET",headers:{}};
  if(data){options.headers["Content-Type"]="application/json";options.body=JSON.stringify(data)}
  const response=await fetch(path,options);const result=await response.json();
  if(!response.ok)throw Error(result.error||"Request failed");return result
}
function node(tag,text,cls){
const e=document.createElement(tag);
if(text!==undefined)e.textContent=text;
if(cls)e.className=cls;return e}
function field(form,labelText,name,type="text",required=true){
  const label=node("label",labelText);
  const input=document.createElement(type==="textarea"?"textarea":"input");
  if(type!=="textarea")input.type=type;input.name=name;input.required=required;
  form.append(label,input);return input
}
function button(form,text,cls=""){
  const b=node("button",text,cls);form.append(b);return b
}
function formPanel(title,fields,submitText,callback,extra){
  const section=node("section",undefined,"panel");section.append(node("h2",title));
  const form=document.createElement("form");for(const f of fields)field(form,...f);
  const submit=button(form,submitText);
  form.addEventListener("submit",async e=>{e.preventDefault();submit.disabled=true;notice("");
    try{await callback(Object.fromEntries(new FormData(form).entries()))}
    catch(err){notice(err.message,true)}finally{submit.disabled=false}});
  section.append(form);if(extra)section.append(extra);return section
}
function showSecret(words){
  const box=node("div",undefined,"notice secret");
  box.append(node("strong",
    "Write down this recovery phrase and keep it offline. Anyone with it can spend your coins."));
  const phrase=node("p",words);box.append(phrase);
  const copy=node("button","Copy phrase","secondary");
  copy.type="button";
  copy.addEventListener("click",async()=>{
    await navigator.clipboard.writeText(words);
    notice("Recovery phrase copied. Keep it secret.")
  });
  const hide=node("button","Hide phrase","secondary");hide.type="button";
  hide.addEventListener("click",()=>box.remove());
  box.append(copy,hide);return box
}
function newWalletPanel(){
  return formPanel("Create another wallet",[
    ["Wallet name (letters, numbers, _ or -)","name","text"],
    ["New password (at least 12 characters)","password","password"],
    ["Repeat password","confirm","password"]],
    "Create separate wallet",async data=>{
      if(data.password.length<12)throw Error("Use a password with at least 12 characters.");
      if(data.password!==data.confirm)throw Error("The passwords do not match.");
      const confirmed=window.confirm(
        "Create a separate wallet file? Your current wallet will not be overwritten."
      );
      if(!confirmed)return;
      const result=await api("/api/create-new",data);
      $("#secret").append(showSecret(result.mnemonic));
      await start();
      notice("New wallet created. Save its recovery phrase offline.")
    })
}
function walletSelector(status){
  if(status.wallets.length<2)return null;
  const section=node("section",undefined,"panel");
  section.append(node("h2","Choose wallet"));
  const form=document.createElement("form");
  const select=document.createElement("select");
  select.name="wallet";
  for(const wallet of status.wallets){
    const option=document.createElement("option");
    option.value=wallet.file;option.textContent=wallet.name;
    option.selected=wallet.file===status.file;select.append(option)
  }
  form.append(select);
  const change=button(form,"Switch wallet","secondary");
  form.addEventListener("submit",async e=>{
    e.preventDefault();change.disabled=true;
    try{await api("/api/select-wallet",{file:select.value});await start()}
    catch(err){notice(err.message,true)}finally{change.disabled=false}
  });
  section.append(form);return section
}
async function start(){
  try{
    const status=await api("/api/status");
    $("#network").textContent="Network: "+status.network
      +" · Local-only wallet · Auto-locks after 10 minutes";
    locked.replaceChildren();dashboard.replaceChildren();dashboard.hidden=true;locked.hidden=false;
    if(status.unlocked){locked.hidden=true;await renderWallet();return}
    if(status.exists){
      const selector=walletSelector(status);if(selector)locked.append(selector);
      locked.append(formPanel("Unlock wallet",[["Wallet password","password","password"]],
        "Unlock",async data=>{await api("/api/unlock",data);await start()}));
      locked.append(node(
        "p",
        "Wallet files must be encrypted. For an unencrypted wallet, first set a password "
          +"with weed-wallet password.",
        "note"
      ));
      locked.append(newWalletPanel());
    }else{
      locked.append(formPanel("Create wallet",[
        ["New password (at least 12 characters)","password","password"],
        ["Repeat password","password","confirm"]],
        "Create encrypted wallet",async data=>{
          if(data.password.length<12)throw Error("Use a password with at least 12 characters.");
          if(data.password!==data.confirm)throw Error("The passwords do not match.");
          const result=await api("/api/create",data);
          $("#secret").append(showSecret(result.mnemonic));
          await start();
          notice("Wallet created. Save the recovery phrase before closing this page.")
        }));
      const restore=node("section",undefined,"panel");restore.append(node("h2","Restore wallet"));
      const form=document.createElement("form");
      field(form,"Recovery phrase","mnemonic","textarea");
      field(form,"New wallet password (at least 12 characters)","password","password");
      field(form,"Repeat password","confirm","password");
      const submit=button(form,"Restore encrypted wallet");
      form.addEventListener("submit",async e=>{e.preventDefault();submit.disabled=true;
        try{const data=Object.fromEntries(new FormData(form).entries());
          if(data.password.length<12)throw Error("Use a password with at least 12 characters.");
          if(data.password!==data.confirm)throw Error("The passwords do not match.");
          await api("/api/restore",data);
          await start();
          notice("Wallet restored. The phrase is not stored in this browser.")
        }catch(err){notice(err.message,true)}finally{submit.disabled=false}});
      restore.append(form);locked.append(restore)
    }
  }catch(err){notice(err.message,true)}
}
async function renderWallet(){
  const [data,status]=await Promise.all([api("/api/wallet"),api("/api/status")]);
  dashboard.replaceChildren();dashboard.hidden=false;
  const selector=walletSelector(status);if(selector)dashboard.append(selector);
  const summary=node("section",undefined,"panel");
  summary.append(node("h2","Balance"));
  summary.append(node("p",`Spendable: ${data.balance.spendable} WEED`));
  summary.append(node(
    "p",
    `Total: ${data.balance.confirmed} WEED · Immature: ${data.balance.immature} WEED`
  ));
  summary.append(node("p",`Node height: ${data.height}`,"muted"));
  const actions=node("div",undefined,"actions");
  actions.append(node("span","Your keys stay in the encrypted local wallet file."));
  const lock=node("button","Lock wallet","secondary");
  lock.addEventListener("click",async()=>{
    await api("/api/lock",{});
    await start()
  });
  actions.append(lock);summary.append(actions);dashboard.append(summary);
  const addresses=node("section",undefined,"panel");addresses.append(node("h2","Addresses"));
  const table=document.createElement("table"),head=document.createElement("tr");
  for(const name of ["Address","Label","Balance (WEED)"])head.append(node("th",name));
  table.append(head);for(const item of data.addresses){const row=document.createElement("tr");
    for(const value of [item.address,item.label,item.balance])row.append(node("td",value));
    table.append(row)}addresses.append(table);
  const newForm=document.createElement("form");
  field(newForm,"Label (optional)","label","text",false);
  const newButton=button(newForm,"Create address");
  newForm.addEventListener("submit",async e=>{
    e.preventDefault();newButton.disabled=true;
    try{
      await api("/api/address",Object.fromEntries(new FormData(newForm).entries()));
      await start()
    }catch(err){notice(err.message,true)}finally{newButton.disabled=false}
  });
  addresses.append(newForm);dashboard.append(addresses);
  dashboard.append(newWalletPanel());
  dashboard.append(formPanel("Send WEED",[
    ["Destination WEED address","address","text"],
    ["Amount in WEED (or 'all')","amount","text"],
    ["Fee rate (scar per kB; blank uses network default)","fee_rate","number",false]],
    "Review and send",async fields=>{
      if(!window.confirm(`Send ${fields.amount} WEED to ${fields.address}?`))return;
      const result=await api("/api/send",fields);
      notice("Broadcast transaction(s): "+result.txids.join(", ")+" · Fee: "+result.fee+" WEED");
      await start()
    }));
  const history=node("section",undefined,"panel");history.append(node("h2","Recent history"));
  const historyTable=document.createElement("table"),historyHead=document.createElement("tr");
  for(const name of ["Height","Net (WEED)","Confirmations","Transaction"])
    historyHead.append(node("th",name));
  historyTable.append(historyHead);
  for(const tx of data.history){const row=document.createElement("tr");
    for(const value of [tx.height||"Pending",tx.net,tx.confirmations,tx.txid]){
      const cell=node("td",value);row.append(cell)}historyTable.append(row)}
  history.append(historyTable);dashboard.append(history)
}
start();setInterval(async()=>{try{const s=await api("/api/status");
  if((s.unlocked&&dashboard.hidden)||(!s.unlocked&&!dashboard.hidden))await start()
}catch(err){notice(err.message,true)}},30000);
</script></main></body></html>"""


class WalletWebApp:
    """Own the encrypted wallet state and its RPC connection."""

    def __init__(self, path: Path, network: str, client: RpcClient) -> None:
        self.path = path
        self.default_path = path
        self.network = network
        self.params = get_params(network)
        self.client = client
        self.keystore: Keystore | None = None
        self.wallet: Wallet | None = None
        self._last_activity = 0.0
        self._lock = threading.RLock()

    @property
    def unlocked(self) -> bool:
        self._expire()
        return self.wallet is not None

    def _expire(self) -> None:
        if self.wallet is not None and time.monotonic() - self._last_activity >= AUTO_LOCK_SECONDS:
            self.lock()

    def _touch(self) -> Wallet:
        self._expire()
        if self.wallet is None:
            raise WalletError("unlock the wallet first")
        self._last_activity = time.monotonic()
        return self.wallet

    def lock(self) -> None:
        if self.keystore is not None:
            self.keystore.lock()
        self.wallet = None
        self.keystore = None

    def status(self) -> dict:
        self._expire()
        paths = []
        if self.default_path.is_file():
            paths.append(self.default_path)
        paths.extend(
            path
            for path in sorted(self.default_path.parent.glob("wallet-*.json"))
            if path.is_file() and path != self.default_path
        )
        return {
            "network": self.network,
            "exists": self.path.exists(),
            "unlocked": self.wallet is not None,
            "file": self.path.name,
            "wallets": [
                {
                    "file": path.name,
                    "name": "Main wallet" if path == self.default_path else path.stem[7:],
                }
                for path in paths
            ],
        }

    def select_wallet(self, filename: str) -> dict:
        if filename != self.default_path.name and not re.fullmatch(
            r"wallet-[A-Za-z0-9_-]{1,32}\.json", filename
        ):
            raise WalletError("invalid wallet selection")
        path = self.default_path.with_name(filename)
        if not path.is_file():
            raise WalletError("wallet file does not exist")
        self.lock()
        self.path = path
        return {"ok": True}

    def _check_network(self, keystore: Keystore) -> None:
        if keystore.params.name != self.network:
            raise WalletError(
                f"wallet belongs to {keystore.params.name}, not the selected {self.network} network"
            )

    def create(self, password: str) -> dict:
        if len(password) < 12:
            raise WalletError("use a password with at least 12 characters")
        if self.path.exists():
            raise WalletError("wallet already exists; refusing to overwrite it")
        keystore = Keystore.create(self.path, self.network, password=password)
        mnemonic = keystore.new_mnemonic
        keystore.new_mnemonic = None
        self.keystore = keystore
        self.wallet = Wallet(keystore, self.client)
        self._last_activity = time.monotonic()
        return {"mnemonic": mnemonic}

    def create_new(self, name: str, password: str) -> dict:
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,32}", name):
            raise WalletError("wallet name must use 1-32 letters, numbers, '_' or '-'")
        path = self.default_path.with_name(f"wallet-{name}.json")
        if path == self.path:
            raise WalletError("choose a different wallet name")
        if len(password) < 12:
            raise WalletError("use a password with at least 12 characters")
        if path.exists():
            raise WalletError(f"wallet {name!r} already exists; choose another name")
        keystore = Keystore.create(path, self.network, password=password)
        mnemonic = keystore.new_mnemonic
        keystore.new_mnemonic = None
        self.lock()
        self.path = path
        self.keystore = keystore
        self.wallet = Wallet(keystore, self.client)
        self._last_activity = time.monotonic()
        return {"mnemonic": mnemonic}

    def restore(self, password: str, mnemonic: str) -> None:
        if len(password) < 12:
            raise WalletError("use a password with at least 12 characters")
        if self.path.exists():
            raise WalletError("wallet already exists; refusing to overwrite it")
        keystore = Keystore.restore(self.path, self.network, mnemonic, password=password)
        self._check_network(keystore)
        keystore.new_mnemonic = None
        self.keystore = keystore
        self.wallet = Wallet(keystore, self.client)
        self._last_activity = time.monotonic()

    def unlock(self, password: str) -> None:
        keystore = Keystore.load(self.path, password=password)
        self._check_network(keystore)
        if not keystore.encrypted:
            raise WalletError(
                "wallet is not password-protected; set a password with weed-wallet password first"
            )
        if keystore.locked:
            raise WalletError("wallet could not be unlocked")
        self.keystore = keystore
        self.wallet = Wallet(keystore, self.client)
        self._last_activity = time.monotonic()

    def wallet_data(self) -> dict:
        wallet = self._touch()
        balance = wallet.balance()
        addresses = [
            {"address": address, "label": label, "balance": format_amount(amount)}
            for address, label, amount in wallet.balances_by_address()
        ]
        history = [
            {
                "height": item["height"],
                "net": format_amount(item["net"]),
                "confirmations": item["confirmations"],
                "txid": item["txid"],
            }
            for item in wallet.history(25)
        ]
        info = self.client.getinfo()
        if info.get("genesis") != self.params.genesis_hash[::-1].hex():
            raise RpcClientError(f"the connected node is not on {self.network}")
        return {
            "balance": {
                "confirmed": format_amount(balance.confirmed),
                "spendable": format_amount(balance.spendable),
                "immature": format_amount(balance.immature),
            },
            "addresses": addresses,
            "history": history,
            "height": info["height"],
        }

    def new_address(self, label: str) -> dict:
        wallet = self._touch()
        address = wallet.new_address(label[:80])
        return {"address": address}

    def send(self, address: str, amount_text: str, fee_rate: str = "") -> dict:
        wallet = self._touch()
        amount_text = amount_text.strip()
        fee_per_kb = int(fee_rate) if fee_rate.strip() else None
        if fee_per_kb is not None and not 1 <= fee_per_kb <= 10_000_000:
            raise ValueError("fee rate must be between 1 and 10,000,000 scar per kB")
        if amount_text.lower() == "all":
            results = wallet.send_everything(address, fee_per_kb=fee_per_kb)
        else:
            amount = parse_amount(amount_text)
            results = [wallet.send(address, amount, fee_per_kb=fee_per_kb)]
        return {
            "txids": [result.txid for result in results],
            "fee": format_amount(sum(result.fee for result in results)),
        }


def _handler(app: WalletWebApp):
    class Handler(BaseHTTPRequestHandler):
        server_version = "WEED-Wallet"
        sys_version = ""

        def log_message(self, _format: str, *_args: object) -> None:
            return

        def _headers(self) -> None:
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("X-Frame-Options", "DENY")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header(
                "Content-Security-Policy",
                "default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; "
                "connect-src 'self'; form-action 'self'; base-uri 'none'; frame-ancestors 'none'",
            )

        def _send(self, status: HTTPStatus, body: bytes, content_type: str) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self._headers()
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(body)

        def _json(self, value: object, status: HTTPStatus = HTTPStatus.OK) -> None:
            self._send(
                status,
                json.dumps(value, separators=(",", ":")).encode("utf-8"),
                "application/json; charset=utf-8",
            )

        def _local_host(self) -> bool:
            try:
                host = urlsplit(f"//{self.headers.get('Host', '')}")
                return (
                    host.hostname in {"127.0.0.1", "localhost"}
                    and host.port == self.server.server_address[1]
                )
            except ValueError:
                return False

        def _same_origin_post(self) -> bool:
            origin = self.headers.get("Origin")
            if not origin or not self._local_host():
                return False
            parsed = urlsplit(origin)
            return (
                parsed.scheme == "http"
                and parsed.hostname in {"127.0.0.1", "localhost"}
                and parsed.netloc.lower() == self.headers.get("Host", "").lower()
            )

        def _body(self) -> dict:
            if self.headers.get_content_type() != "application/json":
                raise ValueError("request must use application/json")
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError as exc:
                raise ValueError("invalid Content-Length") from exc
            if length <= 0 or length > MAX_REQUEST_BYTES:
                raise ValueError("request body is empty or too large")
            try:
                value = json.loads(self.rfile.read(length).decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise ValueError("invalid JSON request") from exc
            if not isinstance(value, dict):
                raise ValueError("request must be a JSON object")
            return value

        def do_GET(self) -> None:
            if not self._local_host():
                self._json({"error": "local access only"}, HTTPStatus.FORBIDDEN)
            elif self.path == "/":
                self._send(HTTPStatus.OK, _PAGE.encode("utf-8"), "text/html; charset=utf-8")
            elif self.path == "/api/status":
                with app._lock:
                    self._json(app.status())
            elif self.path == "/api/wallet":
                self._wallet_action(app.wallet_data)
            else:
                self._json({"error": "not found"}, HTTPStatus.NOT_FOUND)

        def do_POST(self) -> None:
            if not self._same_origin_post():
                self._json({"error": "same-origin local requests only"}, HTTPStatus.FORBIDDEN)
                return
            try:
                data = self._body()
                routes = {
                    "/api/create": lambda: app.create(str(data.get("password", ""))),
                    "/api/create-new": lambda: app.create_new(
                        str(data.get("name", "")), str(data.get("password", ""))
                    ),
                    "/api/select-wallet": lambda: app.select_wallet(
                        str(data.get("file", ""))
                    ),
                    "/api/restore": lambda: app.restore(
                        str(data.get("password", "")), str(data.get("mnemonic", ""))
                    ) or {"ok": True},
                    "/api/unlock": lambda: app.unlock(str(data.get("password", "")))
                    or {"ok": True},
                    "/api/lock": lambda: app.lock() or {"ok": True},
                    "/api/address": lambda: app.new_address(str(data.get("label", ""))),
                    "/api/send": lambda: app.send(
                        str(data.get("address", "")),
                        str(data.get("amount", "")),
                        str(data.get("fee_rate", "")),
                    ),
                }
                action = routes.get(self.path)
                if action is None:
                    self._json({"error": "not found"}, HTTPStatus.NOT_FOUND)
                    return
                with app._lock:
                    self._json(action())
            except (WalletError, RpcClientError, InsufficientFundsError, ValueError) as exc:
                self._json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
            except OSError as exc:
                logger.exception("wallet web request failed")
                self._json(
                    {"error": f"wallet file operation failed: {exc}"},
                    HTTPStatus.INTERNAL_SERVER_ERROR,
                )

        def _wallet_action(self, action) -> None:
            try:
                with app._lock:
                    self._json(action())
            except (WalletError, RpcClientError, InsufficientFundsError, ValueError) as exc:
                self._json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)

        def do_HEAD(self) -> None:
            self.do_GET()

    return Handler


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="weed-wallet-web",
        description="Run a local-only browser interface for an encrypted WEED wallet.",
    )
    parser.add_argument("--network", default="mainnet", choices=network_names())
    parser.add_argument("--datadir", type=Path, default=DEFAULT_DATADIR)
    parser.add_argument("--wallet", type=Path, help="wallet file path")
    parser.add_argument("--rpc-url", help="node RPC URL")
    parser.add_argument("--rpc-token", help="node RPC token")
    parser.add_argument(
        "--no-browser", action="store_true", help=argparse.SUPPRESS
    )
    args = parser.parse_args(argv)

    path = args.wallet or default_wallet_path(args.datadir, args.network)
    client_args = argparse.Namespace(
        network=args.network,
        datadir=args.datadir,
        rpc_url=args.rpc_url,
        rpc_token=args.rpc_token,
        timeout=10.0,
    )
    app = WalletWebApp(path, args.network, make_client(client_args))
    server = ThreadingHTTPServer(("127.0.0.1", WEB_PORT), _handler(app))
    server.daemon_threads = True
    url = f"http://127.0.0.1:{server.server_address[1]}/"
    print(f"WEED browser wallet: {url}")
    print("Local computer only. Keep this terminal open; press Ctrl+C to stop.")
    if not args.no_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping WEED browser wallet.")
    finally:
        app.lock()
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
