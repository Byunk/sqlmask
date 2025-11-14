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
    BOOLEAN_KEYWORDS = ("TRUE", "FALSE")
    NO_MASK_KEYWORDS = ("LIMIT", "OFFSET", "TOP")

    def __init__(
        self,
        format: bool = False,
        remove_limit: bool = False,
    ):
        self.format = format
        self.remove_limit = remove_limit

    def mask(self, sql: str) -> str:
        if self.format:
            sql = sqlparse.format(
                sql,
                keyword_case="upper",
                identifier_case="lower",
                reindent=True,
                use_space_around_operators=True,
                strip_comments=True,
            )

        parsed = sqlparse.parse(sql)
        return self._mask_tokens(parsed[0].tokens)

    def _mask_tokens(self, tokens: list[ss.Token]) -> str:
        result = []
        prev_token = None
        skip_until_number = False

        for token in tokens:
            # Check if this is a LIMIT/OFFSET/TOP keyword that should be removed
            if self.remove_limit and self._is_remove_limit_keyword(token):
                # Remove trailing whitespace from result
                while result and result[-1].strip() == "":
                    result.pop()
                # Also trim trailing whitespace from the last string if it has content
                if result and result[-1]:
                    result[-1] = result[-1].rstrip()
                skip_until_number = True
                if not token.is_whitespace:
                    prev_token = token
                continue

            # When in skip mode, skip whitespace and the number
            if skip_until_number:
                if token.is_whitespace:
                    continue
                elif self._is_number_literal_type(token):
                    skip_until_number = False
                    if not token.is_whitespace:
                        prev_token = token
                    continue
                else:
                    # Hit something unexpected, stop skipping
                    skip_until_number = False

            if self._is_recursive_token_type(token):
                result.append(self._process_recursive_token(token))
            elif isinstance(token, ss.Parenthesis):
                result.append(self._process_parenthesis(token, prev_token))
            elif self._is_literal_type(token):
                result.append(self._process_literal(token, prev_token))
            else:
                result.append(str(token))

            # Update prev_token (skip whitespace)
            if not token.is_whitespace:
                prev_token = token

        return "".join(result)

    def _is_literal_type(self, token: ss.Token) -> bool:
        return (
            self._is_string_literal_type(token)
            or self._is_number_literal_type(token)
            or self._is_boolean_keyword(token)
        )

    def _is_string_literal_type(self, token: ss.Token) -> bool:
        return token.ttype in self.STRING_LITERAL_TYPES

    def _is_number_literal_type(self, token: ss.Token) -> bool:
        return token.ttype in self.NUMBER_LITERAL_TYPES

    def _is_boolean_keyword(self, token: ss.Token) -> bool:
        return token.ttype == st.Keyword and token.value.upper() in self.BOOLEAN_KEYWORDS

    def _is_remove_limit_keyword(self, token: ss.Token) -> bool:
        # Check for keyword tokens (LIMIT, OFFSET)
        if token.ttype == st.Keyword and token.value.upper() in self.NO_MASK_KEYWORDS:
            return True
        # Check for Identifier groups containing TOP/LIMIT/OFFSET as Name
        if isinstance(token, ss.Identifier):
            # Check the first non-whitespace token in the identifier
            for subtoken in token.tokens:
                if not subtoken.is_whitespace:
                    if subtoken.ttype == st.Name and subtoken.value.upper() in self.NO_MASK_KEYWORDS:
                        return True
                    break
        return False

    def _is_recursive_token_type(self, token: ss.Token) -> bool:
        return isinstance(token, self.RECURSIVE_TOKEN_TYPES)

    def _follows_no_mask_keyword(self, prev_token: ss.Token | None) -> bool:
        return (
            prev_token is not None
            and prev_token.ttype == st.Keyword
            and prev_token.value.upper() in self.NO_MASK_KEYWORDS
        )

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
        should_mask = self._is_literal_type(token) and not self._follows_no_mask_keyword(prev_token)
        return "?" if should_mask else str(token)

    def _is_literal_list(self, tokens: list[ss.Token]) -> bool:
        has_literal = False
        for token in tokens:
            if token.is_whitespace or token.ttype == st.Punctuation:
                continue
            if isinstance(token, ss.IdentifierList):
                return self._is_literal_list(token.tokens)
            if self._is_literal_type(token):
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
            if self._is_literal_type(token):
                return True
        return False
