"""
WAIT_FOR_DB MANAGEMENT COMMAND

WHY IS THIS NEEDED?
When Docker starts, all containers launch simultaneously.
Django starts in ~2 seconds, but PostgreSQL takes ~5-10 seconds
to be ready to accept connections.

Without this command, Django crashes on startup with:
  "could not connect to server: Connection refused"

This command polls PostgreSQL every second until it's ready.

Usage (in docker-compose.yml):
  command: sh -c "python manage.py wait_for_db && python manage.py migrate && ..."
"""

import time
import logging
from django.core.management.base import BaseCommand
from django.db import connections
from django.db.utils import OperationalError

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Wait for database to be available before proceeding"

    def add_arguments(self, parser):
        parser.add_argument(
            "--timeout",
            type=int,
            default=60,
            help="Maximum seconds to wait (default: 60)",
        )

    def handle(self, *args, **options):
        timeout = options["timeout"]
        self.stdout.write("⏳ Waiting for database...")

        start_time = time.time()
        db_conn = None

        while not db_conn:
            elapsed = time.time() - start_time
            if elapsed > timeout:
                self.stdout.write(
                    self.style.ERROR(f"❌ Database not available after {timeout}s. Giving up.")
                )
                raise SystemExit(1)

            try:
                db_conn = connections["default"]
                db_conn.ensure_connection()
                self.stdout.write(self.style.SUCCESS("✅ Database is ready!"))
            except OperationalError:
                self.stdout.write(f"   Database unavailable ({elapsed:.0f}s elapsed), retrying in 1s...")
                time.sleep(1)
