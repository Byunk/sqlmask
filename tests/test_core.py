from textwrap import dedent
from sqlmask import mask
from sqlmask.core import SQLMask
import pytest


class TestSQLMask:
    def test_numeric_literals(self):
        sql = "SELECT id, name FROM customers WHERE age > 30"
        expected = "SELECT id, name FROM customers WHERE age > ?"
        assert mask(sql) == expected

    def test_string_literals(self):
        sql = "SELECT * FROM products WHERE price < 20 AND category = 'books'"
        expected = "SELECT * FROM products WHERE price < ? AND category = ?"
        assert mask(sql) == expected

    def test_boolean_literals(self):
        sql = "SELECT * FROM users WHERE is_active = true AND is_admin = false"
        expected = "SELECT * FROM users WHERE is_active = ? AND is_admin = ?"
        assert mask(sql) == expected

    def test_in_clause(self):
        sql = "SELECT * FROM orders WHERE status IN ('pending', 'shipped', 'delivered')"
        expected = "SELECT * FROM orders WHERE status IN (?)"
        assert mask(sql) == expected

    def test_column_alias(self):
        sql = "SELECT id AS user_id, name AS user_name FROM users WHERE age > 25"
        expected = "SELECT id AS user_id, name AS user_name FROM users WHERE age > ?"
        assert mask(sql) == expected

    def test_table_alias(self):
        sql = "SELECT u.id, u.name FROM users AS u WHERE u.status = 'active'"
        expected = "SELECT u.id, u.name FROM users AS u WHERE u.status = ?"
        assert mask(sql) == expected

    def test_simple_subquery(self):
        sql = "SELECT * FROM users WHERE id IN (SELECT user_id FROM orders WHERE total > 100)"
        expected = "SELECT * FROM users WHERE id IN (SELECT user_id FROM orders WHERE total > ?)"
        assert mask(sql) == expected

    def test_multiple_subqueries(self):
        sql = """
            SELECT * FROM users
            WHERE id IN (SELECT user_id FROM orders WHERE total > 100)
            AND region_id IN (SELECT id FROM regions WHERE name = 'US')
        """
        expected = """
            SELECT * FROM users
            WHERE id IN (SELECT user_id FROM orders WHERE total > ?)
            AND region_id IN (SELECT id FROM regions WHERE name = ?)
        """
        assert mask(sql.strip()) == expected.strip()

    def test_nested_subquery(self):
        sql = """
            SELECT * FROM users
            WHERE id IN (
                SELECT user_id FROM orders
                WHERE product_id IN (
                    SELECT id FROM products WHERE price > 50
                )
            )
        """
        expected = """
            SELECT * FROM users
            WHERE id IN (
                SELECT user_id FROM orders
                WHERE product_id IN (
                    SELECT id FROM products WHERE price > ?
                )
            )
        """
        assert mask(sql.strip()) == expected.strip()

    def test_with_clause(self):
        sql = """
            WITH high_value_orders AS (
                SELECT user_id, total FROM orders WHERE total > 1000
            )
            SELECT * FROM high_value_orders WHERE user_id = 5
        """
        expected = """
            WITH high_value_orders AS (
                SELECT user_id, total FROM orders WHERE total > ?
            )
            SELECT * FROM high_value_orders WHERE user_id = ?
        """
        assert mask(sql.strip()) == expected.strip()

    def test_multiple_cte(self):
        sql = """
            WITH
            active_users AS (SELECT id FROM users WHERE status = 'active'),
            recent_orders AS (SELECT user_id FROM orders WHERE created_at > '2024-01-01')
            SELECT * FROM active_users WHERE id IN (SELECT user_id FROM recent_orders)
        """
        expected = """
            WITH
            active_users AS (SELECT id FROM users WHERE status = ?),
            recent_orders AS (SELECT user_id FROM orders WHERE created_at > ?)
            SELECT * FROM active_users WHERE id IN (SELECT user_id FROM recent_orders)
        """
        assert mask(sql.strip()) == expected.strip()

    def test_insert_values(self):
        sql = "INSERT INTO users (name, age, email) VALUES ('John', 30, 'john@example.com')"
        expected = "INSERT INTO users (name, age, email) VALUES (?, ?, ?)"
        assert mask(sql) == expected

    def test_insert_multiple_rows(self):
        sql = """
            INSERT INTO products (name, price, category)
            VALUES ('Book', 15.99, 'education'), ('Pen', 2.50, 'stationery')
        """
        expected = """
            INSERT INTO products (name, price, category)
            VALUES (?, ?, ?), (?, ?, ?)
        """
        assert mask(sql.strip()) == expected.strip()

    def test_union(self):
        sql = """
            SELECT id, name FROM customers WHERE age > 50
            UNION
            SELECT id, name FROM customers WHERE country = 'USA'
        """
        expected = """
            SELECT id, name FROM customers WHERE age > ?
            UNION
            SELECT id, name FROM customers WHERE country = ?
        """
        assert mask(sql.strip()) == expected.strip()

    def test_union_all(self):
        sql = """
            SELECT product_id FROM orders WHERE status = 'pending'
            UNION ALL
            SELECT product_id FROM orders WHERE status = 'shipped'
        """
        expected = """
            SELECT product_id FROM orders WHERE status = ?
            UNION ALL
            SELECT product_id FROM orders WHERE status = ?
        """
        assert mask(sql.strip()) == expected.strip()

    def test_having_clause(self):
        sql = "SELECT category, COUNT(*) FROM products GROUP BY category HAVING COUNT(*) > 10"
        expected = "SELECT category, COUNT(*) FROM products GROUP BY category HAVING COUNT(*) > ?"
        assert mask(sql) == expected

    def test_having_with_literals(self):
        sql = """
            SELECT user_id, SUM(total) as sum_total
            FROM orders
            WHERE status = 'completed'
            GROUP BY user_id
            HAVING SUM(total) > 1000
        """
        expected = """
            SELECT user_id, SUM(total) as sum_total
            FROM orders
            WHERE status = ?
            GROUP BY user_id
            HAVING SUM(total) > ?
        """
        assert mask(sql.strip()) == expected.strip()

    def test_case_expression(self):
        """Should not mask literals inside CASE expressions."""
        sql = """
            SELECT
                name,
                CASE
                    WHEN age < 18 THEN 'minor'
                    WHEN age >= 18 AND age < 65 THEN 'adult'
                    ELSE 'senior'
                END as age_group
            FROM users
        """
        expected = """
            SELECT
                name,
                CASE
                    WHEN age < 18 THEN 'minor'
                    WHEN age >= 18 AND age < 65 THEN 'adult'
                    ELSE 'senior'
                END as age_group
            FROM users
        """
        assert mask(sql.strip()) == expected.strip()

    def test_case_in_where(self):
        """Should not mask literals inside CASE expressions."""
        sql = """
            SELECT * FROM products
            WHERE CASE
                WHEN category = 'books' THEN price > 10
                WHEN category = 'electronics' THEN price > 100
                ELSE price > 50
            END
        """
        expected = """
            SELECT * FROM products
            WHERE CASE
                WHEN category = 'books' THEN price > 10
                WHEN category = 'electronics' THEN price > 100
                ELSE price > 50
            END
        """
        assert mask(sql.strip()) == expected.strip()

    def test_inner_join(self):
        sql = """
            SELECT u.name, o.total
            FROM users u
            INNER JOIN orders o ON u.id = o.user_id
            WHERE o.total > 100
        """
        expected = """
            SELECT u.name, o.total
            FROM users u
            INNER JOIN orders o ON u.id = o.user_id
            WHERE o.total > ?
        """
        assert mask(sql.strip()) == expected.strip()

    def test_left_join(self):
        sql = """
            SELECT u.name, o.total
            FROM users u
            LEFT JOIN orders o ON u.id = o.user_id
            WHERE u.status = 'active'
        """
        expected = """
            SELECT u.name, o.total
            FROM users u
            LEFT JOIN orders o ON u.id = o.user_id
            WHERE u.status = ?
        """
        assert mask(sql.strip()) == expected.strip()

    def test_multiple_joins(self):
        sql = """
            SELECT u.name, o.total, p.name as product_name
            FROM users u
            INNER JOIN orders o ON u.id = o.user_id
            INNER JOIN products p ON o.product_id = p.id
            WHERE u.country = 'USA' AND p.price > 50
        """
        expected = """
            SELECT u.name, o.total, p.name as product_name
            FROM users u
            INNER JOIN orders o ON u.id = o.user_id
            INNER JOIN products p ON o.product_id = p.id
            WHERE u.country = ? AND p.price > ?
        """
        assert mask(sql.strip()) == expected.strip()

    def test_window_function(self):
        sql = """
            SELECT
                name,
                salary,
                ROW_NUMBER() OVER (ORDER BY salary DESC) as rank
            FROM employees
            WHERE department = 'engineering'
        """
        expected = """
            SELECT
                name,
                salary,
                ROW_NUMBER() OVER (ORDER BY salary DESC) as rank
            FROM employees
            WHERE department = ?
        """
        assert mask(sql.strip()) == expected.strip()

    def test_window_partition(self):
        sql = """
            SELECT
                name,
                department,
                salary,
                AVG(salary) OVER (PARTITION BY department) as dept_avg_salary
            FROM employees
            WHERE salary > 50000
        """
        expected = """
            SELECT
                name,
                department,
                salary,
                AVG(salary) OVER (PARTITION BY department) as dept_avg_salary
            FROM employees
            WHERE salary > ?
        """
        assert mask(sql.strip()) == expected.strip()

    def test_update_statement(self):
        sql = "UPDATE users SET status = 'inactive', updated_at = '2024-01-01' WHERE age > 65"
        expected = "UPDATE users SET status = ?, updated_at = ? WHERE age > ?"
        assert mask(sql) == expected

    def test_update_with_subquery(self):
        sql = """
            UPDATE products
            SET price = 99.99
            WHERE id IN (SELECT product_id FROM discontinued WHERE date < '2024-01-01')
        """
        expected = """
            UPDATE products
            SET price = ?
            WHERE id IN (SELECT product_id FROM discontinued WHERE date < ?)
        """
        assert mask(sql.strip()) == expected.strip()

    def test_like_pattern(self):
        sql = "SELECT * FROM users WHERE name LIKE '%John%' AND email LIKE 'admin@%'"
        expected = "SELECT * FROM users WHERE name LIKE ? AND email LIKE ?"
        assert mask(sql) == expected

    def test_between(self):
        sql = "SELECT * FROM products WHERE price BETWEEN 10 AND 100"
        expected = "SELECT * FROM products WHERE price BETWEEN ? AND ?"
        assert mask(sql) == expected

    def test_null_comparison(self):
        sql = "SELECT * FROM users WHERE email IS NULL AND phone IS NOT NULL"
        expected = "SELECT * FROM users WHERE email IS NULL AND phone IS NOT NULL"
        assert mask(sql) == expected

    def test_arithmetic_expression(self):
        sql = "SELECT * FROM products WHERE price * 1.1 > 50 AND quantity - 5 < 100"
        expected = "SELECT * FROM products WHERE price * ? > ? AND quantity - ? < ?"
        assert mask(sql) == expected

    def test_delete_statement(self):
        sql = "DELETE FROM users WHERE status = 'inactive' AND last_login < '2023-01-01'"
        expected = "DELETE FROM users WHERE status = ? AND last_login < ?"
        assert mask(sql) == expected

    def test_order_by_with_limit(self):
        """Should not mask literals inside LIMIT clauses."""
        sql = "SELECT * FROM products WHERE category = 'books' ORDER BY price DESC LIMIT 10"
        expected = "SELECT * FROM products WHERE category = ? ORDER BY price DESC LIMIT 10"
        assert mask(sql) == expected

    def test_distinct(self):
        sql = "SELECT DISTINCT category FROM products WHERE price > 25"
        expected = "SELECT DISTINCT category FROM products WHERE price > ?"
        assert mask(sql) == expected

    def test_date_literals(self):
        sql = "SELECT * FROM orders WHERE created_at >= '2024-01-01' AND created_at < '2024-12-31'"
        expected = "SELECT * FROM orders WHERE created_at >= ? AND created_at < ?"
        assert mask(sql) == expected

    def test_negative_numbers(self):
        sql = "SELECT * FROM transactions WHERE amount < -100 OR balance = -50.5"
        expected = "SELECT * FROM transactions WHERE amount < ? OR balance = ?"
        assert mask(sql) == expected

    def test_multiple_in_clauses(self):
        sql = """
            SELECT * FROM products
            WHERE category IN ('books', 'electronics', 'toys')
            AND status IN ('active', 'featured')
        """
        expected = """
            SELECT * FROM products
            WHERE category IN (?)
            AND status IN (?)
        """
        assert mask(sql.strip()) == expected.strip()


