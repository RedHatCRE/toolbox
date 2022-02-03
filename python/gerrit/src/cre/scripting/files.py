import random


def touch(file: str, size: int = 40) -> None:
    with open(file, 'wb') as buffer:
        buffer.write(random.randbytes(size))
