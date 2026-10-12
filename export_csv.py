import argparse
import csv
import sqlite3
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(
        description="Export telemetry readings from SQLite to CSV."
    )
    parser.add_argument(
        "--database",
        default="telemetry.db",
        help="Input database filename."
    )
    parser.add_argument(
        "--output",
        default="telemetry.csv",
        help="Output CSV filename."
    )
    args = parser.parse_args()

    database_path = PROJECT_DIR / args.database
    output_path = PROJECT_DIR / args.output

    if not database_path.is_file():
        print(f"Database not found: {database_path}")
        raise SystemExit(1)

    if database_path.resolve() == output_path.resolve():
        print("The output file must differ from the database.")
        raise SystemExit(1)

    try:
        # Open in read-only mode to protect the source database.
        database_uri = database_path.resolve().as_uri() + "?mode=ro"
        connection = sqlite3.connect(database_uri, uri=True)

        try:
            cursor = connection.execute("""
                SELECT id, received_at_utc, uptime_ms, rpm
                FROM readings
                ORDER BY id
            """)

            with output_path.open(
                "w", newline="", encoding="utf-8"
            ) as output_file:
                writer = csv.writer(output_file)
                writer.writerow([
                    "id",
                    "received_at_utc",
                    "uptime_ms",
                    "rpm"
                ])

                row_count = 0

                for row in cursor:
                    writer.writerow(row)
                    row_count += 1

        finally:
            connection.close()

        print(f"Exported readings: {row_count}")
        print(f"CSV file: {output_path}")

    except (sqlite3.Error, OSError) as error:
        print(f"Export failed: {error}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
