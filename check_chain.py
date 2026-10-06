import os
import sys

from node import WeedNode


if len(sys.argv) != 2:

    print("Usage: python check_chain.py DATA_DIR")
    sys.exit(1)


data_dir = sys.argv[1]

os.environ["WEED_DATA_DIR"] = data_dir


node = WeedNode()


print()
print("================================")
print("       WEED CHAIN CHECK")
print("================================")

print()
print("Data directory:")
print(data_dir)

print()
print("Blocks:")
print(len(node.chain))

valid = True


for index, block in enumerate(node.chain):

    calculated_hash = block.calculate_hash()

    if calculated_hash != block.hash:

        print()
        print("INVALID BLOCK:")
        print(block.index)

        print()
        print("Stored hash:")
        print(block.hash)

        print()
        print("Calculated hash:")
        print(calculated_hash)

        valid = False

        break

    if index == 0:

        if block.index != 0:
            print("Invalid genesis index")
            valid = False
            break

        if block.previous_hash != "0":
            print("Invalid genesis previous hash")
            valid = False
            break

        continue

    previous_block = node.chain[index - 1]

    if block.index != previous_block.index + 1:

        print()
        print("Invalid block index:")
        print(block.index)

        valid = False

        break

    if block.previous_hash != previous_block.hash:

        print()
        print("Invalid previous hash at block:")
        print(block.index)

        valid = False

        break


print()

if valid:

    print("================================")
    print("       BLOCKCHAIN VALID")
    print("================================")

else:

    print("================================")
    print("       BLOCKCHAIN INVALID")
    print("================================")

    sys.exit(1)
