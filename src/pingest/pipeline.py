def read_records(source):
    """Yield one record at a time. Source is consumed exactly once"""
    for rec in source:
        yield rec
