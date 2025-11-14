import sqlparse
import sqlparse.sql as ss
import sqlparse.tokens as st
from sqlparse.sql import Operation, Values


class SQLMask:
    RECURSIVE_TOKEN_TYPES = (
        ss.Statement,
        ss.Where,
        ss.Comparison,
        ss.Identifier,
        ss.Function,
        ss.IdentifierList,
        Values,
        Operation,
    )
    STRING_LITERAL_TYPES = (st.Literal.String.Single, st.Literal.String.Symbol)
    NUMBER_LITERAL_TYPES = (st.Literal.Number.Integer, st.Literal.Number.Float)
    NO_MASK_KEYWORDS = ("LIMIT", "OFFSET", "TOP")

    def mask(self, sql: str) -> str:
        parsed = sqlparse.parse(sql)
        return self._mask_tokens(parsed[0].tokens)

    def _mask_tokens(self, tokens: list[ss.Token]) -> str:
        result = []
        prev_token = None

        for token in tokens:
            if self._is_recursive_token_type(token):
                result.append(self._process_recursive_token(token))
            elif isinstance(token, ss.Parenthesis):
                result.append(self._process_parenthesis(token, prev_token))
            elif self._is_string_literal(token) or self._is_number_literal(token):
                result.append(self._process_literal(token, prev_token))
            else:
                result.append(str(token))

            # Update prev_token (skip whitespace)
            if not token.is_whitespace:
                prev_token = token

        return "".join(result)

    def _is_string_literal(self, token: ss.Token) -> bool:
        return token.ttype in self.STRING_LITERAL_TYPES

    def _is_number_literal(self, token: ss.Token) -> bool:
        return token.ttype in self.NUMBER_LITERAL_TYPES

    def _is_recursive_token_type(self, token: ss.Token) -> bool:
        return isinstance(token, self.RECURSIVE_TOKEN_TYPES)

    def _follows_no_mask_keyword(self, prev_token: ss.Token | None) -> bool:
        return (
            prev_token is not None
            and prev_token.ttype == st.Keyword
            and prev_token.value.upper() in self.NO_MASK_KEYWORDS
        )

    def _should_mask_string_literal(self, prev_token: ss.Token | None) -> bool:
        return not self._follows_no_mask_keyword(prev_token)

    def _should_mask_number_literal(self, prev_token: ss.Token | None) -> bool:
        return not self._follows_no_mask_keyword(prev_token)

    def _process_recursive_token(self, token: ss.Token) -> str:
        return self._mask_tokens(token.tokens)

    def _process_parenthesis(self, token: ss.Token, prev_token: ss.Token | None) -> str:
        inner_tokens = token.tokens[1:-1]
        should_collapse = (
            self._is_literal_list(inner_tokens)
            and self._should_collapse_literal_list(inner_tokens)
            and prev_token is not None
            and prev_token.ttype == st.Keyword
            and prev_token.value.upper() == "IN"
        )
        if should_collapse:
            return "(?)"
        return self._mask_tokens(token.tokens)

    def _process_literal(self, token: ss.Token, prev_token: ss.Token | None) -> str:
        if self._is_string_literal(token):
            return "?" if self._should_mask_string_literal(prev_token) else str(token)
        elif self._is_number_literal(token):
            return "?" if self._should_mask_number_literal(prev_token) else str(token)
        return str(token)

    def _is_literal_list(self, tokens: list[ss.Token]) -> bool:
        has_literal = False
        for token in tokens:
            if token.is_whitespace or token.ttype == st.Punctuation:
                continue
            if isinstance(token, ss.IdentifierList):
                return self._is_literal_list(token.tokens)
            if self._is_string_literal(token) or self._is_number_literal(token):
                has_literal = True
            else:
                return False
        return has_literal

    def _should_collapse_literal_list(self, tokens: list[ss.Token]) -> bool:
        for token in tokens:
            if token.is_whitespace or token.ttype == st.Punctuation:
                continue
            if isinstance(token, ss.IdentifierList):
                return self._should_collapse_literal_list(token.tokens)
            if self._is_string_literal(token) or self._is_number_literal(token):
                return True
        return False
