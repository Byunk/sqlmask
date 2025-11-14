from sqlmask.core import SQLMask


def mask(
    sql: str,
) -> str:
    """Masks sensitive literal values in SQL queries.

    Args:
        sql: The SQL query to mask.

    Returns:
        The masked SQL query.

    Examples:
        >>> import sqlmask
        >>> sqlmask.mask("SELECT * FROM users WHERE id = 1")
        'SELECT * FROM users WHERE id = ?'
    """
    masker = SQLMask()
    return masker.mask(sql)
