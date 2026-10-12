import argparse
import sqlite3
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(
        description="Run SQL analysis on a telemetry database."
    )
    parser.add_argument("--database", default="telemetry.db")
    args = parser.parse_args()

    database_path = (PROJECT_DIR / args.database).resolve()
    queries_path = PROJECT_DIR / "queries.sql"

    if not database_path.is_file():
        raise FileNotFoundError(f"Database not found: {database_path}")

    sql_text = queries_path.read_text(encoding="utf-8")
    statements = []
    pending = ""

    for line in sql_text.splitlines():
        pending += line + "\n"
        if sqlite3.complete_statement(pending):
            statements.append(pending.strip())
            pending = ""

    if pending.strip():
        raise ValueError("Incomplete SQL statement in queries.sql")

    connection = sqlite3.connect(
        database_path.as_uri() + "?mode=ro",
        uri=True,
    )

    try:
        connection.execute("PRAGMA query_only = ON")
        print(f"Database: {database_path}")
        print("Read-only analysis. No data will be changed.")

        for number, statement in enumerate(statements, start=1):
            cursor = connection.execute(statement)
            columns = [column[0] for column in cursor.description]

            print(f"\n--- Query {number} ---")
            print(" | ".join(columns))

            for row in cursor:
                print(" | ".join(
                    "NULL" if value is None else str(value)
                    for value in row
                ))
    finally:
        connection.close()


if __name__ == "__main__":
    try:
        main()
    except (OSError, sqlite3.Error, ValueError) as error:
        print(f"Analysis failed: {error}")
        raise SystemExit(1)