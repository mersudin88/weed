import os
import sys
import subprocess


if len(sys.argv) != 2:
    print("Usage: python run_node.py PORT")
    sys.exit(1)


port = int(sys.argv[1])


if port == 5000:

    data_dir = "node_a"
    wallet_file = "wallet.json"

elif port == 5001:

    data_dir = "node_b"
    wallet_file = "wallet_b.json"

else:

    print("Only ports 5000 and 5001 are supported.")
    sys.exit(1)


os.environ["WEED_DATA_DIR"] = data_dir
os.environ["WEED_WALLET_FILE"] = wallet_file


print()
print("================================")
print("        WEED NODE LAUNCHER")
print("================================")

print()
print("Port:")
print(port)

print()
print("Data directory:")
print(data_dir)

print()
print("Wallet file:")
print(wallet_file)


subprocess.run(
    [sys.executable, "p2p_server.py", str(port)],
    env=os.environ
)
