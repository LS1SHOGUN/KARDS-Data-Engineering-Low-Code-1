"""
Load Kards gold-layer CSV exports into SQL Server 2025 (KardsWarehouse DB).

Requirements:
    pip install pandas sqlalchemy pyodbc

You also need the "ODBC Driver 18 for SQL Server" installed on Windows
(usually already present if you have SSMS installed; if not, download from
Microsoft: "ODBC Driver 18 for SQL Server").
"""

import pandas as pd
from sqlalchemy import create_engine
import urllib
import os

# Folder where this script (and the CSV files) live.
# Change this if your CSVs are somewhere else, e.g.:
BASE_DIR = r"C:\Users\swethakarunamoorthy\Downloads"
# BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ---- CONNECTION SETTINGS ----
SERVER = r"SWETHA\SQL2025"   # e.g. SWETHA\SQL2025
DATABASE = "KardsWarehouse"
# Use Windows Authentication (Trusted Connection) — no username/password needed
# since your Windows account is already an admin on this instance.

params = urllib.parse.quote_plus(
    f"DRIVER={{ODBC Driver 18 for SQL Server}};"
    f"SERVER={SERVER};"
    f"DATABASE={DATABASE};"
    f"Trusted_Connection=yes;"
    f"TrustServerCertificate=yes;"
)
engine = create_engine(f"mssql+pyodbc:///?odbc_connect={params}")

# ---- FILES TO LOAD ----
tables = {
    "FULL_CARDS_KARDS": "FULL_CARDS_KARDS.csv",
    "FORECAST": "FORECAST.csv",
    "RETRIBUTION": "RETRIBUTION.csv",
}

for table_name, csv_file in tables.items():
    csv_path = os.path.join(BASE_DIR, csv_file)
    print(f"Loading {csv_path} -> {table_name} ...")
    df = pd.read_csv(csv_path, encoding="utf-8-sig")

    # Add a surrogate key so every row has a unique identifier
    # (useful since CardId repeats for veteran/spawn variants).
    df.insert(0, "RowId", range(1, len(df) + 1))

    df.to_sql(
        table_name,
        engine,
        if_exists="replace",   # drops & recreates the table each run
        index=False,
        chunksize=500
    )
    print(f"  -> {len(df)} rows loaded.")

print("Done.")