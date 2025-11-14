# python-sqlmask - Anonymize SQL statements

sqlmask replaces values in SQL statements with placeholders.

**Use cases**

- Logging SQL queries without sensitive data
- Analyzing SQL query patterns
- Sanitizing LLM inputs

## Quick Start

```bash
pip install sqlmask
```

```python
from sqlmask import mask

sql = "SELECT * FROM users WHERE age > 25 AND status = 'active'"
result = mask(sql)
print(result) # SELECT * FROM users WHERE age > ? AND status = ?

sql = "SELECT * FROM orders AS o WHERE o.status in ('shipped', 'delivered')"
result = mask(sql)
print(result) # SELECT * FROM orders AS o WHERE o.status in (?)

sql = "INSERT INTO products (name, price) VALUES ('Gadget', 99.99)"
result = mask(sql)
print(result) # INSERT INTO products (name, price) VALUES (?, ?)
```

## Options

- `format`: Consolidate the format of the SQL query.
- `remove_limit`: Remove LIMIT, OFFSET, and TOP clauses from SQL queries.
