from consensus import get_difficulty


def make_chain(block_time):

    chain = []

    for height in range(31):

        chain.append({
            "index": height,
            "timestamp": height * block_time
        })

    return chain


def test(name, block_time):

    chain = make_chain(block_time)

    difficulty_before = get_difficulty(
        19,
        chain
    )

    difficulty_after = get_difficulty(
        20,
        chain
    )

    print()
    print(name)
    print("Block time:", block_time)
    print("Difficulty at 19:", difficulty_before)
    print("Difficulty at 20:", difficulty_after)


print()
print("================================")
print("      WEED DIFFICULTY TEST")
print("================================")

test("FAST", 10)

test("NORMAL", 60)

test("SLOW", 120)
