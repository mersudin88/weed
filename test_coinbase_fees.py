from consensus import get_block_reward


def maximum_coinbase_reward(
    block_height,
    total_fees
):

    subsidy = get_block_reward(
        block_height
    )

    return subsidy + total_fees


print()
print("================================")
print("   WEED COINBASE + FEES TEST")
print("================================")

subsidy = get_block_reward(1)
fees = 5

maximum = maximum_coinbase_reward(
    1,
    fees
)

print()
print("Block subsidy:")
print(subsidy, "WEED")

print()
print("Transaction fees:")
print(fees, "WEED")

print()
print("Maximum coinbase:")
print(maximum, "WEED")


if maximum != 55:
    raise SystemExit(
        "TEST FAILED: incorrect maximum reward"
    )


print()
print("================================")
print("         TEST PASSED")
print("================================")
