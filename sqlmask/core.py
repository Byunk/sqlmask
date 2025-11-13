import sqlparse
import sqlparse.sql as ss
import sqlparse.tokens as st
from sqlparse.sql import Operation, Values


class SQLMask:
    def mask(self, sql: str) -> str:
        parsed = sqlparse.parse(sql)
        return self._mask_tokens(parsed[0].tokens)

    def _mask_tokens(self, tokens: list[ss.Token]):
        result = []
        prev_token = None

        for token in tokens:
            if isinstance(
                token,
                (
                    ss.Statement,
                    ss.Where,
                    ss.Comparison,
                    ss.Identifier,
                    ss.Function,
                    ss.IdentifierList,
                    Values,
                    Operation,
                ),
            ):
                result.append(self._mask_tokens(token.tokens))
            elif isinstance(token, ss.Parenthesis):
                # Collapse if preceded by IN keyword, otherwise mask each literal individually
                if (
                    self._is_literal_list(token.tokens[1:-1])
                    and prev_token
                    and prev_token.ttype == st.Keyword
                    and prev_token.value.upper() == "IN"
                ):
                    result.append("(?)")
                else:
                    result.append(self._mask_tokens(token.tokens))
            elif token.ttype in (
                st.Literal.String.Single,
                st.Literal.String.Symbol,
                st.Literal.Number.Integer,
                st.Literal.Number.Float,
            ):
                # Don't mask literals that follow LIMIT/OFFSET/TOP keywords
                if (
                    prev_token
                    and prev_token.ttype == st.Keyword
                    and prev_token.value.upper() in ("LIMIT", "OFFSET", "TOP")
                ):
                    result.append(str(token))
                else:
                    result.append("?")
            else:
                result.append(str(token))

            # Update prev_token (skip whitespace)
            if not token.is_whitespace:
                prev_token = token

        return "".join(result)

    def _is_literal_list(self, tokens: list[ss.Token]) -> bool:
        has_literal = False
        for token in tokens:
            # Skip whitespace and commas
            if token.is_whitespace or token.ttype == st.Punctuation:
                continue
            # Recursively check identifier lists
            if isinstance(token, ss.IdentifierList):
                return self._is_literal_list(token.tokens)
            # Check if it's a literal
            if token.ttype in (
                st.Literal.String.Single,
                st.Literal.String.Symbol,
                st.Literal.Number.Integer,
                st.Literal.Number.Float,
            ):
                has_literal = True
            else:
                # Found a non-literal, non-punctuation token
                return False
        return has_literal
