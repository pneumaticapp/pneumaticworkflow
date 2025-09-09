from typing import Optional, Tuple


class NormalizeEmailMixin:
    @classmethod
    def normalize_email(cls, email: Optional[str]) -> str:
        return (email or '').lower()


class SearchSqlQueryMixin:

    def _search_in(self, table: str, tsquery: str) -> str:
        return f"{table}.search_content @@ {tsquery} = TRUE"

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
            3. Escape single quotes

            TODO The shit and confusing logic is due to the fact that partial
              search and URL search conflict and it is necessary to wrap the
              word in single quotes
        """

        words = self.search_text.replace("'", "''").split(' ')
        result = (
            " || ' | ' || ".join(
                [f"''%(search_{i})s'' || ':*'" for i in range(len(words))]
            )
        )
        params = {f'search_{i}': value for i, value in enumerate(words)}
        return f'to_tsquery({result})', params
