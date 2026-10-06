from consensus import (
    BLOCK_REWARD,
    HALVING_INTERVAL,
    get_block_reward
)


total_supply = 0
height = 0

while True:

    reward = get_block_reward(height)

    if reward == 0:
        break

    total_supply += reward

    height += 1


print("================================")
print("       WEED SUPPLY TEST")
print("================================")

print()
print("Initial reward:")
print(BLOCK_REWARD, "WEED")

print()
print("Halving interval:")
print(HALVING_INTERVAL, "blocks")

print()
print("Last reward block:")
print(height - 1)

print()
print("First zero-reward block:")
print(height)

print()
print("Maximum block subsidy:")
print(total_supply, "WEED")
