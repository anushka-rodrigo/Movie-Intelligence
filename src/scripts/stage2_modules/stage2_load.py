import json
import logging
import os

from config.paths import PROCESSED_DATA_DIR
from src.scripts.stage2_modules.stage2_fingerprint_data import calculate_sha256
from src.scripts.stage2_modules.stage2_table_specs import TABLE_SPECS

logger = logging.getLogger(__name__)

MANIFEST_NAME = "processed_data_manifest.json"

def cast_integer_columns(table, columns):
    """Return a copy of the table with the given float columns converted to nullable integers.

    PostgreSQL rejects text such as 4000000.0 in an integer column. Missing values stay missing,
    and pandas raises an error if a value is not a whole number.
    """
    return table.assign(**{column: table[column].astype("Int64") for column in columns})

def load_tables(tables):
    """Write every final table to data/processed as CSV, and record rows and SHA-256 per file."""
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    manifest = {}

    for name, spec in TABLE_SPECS.items():
        table = tables[name]

        # A fixed row order makes the output identical on every run
        if spec["sort"]:
            table = table.sort_values(spec["key"]).reset_index(drop=True)
        
        table = cast_integer_columns(table, spec.get("integer_columns", []))   # <- new line
        
        final_path = PROCESSED_DATA_DIR / f"{name}.csv"
        temp_path = PROCESSED_DATA_DIR / f"{name}.csv.tmp"

        # Write to a temporary file first, so a crash never leaves a half-written table
        table.to_csv(temp_path, index=False, encoding="utf-8", lineterminator="\n")
        os.replace(temp_path, final_path)

        manifest[final_path.name] = {
            "rows": len(table),
            "sha256": calculate_sha256(final_path),
        }
        logger.info("load_tables: wrote %s (%s rows).", final_path.name, len(table))

    manifest_path = PROCESSED_DATA_DIR / MANIFEST_NAME
    with open(manifest_path, "w", encoding="utf-8") as file:
        json.dump(manifest, file, indent=4, sort_keys=True)

    return manifest
