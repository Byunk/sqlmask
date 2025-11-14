from sqlmask.core import SQLMask


def mask(
    sql: str,
    format: bool = False,
    remove_limit: bool = False,
) -> str:
    """Masks sensitive literal values in SQL queries.

    Args:
        sql: The SQL query to mask.
        format: Whether to format the SQL query.
        remove_limit: Whether to remove LIMIT, OFFSET, and TOP clauses.
    Returns:
        The masked SQL query.

    Examples:
        >>> import sqlmask
        >>> sqlmask.mask("SELECT * FROM users WHERE id = 1")
        'SELECT * FROM users WHERE id = ?'
        >>> sqlmask.mask("SELECT * FROM users LIMIT 10", remove_limit=True)
        'SELECT * FROM users'
    """
    masker = SQLMask(format=format, remove_limit=remove_limit)
    return masker.mask(sql)
