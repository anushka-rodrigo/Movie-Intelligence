import logging
import time

from config.logging_config import setup_logging
from src.scripts.stage2_modules.stage2_extract_data import extract_data
from src.scripts.stage2_modules.stage2_fingerprint_data import (
    fingerprint_raw_data,
    save_or_verify_fingerprints,
)
from src.scripts.stage2_modules.stage2_assemble import build_all_tables
from src.scripts.stage2_modules.stage2_validate import validate_all
from src.scripts.stage2_modules.stage2_load import load_tables


def main():
    setup_logging()
    logger = logging.getLogger(__name__)
    started = time.time()

    logger.info("Starting Stage 2 ETL pipeline.")

    try:
        # 1. Verify that the raw data is the data we recorded
        logger.info("Verifying raw data fingerprints.")
        save_or_verify_fingerprints(fingerprint_raw_data())

        # 2. Extract
        logger.info("Starting data extraction.")
        tables = extract_data()
        for table_name, dataframe in tables.items():
            logger.info(
                "Extracted %s | rows: %s | columns: %s",
                table_name, dataframe.shape[0], dataframe.shape[1],
            )

        # 3. Clean and transform
        logger.info("Cleaning and building the final tables.")
        final_tables, coverage = build_all_tables(tables)

        # 4. Validate
        logger.info("Validating the final tables.")
        validate_all(final_tables, coverage)

        # 5. Load
        logger.info("Saving the final tables.")
        load_tables(final_tables)

        # 6. Prove the raw data was not touched
        logger.info("Re-verifying raw data fingerprints.")
        save_or_verify_fingerprints(fingerprint_raw_data())

        logger.info(
            "Stage 2 ETL pipeline completed successfully in %.0f seconds.",
            time.time() - started,
        )

    except Exception:
        logger.exception("Stage 2 ETL pipeline failed.")
        raise


if __name__ == "__main__":
    main()
