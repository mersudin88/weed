from consensus import (
    get_block_reward,
    get_difficulty,
    BLOCK_REWARD,
    HALVING_INTERVAL
)


def test_initial_block_reward():

    assert get_block_reward(0) == BLOCK_REWARD


def test_first_halving():

    assert get_block_reward(
        HALVING_INTERVAL
    ) == BLOCK_REWARD // 2


def test_second_halving():

    assert get_block_reward(
        HALVING_INTERVAL * 2
    ) == BLOCK_REWARD // 4


def test_reward_never_becomes_negative():

    assert get_block_reward(
        HALVING_INTERVAL * 100
    ) == 0


def test_initial_difficulty():

    difficulty = get_difficulty(
        0,
        []
    )

    assert difficulty == 4