class TestRemoveLimit:
    @pytest.mark.parametrize(
        "sql,expected",
        [
            # LIMIT
            (
                "SELECT * FROM products WHERE category = 'books' ORDER BY price DESC LIMIT 10",
                "SELECT * FROM products WHERE category = ? ORDER BY price DESC",
            ),
            # OFFSET
            (
                "SELECT * FROM users WHERE age > 25 OFFSET 5",
                "SELECT * FROM users WHERE age > ?",
            ),
            # TOP (SQL Server)
            (
                "SELECT TOP 10 * FROM orders WHERE status = 'pending'",
                "SELECT * FROM orders WHERE status = ?",
            ),
        ],
    )
    def test_remove_limit_single_clause(self, sql: str, expected: str):
        assert mask(sql, remove_limit=True) == expected

    @pytest.mark.parametrize(
        "sql,expected",
        [
            (
                "SELECT * FROM users WHERE age > 25 LIMIT 10 OFFSET 5",
                "SELECT * FROM users WHERE age > ?",
            ),
            (
                "SELECT * FROM products ORDER BY price DESC LIMIT 20 OFFSET 10",
                "SELECT * FROM products ORDER BY price DESC",
            ),
        ],
    )
    def test_remove_limit_combined(self, sql: str, expected: str):
        assert mask(sql, remove_limit=True) == expected

    @pytest.mark.parametrize(
        "sql,expected",
        [
            # Subquery
            (
                "SELECT * FROM users WHERE id IN (SELECT user_id FROM orders WHERE total > 100 LIMIT 5)",
                "SELECT * FROM users WHERE id IN (SELECT user_id FROM orders WHERE total > ?)",
            ),
            # CTE
            (
                """WITH top_orders AS (
                SELECT user_id, total FROM orders WHERE total > 1000 LIMIT 10
            )
            SELECT * FROM top_orders WHERE user_id = 5""",
                """WITH top_orders AS (
                SELECT user_id, total FROM orders WHERE total > ?
            )
            SELECT * FROM top_orders WHERE user_id = ?""",
            ),
            # Nested subquery
            (
                """SELECT * FROM users
            WHERE id IN (
                SELECT user_id FROM orders
                WHERE product_id IN (
                    SELECT id FROM products WHERE price > 50 LIMIT 3
                ) LIMIT 10
            )""",
                """SELECT * FROM users
            WHERE id IN (
                SELECT user_id FROM orders
                WHERE product_id IN (
                    SELECT id FROM products WHERE price > ?
                )
            )""",
            ),
        ],
    )
    def test_remove_limit_nested(self, sql: str, expected: str):
        assert mask(sql.strip(), remove_limit=True) == expected.strip()

    def test_remove_limit_with_other_clauses(self):
        sql = """
            SELECT category, COUNT(*) as count
            FROM products
            WHERE price > 10 AND status = 'active'
            GROUP BY category
            HAVING COUNT(*) > 5
            ORDER BY count DESC
            LIMIT 20
        """
        expected = """
            SELECT category, COUNT(*) as count
            FROM products
            WHERE price > ? AND status = ?
            GROUP BY category
            HAVING COUNT(*) > ?
            ORDER BY count DESC
        """
        assert mask(sql.strip(), remove_limit=True) == expected.strip()


class TestSQLMaskFormatting:
    def test_format(self):
        masker = SQLMask(format=True)
        sql = "select * from users where age > 30 and status = 'active'"
        expected = "SELECT *\nFROM users\nWHERE age > ?\n  AND status = ?"
        result = masker.mask(sql)
        assert result == expected

    @pytest.mark.parametrize(
        "sql",
        [
            "select * from users where age > 25",
            "SELECT * FROM users WHERE age > 25",
            "SeLeCt * FrOm users WhErE age > 25",
            """select *
            from users
            where age > 25""",
        ],
    )
    def test_format_consistency(self, sql: str):
        masker = SQLMask(format=True)
        expected = "SELECT *\nFROM users\nWHERE age > ?"
        result = masker.mask(sql)
        assert result == expected

    def test_format_with_cte(self):
        masker = SQLMask(format=True)
        sql = """
            WITH active_users AS (
                SELECT id FROM users WHERE status = 'active'
            )
            SELECT * FROM active_users WHERE id > 10
        """
        expected = "WITH active_users AS\n  (SELECT id\n   FROM users\n   WHERE status = ?)\nSELECT *\nFROM active_users\nWHERE id > ?"
        result = masker.mask(sql)
        assert result == expected
