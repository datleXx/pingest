import itertools


def read_records(source):
    """Yield one record at a time. Source is consumed exactly once"""
    for rec in source:
        yield rec


def batched(iterable, n):
    """Yield a list of n at once"""
    if n <= 0:
        raise ValueError("n must be >= 0")
    source = iter(iterable)
    while True:
        chunk = list(itertools.islice(source, n))
        if chunk:
            yield chunk
        else:
            break
