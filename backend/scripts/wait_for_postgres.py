"""Wait until Postgres accepts connections (used by Docker entrypoint)."""

from __future__ import annotations

import os
import sys
import time

import psycopg2

MAX_ATTEMPTS = 60
SLEEP_SEC = 1.0


def main() -> None:
    host = os.environ["POSTGRES_HOST"]
    port = os.environ.get("POSTGRES_PORT", "5432")
    user = os.environ["POSTGRES_USER"]
    password = os.environ["POSTGRES_PASSWORD"]
    dbname = os.environ["POSTGRES_DB"]

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            conn = psycopg2.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                dbname=dbname,
                connect_timeout=3,
            )
            conn.close()
            print(f"Postgres is ready ({host}:{port}).", file=sys.stderr)
            return
        except Exception as e:  # noqa: BLE001
            if attempt == MAX_ATTEMPTS:
                print(f"Postgres not reachable after {MAX_ATTEMPTS} attempts: {e}", file=sys.stderr)
                sys.exit(1)
            print(
                f"Waiting for Postgres ({attempt}/{MAX_ATTEMPTS})…",
                file=sys.stderr,
            )
            time.sleep(SLEEP_SEC)


if __name__ == "__main__":
    main()
