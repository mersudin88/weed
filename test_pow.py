from consensus import get_difficulty


def check_pow(block, difficulty):

    target = "0" * difficulty

    return block["hash"].startswith(target)


print()
print("================================")
print("          WEED POW TEST")
print("================================")

valid_block = {
    "hash": "0000abcdef123456"
}

invalid_block = {
    "hash": "0001abcdef123456"
}

difficulty = 4

print()
print("Difficulty:", difficulty)

print()
print("Valid block:")
print(check_pow(valid_block, difficulty))

print()
print("Invalid block:")
print(check_pow(invalid_block, difficulty))
