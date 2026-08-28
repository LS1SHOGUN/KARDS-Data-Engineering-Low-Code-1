"""
Generate embeddings for all three Kards gold-layer tables and write them
into SQL Server 2025's VECTOR columns.

Requirements:
    pip install sentence-transformers pandas sqlalchemy pyodbc

First run downloads the model (~90MB) from Hugging Face and caches it
locally (~/.cache/huggingface) — after that it works fully offline.
"""

from sentence_transformers import SentenceTransformer
import pandas as pd
from sqlalchemy import create_engine, text
import urllib
import json

# ---- CONNECTION SETTINGS ----
SERVER = r"SWETHA\SQL2025"   # e.g. SWETHA\SQL2025
DATABASE = "KardsWarehouse"

params = urllib.parse.quote_plus(
    f"DRIVER={{ODBC Driver 18 for SQL Server}};"
    f"SERVER={SERVER};"
    f"DATABASE={DATABASE};"
    f"Trusted_Connection=yes;"
    f"TrustServerCertificate=yes;"
)
engine = create_engine(f"mssql+pyodbc:///?odbc_connect={params}")

# ---- LOAD MODEL ----
# 'all-MiniLM-L6-v2' -> 384-dim embeddings. Make sure this matches the
# VECTOR(n) size you used in each ALTER TABLE statement.
model = SentenceTransformer("all-MiniLM-L6-v2")
VECTOR_DIM = 384

# ---- TABLE CONFIG ----
# Each entry: table name, name column, effect/text column, embedding column
tables = [
    {
        "table": "gold.FULL_CARDS_KARDS",
        "name_col": "CardName",
        "effect_col": "CardEffect",
        "embedding_col": "CardEffectEmbedding",
    },
    {
        "table": "gold.FORECAST",
        "name_col": "ForecastCardName",
        "effect_col": "ForecastCardEffect",
        "embedding_col": "CardEffectEmbedding",
    },
    {
        "table": "gold.RETRIBUTION",
        "name_col": "RetributionCardName",
        "effect_col": "RetributionCardEffect",
        "embedding_col": "CardEffectEmbedding",
    },
]

for cfg in tables:
    table = cfg["table"]
    name_col = cfg["name_col"]
    effect_col = cfg["effect_col"]
    embedding_col = cfg["embedding_col"]

    print(f"\n=== {table} ===")
    df = pd.read_sql(f"SELECT RowId, {name_col}, {effect_col} FROM {table}", engine)

    texts = (df[name_col].fillna("") + ". " + df[effect_col].fillna("")).tolist()

    print(f"Generating embeddings for {len(texts)} rows...")
    embeddings = model.encode(texts, show_progress_bar=True)

    print(f"Writing embeddings back to {table}.{embedding_col} ...")
    with engine.begin() as conn:
        for row_id, vec in zip(df["RowId"], embeddings):
            vec_json = json.dumps(vec.tolist())
            conn.execute(
                text(f"""
                    UPDATE {table}
                    SET {embedding_col} = CAST(CAST(:vec AS NVARCHAR(MAX)) AS VECTOR({VECTOR_DIM}))
                    WHERE RowId = :row_id
                """),
                {"vec": vec_json, "row_id": int(row_id)}
            )
    print(f"  -> {len(df)} rows updated.")

print("\nDone — embeddings written for all three tables.")