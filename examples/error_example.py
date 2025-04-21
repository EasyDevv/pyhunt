from pyhunt import trace, logger


@trace
def level_three(value: int):
    logger.info("Inside level_three, about to raise TypeError.")

    # This will raise a TypeError, string + int
    try:
        result = "number: " + value
        return result
    except TypeError as e:
        raise TypeError(e)


@trace
def level_two(value):
    logger.info("Inside level_two, calling level_three.")
    level_three(value - 1)


@trace
def level_one(value):
    logger.info("Inside level_one, calling level_two.")
    level_two(value - 1)


if __name__ == "__main__":
    int_value = 5
    level_one(int_value)
