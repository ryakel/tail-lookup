"""SQLite database operations for tail-lookup."""
import sqlite3
from typing import Optional
from models import AircraftResponse, StatsResponse

AIRCRAFT_TYPES = {
    "1": "Glider",
    "2": "Balloon",
    "3": "Blimp/Dirigible",
    "4": "Fixed Wing Single-Engine",
    "5": "Fixed Wing Multi-Engine",
    "6": "Rotorcraft",
    "7": "Weight-Shift-Control",
    "8": "Powered Parachute",
    "9": "Gyroplane",
    "H": "Hybrid Lift",
    "O": "Other"
}

ENGINE_TYPES = {
    "0": "None",
    "1": "Reciprocating",
    "2": "Turbo-Prop",
    "3": "Turbo-Shaft",
    "4": "Turbo-Jet",
    "5": "Turbo-Fan",
    "6": "Ramjet",
    "7": "2-Cycle",
    "8": "4-Cycle",
    "9": "Unknown",
    "10": "Electric",
    "11": "Rotary"
}


class Database:
    def __init__(self, db_path: str):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row

    def close(self):
        self.conn.close()

    def lookup(self, n_number: str) -> Optional[AircraftResponse]:
        """Lookup aircraft by N-number (without 'N' prefix)."""
        cursor = self.conn.execute("""
            SELECT
                m.n_number,
                m.mfr_mdl_code,
                m.type_aircraft,
                m.type_engine,
                COALESCE(a.no_eng, m.no_eng) as no_eng,
                COALESCE(a.no_seats, m.no_seats) as no_seats,
                m.year_mfr,
                a.mfr AS manufacturer,
                a.model,
                a.series
            FROM master m
            LEFT JOIN acftref a ON m.mfr_mdl_code = a.code
            WHERE m.n_number = ?
        """, (n_number,))

        row = cursor.fetchone()
        if not row:
            return None

        return AircraftResponse(
            tail_number=f"N{row['n_number']}",
            manufacturer=row["manufacturer"] or "Unknown",
            model=row["model"] or "Unknown",
            series=row["series"] or None,
            aircraft_type=AIRCRAFT_TYPES.get(str(row["type_aircraft"]), "Unknown"),
            engine_type=ENGINE_TYPES.get(str(row["type_engine"]), "Unknown"),
            num_engines=int(row["no_eng"]) if row["no_eng"] else None,
            num_seats=int(row["no_seats"]) if row["no_seats"] else None,
            year_mfr=int(row["year_mfr"]) if row["year_mfr"] else None
        )

    def get_stats(self) -> StatsResponse:
        """Get database statistics."""
        cursor = self.conn.execute("SELECT COUNT(*) as cnt FROM master")
        count = cursor.fetchone()["cnt"]

        cursor = self.conn.execute(
            "SELECT value FROM metadata WHERE key = 'last_updated'"
        )
        row = cursor.fetchone()
        last_updated = row["value"] if row else None

        return StatsResponse(record_count=count, last_updated=last_updated)
