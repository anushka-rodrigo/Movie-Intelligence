import logging

from config.logging_config import setup_logging
from src.scripts.stage2_modules.stage2_extract_data import extract_data
from src.scripts.stage2_modules.stage2_fingerprint_data import (
    fingerprint_raw_data,
    save_or_verify_fingerprints,
)
from src.scripts.stage2_modules.stage2_clean_metadata import clean_movies_metadata


def main():
    setup_logging()

    logger = logging.getLogger(__name__)

    logger.info("Starting Stage 2 ETL pipeline.")

    try:
        # Step 1: Verify raw data integrity
        logger.info("Verifying raw data fingerprints.")

        fingerprints = fingerprint_raw_data()
        save_or_verify_fingerprints(fingerprints)

        logger.info("Raw data fingerprint verification completed.")

        # Step 2: Extract source datasets
        logger.info("Starting data extraction.")

        tables = extract_data()

        logger.info("Data extraction completed successfully.")

        # Step 3: Log extracted dataset information
        for table_name, dataframe in tables.items():
            logger.info(
                "Dataset: %s | Rows: %s | Columns: %s",
                table_name,
                dataframe.shape[0],
                dataframe.shape[1],
            )

        # Step 4: Clean movies_metadata
        logger.info("Starting movies_metadata cleaning.")

        clean_metadata = clean_movies_metadata(tables["movies_metadata"])

        logger.info(
            "movies_metadata cleaning completed: %s rows -> %s rows.",
            len(tables["movies_metadata"]),
            len(clean_metadata),
        )

        logger.info("Stage 2 ETL pipeline completed successfully.")

    except Exception:
        logger.exception("Stage 2 ETL pipeline failed.")
        raise


if __name__ == "__main__":
    main()