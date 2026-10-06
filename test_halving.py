from consensus import get_block_reward


tests = [
    (0, 50),
    (1, 50),
    (209999, 50),
    (210000, 25),
    (210001, 25),
    (419999, 25),
    (420000, 12),
    (630000, 6),
    (840000, 3),
    (1050000, 1),
    (1260000, 0),
]


for height, expected in tests:

    actual = get_block_reward(height)

    status = "PASS" if actual == expected else "FAIL"

    print(
        f"Block {height}: "
        f"reward={actual} "
        f"expected={expected} "
        f"[{status}]"
    )

    if actual != expected:
        raise SystemExit(1)


print()
print("Halving test passed.")
