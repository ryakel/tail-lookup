#!/usr/bin/env python3
"""
Download FAA aircraft registration data and build SQLite database.

Usage:
    python update_faa_data.py [output_path]

Default output: ./aircraft.db
"""
import csv
import io
import os
import sqlite3
import sys
import time
import zipfile
from datetime import datetime, timezone

try:
    import requests
except ImportError:
    print("Error: requests library not installed. Run: pip install requests")
    sys.exit(1)

FAA_URL = "https://registry.faa.gov/database/ReleasableAircraft.zip"

# Columns we need from MASTER.txt
MASTER_COLS = [
    "N-NUMBER", "SERIAL NUMBER", "MFR MDL CODE", "ENG MFR MDL", "YEAR MFR",
    "TYPE REGISTRANT", "NAME", "STREET", "STREET2", "CITY", "STATE", "ZIP CODE",
    "REGION", "COUNTY", "COUNTRY", "LAST ACTION DATE", "CERT ISSUE DATE",
    "CERTIFICATION", "TYPE AIRCRAFT", "TYPE ENGINE", "STATUS CODE", "MODE S CODE",
    "FRACT OWNER", "AIR WORTH DATE", "OTHER NAMES(1)", "OTHER NAMES(2)",
    "OTHER NAMES(3)", "OTHER NAMES(4)", "OTHER NAMES(5)", "EXPIRATION DATE",
    "UNIQUE ID", "KIT MFR", "KIT MODEL", "MODE S CODE HEX", "NO-ENG", "NO-SEATS"
]

# Columns we need from ACFTREF.txt
ACFTREF_COLS = ["CODE", "MFR", "MODEL", "TYPE-ACFT", "TYPE-ENG", "AC-CAT",
                "BUILD-CERT-IND", "NO-ENG", "NO-SEATS", "AC-WEIGHT", "SPEED", "TC-DATA-SHEET", "TC-DATA-HOLDER"]


def download_faa_data() -> zipfile.ZipFile:
    """Download FAA database ZIP file with retries."""
    print(f"Downloading {FAA_URL}...")

    max_retries = 3
    timeout = 300  # 5 minutes

    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(
                FAA_URL,
                timeout=timeout,
                stream=True,
                headers={'User-Agent': 'tail-lookup-builder/1.0'}
            )
            response.raise_for_status()

            # Download with progress
            data = bytearray()
            for chunk in response.iter_content(chunk_size=8192):
                data.extend(chunk)

            print(f"Downloaded {len(data) / 1e6:.1f} MB")
            return zipfile.ZipFile(io.BytesIO(data))

        except (requests.exceptions.Timeout, requests.exceptions.RequestException) as e:
            if attempt < max_retries:
                wait_time = attempt * 10  # Exponential backoff: 10s, 20s, 30s
                print(f"Download failed (attempt {attempt}/{max_retries}): {e}")
                print(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                print(f"Download failed after {max_retries} attempts")
                raise


def parse_csv(zf: zipfile.ZipFile, filename: str, expected_cols: list) -> list[dict]:
    """Parse a CSV file from the ZIP archive."""
    print(f"Parsing {filename}...")
    with zf.open(filename) as f:
        # FAA files are UTF-8 with BOM (Byte Order Mark)
        text = io.TextIOWrapper(f, encoding="utf-8-sig", errors="replace")
        reader = csv.reader(text)
        header = [col.strip() for col in next(reader)]

        # Map expected columns to actual positions
        col_map = {}
        for col in expected_cols:
            if col in header:
                col_map[col] = header.index(col)
        
        rows = []
        for row in reader:
            record = {}
            for col, idx in col_map.items():
                if idx < len(row):
                    record[col] = row[idx].strip()
                else:
                    record[col] = ""
            rows.append(record)
    
    print(f"  Parsed {len(rows):,} records")
    return rows


def build_database(master_rows: list, acftref_rows: list, output_path: str):
    """Build SQLite database from parsed data."""
    print(f"Building database at {output_path}...")
    
    if os.path.exists(output_path):
        os.remove(output_path)
    
    conn = sqlite3.connect(output_path)
    cur = conn.cursor()
    
    # Create tables
    cur.execute("""
        CREATE TABLE master (
            n_number TEXT PRIMARY KEY,
            mfr_mdl_code TEXT,
            type_aircraft TEXT,
            type_engine TEXT,
            no_eng TEXT,
            no_seats TEXT,
            year_mfr TEXT
        )
    """)
    
    cur.execute("""
        CREATE TABLE acftref (
            code TEXT PRIMARY KEY,
            mfr TEXT,
            model TEXT,
            series TEXT,
            no_eng TEXT,
            no_seats TEXT
        )
    """)
    
    cur.execute("""
        CREATE TABLE metadata (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    
    # Insert ACFTREF data (need this for JOIN)
    acftref_data = [
        (
            row.get("CODE", ""),
            row.get("MFR", ""),
            row.get("MODEL", ""),
            "",  # Series not in ACFTREF, derive from model name
            row.get("NO-ENG", ""),
            row.get("NO-SEATS", "")
        )
        for row in acftref_rows
        if row.get("CODE")
    ]
    cur.executemany(
        "INSERT OR IGNORE INTO acftref VALUES (?, ?, ?, ?, ?, ?)",
        acftref_data
    )
    print(f"  Inserted {len(acftref_data):,} aircraft reference records")
    
    # Insert MASTER data
    master_data = [
        (
            row.get("N-NUMBER", ""),
            row.get("MFR MDL CODE", ""),
            row.get("TYPE AIRCRAFT", ""),
            row.get("TYPE ENGINE", ""),
            row.get("NO-ENG", "") or row.get("ENG MFR MDL", "")[:1],  # Fallback
            row.get("NO-SEATS", ""),
            row.get("YEAR MFR", "")
        )
        for row in master_rows
        if row.get("N-NUMBER")
    ]
    cur.executemany(
        "INSERT OR IGNORE INTO master VALUES (?, ?, ?, ?, ?, ?, ?)",
        master_data
    )
    print(f"  Inserted {len(master_data):,} registration records")
    
    # Add metadata
    cur.execute(
        "INSERT INTO metadata VALUES (?, ?)",
        ("last_updated", datetime.now(timezone.utc).isoformat())
    )
    
    # Create index for faster lookups
    cur.execute("CREATE INDEX idx_mfr_mdl ON master(mfr_mdl_code)")
    
    conn.commit()
    conn.close()
    
    size_mb = os.path.getsize(output_path) / 1e6
    print(f"Database created: {output_path} ({size_mb:.1f} MB)")


def main():
    output_path = sys.argv[1] if len(sys.argv) > 1 else "./aircraft.db"
    
    zf = download_faa_data()
    
    # Find the actual filenames (they might have slight variations)
    files = zf.namelist()
    master_file = next((f for f in files if "MASTER" in f.upper()), None)
    acftref_file = next((f for f in files if "ACFTREF" in f.upper()), None)
    
    if not master_file or not acftref_file:
        print(f"Error: Could not find MASTER or ACFTREF in ZIP. Files: {files}")
        sys.exit(1)
    
    master_rows = parse_csv(zf, master_file, MASTER_COLS)
    acftref_rows = parse_csv(zf, acftref_file, ACFTREF_COLS)
    
    build_database(master_rows, acftref_rows, output_path)
    print("Done!")


if __name__ == "__main__":
    main()
