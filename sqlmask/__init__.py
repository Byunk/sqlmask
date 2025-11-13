from sqlmask import core


def mask(sql: str) -> str:
    masker = core.SQLMask()
    return masker.mask(sql)
