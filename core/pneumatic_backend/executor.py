from django.db import connections


class RawSqlExecutor:

    @staticmethod
    def exists(query, params, db='default'):
        with connections[db].cursor() as cursor:
            cursor.execute(query, params)
            return bool(cursor.fetchone())

    @staticmethod
    def fetchone(query, params, db='default'):
        with connections[db].cursor() as cursor:
            cursor.execute(query, params)
            columns = [col[0] for col in cursor.description]
            return [
                dict(zip(columns, row))
                for row in cursor.fetchall()
            ][0]

    @staticmethod
    def execute(query, params, db='default'):
        with connections[db].cursor() as cursor:
            cursor.execute(query, params)

    @staticmethod
    def fetch(query, params, stream=False, fetch_size=300, db='default'):
        with connections[db].cursor() as cursor:
            cursor.execute(query, params)
            columns = [col[0] for col in cursor.description]
            if stream:
                while True:
                    results = cursor.fetchmany(fetch_size)
                    if not results:
                        break
                    for row in results:
                        yield dict(zip(columns, row))
            for row in cursor.fetchall():
                yield dict(zip(columns, row))
