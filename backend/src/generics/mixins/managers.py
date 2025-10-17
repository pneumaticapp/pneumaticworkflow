import re
from typing import Optional, Tuple


class NormalizeEmailMixin:
    @classmethod
    def normalize_email(cls, email: Optional[str]) -> str:
        return (email or '').lower()


class SearchSqlQueryMixin:

    def _search_in(self, table: str, tsquery: str) -> str:
        return f"{table}.search_content @@ {tsquery} = TRUE"

    def _escape_tsquery_text(self, text: str) -> str:
        """ Escapes special characters for PostgreSQL tsquery.
            Replaces characters with their escaped versions
            Uses r'\\\1' in re.sub, where '\\' produces one backslash,
            and '\1' refers to the captured character.
        """
        return re.sub(r'([&|!():\\])', r'\\\1', text)

    def _get_tsquery(self) -> Tuple[str, dict]:

        """ Return SQL tsquery syntax search string and safe search words list

            1. Search by prefix. Example:
               Search text "Ja" will find:
                - James
                - JaMartir
                - Ja
            2. Split search text by words and search for all words
               Search text "Ja Mar" will find:
                - James Martir
                - JaMartir
                - Marty.J.
            3. Escape single quotes and tsquery special characters

            TODO The shit and confusing logic is due to the fact that partial
              search and URL search conflict and it is necessary to wrap the
              word in single quotes
        """

        words = self.search_text.replace("'", "''").split(' ')
        escaped_words = [self._escape_tsquery_text(word) for word in words]

        result = (" || ' | ' || ".join(
            [f"''%(search_{i})s'' || ':*'" for i in range(len(escaped_words))],
        ))
        params = {
            f'search_{i}': value for i, value in enumerate(escaped_words)
        }
        return f'to_tsquery({result})', params
