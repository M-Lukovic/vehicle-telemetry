import argparse
import csv
import math
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import serial


SERIAL_PORT = "COM5"
BAUD_RATE = 115200
DATABASE_PATH = Path(__file__).resolve().parent / "telemetry.db"


def main():
    parser = argparse.ArgumentParser(description="Collect vehicle RPM from USB serial.")
    parser.add_argument("--port", default=SERIAL_PORT, help="Serial port, for example COM5.")
    args = parser.parse_args()
    connection = sqlite3.connect(DATABASE_PATH)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            received_at_utc TEXT NOT NULL,
            uptime_ms INTEGER NOT NULL,
            rpm REAL NOT NULL CHECK (rpm >= 0 AND rpm <= 16383.75)
        )
    """)
    connection.commit()

    saved_count = 0
    pending = bytearray()

    try:
        with serial.Serial(
            args.port, BAUD_RATE, timeout=1
        ) as device:
            print(f"Connected to {args.port} at {BAUD_RATE} baud.")
            print(f"Database: {DATABASE_PATH}")
            print("Waiting for readings. Press Ctrl+C to stop.")

            while True:
                chunk = device.read(
                    min(max(device.in_waiting, 1), 4096)
                )

                if not chunk:
                    continue

                pending.extend(chunk)

                # Keep incomplete lines until more bytes arrive.
                while b"\n" in pending:
                    raw_line, _, remainder = pending.partition(b"\n")
                    pending = bytearray(remainder)

                    line = raw_line.decode(
                        "utf-8", errors="replace"
                    ).strip()

                    if not line:
                        continue

                    if line.startswith("#"):
                        print(line)
                        continue

                    if line == "uptime_ms,rpm":
                        continue

                    try:
                        fields = next(csv.reader([line]))

                        if len(fields) != 2:
                            raise ValueError("Expected two fields.")

                        uptime_ms = int(fields[0])
                        rpm = float(fields[1])

                        if not 0 <= uptime_ms <= 4294967295:
                            raise ValueError("Invalid uptime.")

                        if not math.isfinite(rpm):
                            raise ValueError("RPM must be finite.")

                        if not 0 <= rpm <= 16383.75:
                            raise ValueError("Invalid RPM.")

                    except (ValueError, csv.Error):
                        print(f"Skipped non-measurement line: {line}")
                        continue

                    received_at = datetime.now(
                        timezone.utc
                    ).isoformat(timespec="milliseconds")

                    connection.execute(
                        """
                        INSERT INTO readings (
                            received_at_utc, uptime_ms, rpm
                        )
                        VALUES (?, ?, ?)
                        """,
                        (received_at, uptime_ms, rpm)
                    )
                    connection.commit()

                    saved_count += 1
                    print(
                        f"Saved #{saved_count} | "
                        f"{received_at} | RPM: {rpm:.2f}"
                    )

                # Prevent unlimited buffering of malformed input.
                if len(pending) > 8192:
                    pending.clear()
                    print("Discarded oversized incomplete line.")

    except KeyboardInterrupt:
        print("\nCollection stopped.")

    except serial.SerialException as error:
        print(f"Serial error: {error}")
        print(
            "Check the USB connection and close other "
            "programs using the serial port."
        )

    except sqlite3.Error as error:
        print(f"Database error: {error}")

    finally:
        connection.close()
        print(f"Readings saved during this run: {saved_count}")


if __name__ == "__main__":
    main()
