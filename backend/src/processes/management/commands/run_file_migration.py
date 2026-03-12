import psycopg2
import logging
from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
from django.conf import settings
from django.db import connection


class Command(BaseCommand):
    help = 'Run all file migration steps sequentially'

    def add_arguments(self, parser):
        parser.add_argument(
            '--account-ids',
            type=str,
            required=True,
            help='Comma-separated list of account IDs',
        )

    def check_file_db(self):
        db_name = settings.FILE_POSTGRES_DB
        user = settings.FILE_POSTGRES_USER
        password = settings.FILE_POSTGRES_PASSWORD
        host = settings.FILE_POSTGRES_HOST
        port = settings.FILE_POSTGRES_PORT

        if not all([db_name, user, password, host, port]):
            raise CommandError(
                "FILE_POSTGRES_* config missing in environment/settings.",
            )

        try:
            conn = psycopg2.connect(
                dbname=db_name,
                user=user,
                password=password,
                host=host,
                port=port,
            )
            self._verify_table(conn)
        except psycopg2.OperationalError:
            self.stdout.write(self.style.WARNING(
                f"Failed to connect to file service db at {host}:{port}, "
                "trying localhost:5433...",
            ))
            try:
                conn = psycopg2.connect(
                    dbname=db_name,
                    user=user,
                    password=password,
                    host='localhost',
                    port='5433',
                )
                self._verify_table(conn)
            except Exception as e:
                raise CommandError(
                    "Failed to connect to file database on fallback "
                    f"localhost:5433: {e}",
                ) from e
        except Exception as e:
            raise CommandError(
                f"Failed to connect to file database: {e}",
            ) from e

    def _verify_table(self, conn):
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT EXISTS (SELECT FROM information_schema.tables "
                "WHERE table_name = 'files');",
            )
            if not cursor.fetchone()[0]:
                conn.close()
                raise CommandError(
                    "The 'files' table does not exist in the file database! "
                    "Run file service migrations first.",
                )
            conn.close()
        except CommandError:
            raise
        except Exception as e:
            conn.close()
            raise CommandError(
                f"Failed to verify 'files' table in file database: {e}",
            ) from e

    def handle(self, *args, **options):
        self.stdout.write("Checking connection to main database...")
        try:
            with connection.cursor() as cursor:
                cursor.execute('SELECT 1')
        except Exception as e:
            raise CommandError(f"Main database is unreachable: {e}") from e

        self.stdout.write("Checking connection to file database...")
        self.check_file_db()
        self.stdout.write(self.style.SUCCESS(
            "All databases and tables verified! Starting migrations...",
        ))

        # Disable SQL logging to prevent utf-8 issues (Windows) and
        # huge memory leaks
        settings.DEBUG = False
        logging.getLogger('django.db.backends').setLevel(logging.WARNING)

        account_ids = options['account_ids']

        commands = [
            ('migrate', ['storage']),
            ('migrate', ['processes']),
            ('fill_file_attachment_file_id', []),
            ('migrate_file_attachment_to_attachment', []),
            ('sync_files_to_file_service', []),
            ('replace_storage_links_with_file_service', []),
        ]

        for cmd, cmd_args in commands:
            self.stdout.write(self.style.SUCCESS(
                "\n==============================================",
            ))
            if cmd == 'migrate':
                self.stdout.write(self.style.SUCCESS(
                    f"Running: manage.py {cmd} {cmd_args[0]}",
                ))
                self.stdout.write(self.style.SUCCESS(
                    "==============================================\n",
                ))
                call_command(cmd, *cmd_args)
            else:
                self.stdout.write(self.style.SUCCESS(
                    f"Running: manage.py {cmd} --account-ids={account_ids}",
                ))
                self.stdout.write(self.style.SUCCESS(
                    "==============================================\n",
                ))
                call_command(cmd, account_ids=account_ids)

        self.stdout.write(self.style.SUCCESS(
            '\n✅ All file migration steps completed successfully!',
        ))
