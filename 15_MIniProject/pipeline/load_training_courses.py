import pandas as pd
from pathlib import Path
from database.connection import db_cursor
from pipeline.validate_ncs_matching import normalize_ncs_code


def load_training_courses(csv_path: str):
    """Load training_courses CSV into PostgreSQL.
    - Apply NCS code normalization (soft FK, no FK constraint).
    - Unmatched / invalid NCS codes are stored as‑is (no NULL conversion).
    """
    df = pd.read_csv(csv_path, dtype=str)
    # Normalize NCS codes according to new rules
    df['ncs_cd'] = df['ncs_cd'].apply(normalize_ncs_code)
    # Ensure required columns exist (drop any unexpected) and order matches table definition
    cols = ['trpr_id', 'trpr_degr', 'ncs_cd', 'course_nm', 'provider_nm', 'start_dt', 'end_dt']
    df = df[cols]
    # Convert date columns to proper format, ignore errors (will become NaT -> None)
    for dcol in ['start_dt', 'end_dt']:
        if dcol in df.columns:
            df[dcol] = pd.to_datetime(df[dcol], errors='coerce').dt.date
    # Insert via COPY for speed
    with db_cursor() as cur:
        # Build CSV‑like string in memory
        from io import StringIO
        sio = StringIO()
        df.to_csv(sio, sep='\t', header=False, index=False, na_rep='\\N')
        sio.seek(0)
        cur.copy_expert(
            "COPY training_courses (trpr_id, trpr_degr, ncs_cd, course_nm, provider_nm, start_dt, end_dt) FROM STDIN WITH (FORMAT csv, DELIMITER '\t', NULL '\\N')",
            sio,
        )
    print(f"Loaded {len(df)} rows into training_courses")

if __name__ == '__main__':
    import sys
    if len(sys.argv) != 2:
        print('Usage: python load_training_courses.py <csv_path>')
        sys.exit(1)
    load_training_courses(sys.argv[1])
