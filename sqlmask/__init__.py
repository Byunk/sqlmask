from sqlmask.core import SQLMask


def mask(
    sql: str,
    format: bool = False,
) -> str:
    """Masks sensitive literal values in SQL queries.

    Args:
        sql: The SQL query to mask.
        format: Whether to format the SQL query.
    Returns:
        The masked SQL query.

    Examples:
        >>> import sqlmask
        >>> sqlmask.mask("SELECT * FROM users WHERE id = 1")
        'SELECT * FROM users WHERE id = ?'
    """
    masker = SQLMask(format=format)
    return masker.mask(sql)
