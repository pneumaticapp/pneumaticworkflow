from abc import ABC
from typing import Dict, Optional, Tuple


class OrderByMixin:

    ordering = None
    ordering_map: Optional[Dict[str, str]] = None

    def _get_ordering_column(self) -> Optional[str]:

        """ Returns expression for single field in ORDER BY clause

            Example input:
                self.ordering = '-date'
                self.ordering_map = {'-date': 'my_table.crated_date'}
            Result:
                my_table.crated_date DESC
        """

        ordering_column = None
        if self.ordering:
            field = self.ordering_map.get(self.ordering)
            if field:
                direction = 'DESC' if self.ordering.startswith('-') else 'ASC'
                ordering_column = f'{field} {direction}'
        return ordering_column

    def get_order_by(
        self,
        pre_columns: Optional[str] = None,
        post_columns: Optional[str] = None,
        default_column: Optional[str] = None
    ) -> str:

        """ Returns ORDER BY clause for SQL query

            Example input:
                ordering = '-date'
                pre_columns = 'my_table.account_id DESC'
                post_columns = 'other_table.name'
                self.ordering_map = {'-date': 'my_table.crated_date'}
            Result:
                ORDER BY
                  my_table.account_id DESC,
                  my_table.crated_date DESC,
                  other_table.name """

        column = self._get_ordering_column()
        if not column and default_column:
            column = default_column
        columns = []
        if column:
            if pre_columns:
                columns.append(pre_columns)
            columns.append(column)
            if post_columns:
                columns.append(post_columns)
        if columns:
            return f'ORDER BY {", ".join(columns)}'
        return ''


class SqlQueryObject(ABC):

    def get_sql(self) -> Tuple[str, dict]:
        pass

    def _to_sql_list(self, values, prefix) -> Tuple[str, dict]:
        if isinstance(values, int):
            values = (values, )

        result = ', '.join([f'%({prefix}_{i})s' for i in range(len(values))])
        params = {f'{prefix}_{i}': value for i, value in enumerate(values)}
        return f'({result})', params
