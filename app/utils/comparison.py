def compare(a: dict | None, b: dict | None) -> bool:
    if a is None or b is None:
        return False
    return a == b
