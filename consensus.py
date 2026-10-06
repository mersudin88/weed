BLOCK_REWARD = 50
HALVING_INTERVAL = 210000

INITIAL_DIFFICULTY = 4

TARGET_BLOCK_TIME = 60
DIFFICULTY_ADJUSTMENT_INTERVAL = 10

COINBASE_MATURITY = 100
COINBASE_MATURITY_HEIGHT = 15
MERKLE_ACTIVATION_HEIGHT = 15

def get_block_reward(block_height):

    halvings = block_height // HALVING_INTERVAL

    if halvings >= 64:
        return 0

    return BLOCK_REWARD // (2 ** halvings)


def get_block_value(block, key):

    if isinstance(block, dict):
        return block[key]

    return getattr(block, key)


def get_difficulty(block_height, chain=None):

    if chain is None:
        return INITIAL_DIFFICULTY

    if block_height < DIFFICULTY_ADJUSTMENT_INTERVAL:
        return INITIAL_DIFFICULTY

    if block_height % DIFFICULTY_ADJUSTMENT_INTERVAL != 0:
        return get_difficulty(
            block_height - 1,
            chain
        )

    previous_block = chain[
        block_height - 1
    ]

    adjustment_start = max(
        0,
        block_height - DIFFICULTY_ADJUSTMENT_INTERVAL
    )

    first_block = chain[
        adjustment_start
    ]

    previous_timestamp = get_block_value(
        previous_block,
        "timestamp"
    )

    first_timestamp = get_block_value(
        first_block,
        "timestamp"
    )

    actual_time = (
        previous_timestamp
        - first_timestamp
    )

    target_time = (
        TARGET_BLOCK_TIME
        * DIFFICULTY_ADJUSTMENT_INTERVAL
    )

    previous_difficulty = get_difficulty(
        block_height - 1,
        chain
    )

    if actual_time < target_time:
        return previous_difficulty + 1

    if actual_time > target_time:
        return max(
            1,
            previous_difficulty - 1
        )

    return previous_difficulty
