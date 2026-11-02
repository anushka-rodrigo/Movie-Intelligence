# Stage 2 — Entry Point and Logging

## 1. Purpose

Before this step, each Stage 2 script had to be run separately, and progress was reported with scattered `print()` statements.

This step adds two things:

- **Centralized logging:** one reusable configuration that writes messages to both the terminal and a log file.
- **A single entry point:** one script that runs fingerprint verification and extraction in order, so the whole pipeline starts with one command.

The entry point does not contain any extraction or fingerprinting logic. It only calls the functions we already built. This is called **orchestration**.

## 2. Logging configuration

The configuration is in:

```text
config/logging_config.py
```

```python
import logging
from config.paths import LOG_DIR


def setup_logging():
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOG_DIR / "stage2_etl.log"

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler()
        ],
        force=True
    )
```

How it works:

- `LOG_DIR` comes from `config/paths.py`, so the log location is not hardcoded.
- `mkdir(parents=True, exist_ok=True)` creates the `logs/` folder if it is missing and does not fail if it already exists.
- `level=logging.INFO` records INFO messages and anything more severe (WARNING, ERROR).
- `format` makes every line show the timestamp, severity, logger name and message.
- `FileHandler` saves messages to `logs/stage2_etl.log`.
- `StreamHandler` shows the same messages in the terminal.
- `force=True` replaces any earlier logging setup, so the configuration is always the one defined here.

## 3. Testing the logging

The check script is:

```text
tests/check_logging.py
```

```python
import logging
from config.logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

logger.info("Logging test started.")
logger.warning("This is a sample warning.")
logger.error("This is a sample error.")

print("\nLogging test completed.")
```

Run from the project root:

```powershell
python -m tests.check_logging
```

Output:

```text
2026-11-02 09:31:39,182 | INFO | __main__ | Logging test started.
2026-11-02 09:31:39,182 | WARNING | __main__ | This is a sample warning.
2026-11-02 09:31:39,182 | ERROR | __main__ | This is a sample error.

Logging test completed.
```

The warning and error are deliberate samples to show the three severity levels. They are not pipeline failures. The same three messages were also written to `logs/stage2_etl.log`.

## 4. Keeping logs out of Git

A log file is generated every time the pipeline runs. It grows over time, contains run-specific timestamps, and can be recreated at any time, so it should not be committed.

This line was added to `.gitignore`:

```text
# Generated log files
logs/*.log
```

The `logs/` folder itself stays in the project.

## 5. The pipeline entry point

The entry point is:

```text
src/scripts/stage2_pipeline.py
```

```python
import logging

from config.logging_config import setup_logging
from src.scripts.stage2_extract_data import extract_data
from src.scripts.stage2_fingerprint_data import (
    fingerprint_raw_data,
    save_or_verify_fingerprints,
)


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

        logger.info("Stage 2 ETL pipeline completed successfully.")

    except Exception:
        logger.exception("Stage 2 ETL pipeline failed.")
        raise


if __name__ == "__main__":
    main()
```

What it does, in order:

1. Sets up logging.
2. Calculates the raw-file fingerprints and verifies them against the saved manifest (see the fingerprinting document).
3. Extracts the five raw datasets with `extract_data()`.
4. Logs the row and column count of each dataset.

The `try` / `except` block handles failures:

- `logger.exception()` writes the error and its full traceback to the log.
- `raise` re-raises the error, so a failed run is reported as a failure and never looks successful.

Because fingerprint verification runs first, the pipeline stops before extraction if a raw file has changed.

## 6. Running the pipeline

From the project root in PowerShell:

```powershell
python -m src.scripts.stage2_pipeline
```

This single command verifies the raw data, extracts the five datasets (including the large ratings file) and writes the run's progress to both the terminal and `logs/stage2_etl.log`.

## 7. Known limitation

The extraction and fingerprinting scripts still use some `print()` calls. Those messages appear in the terminal but are not written to the log file. They will be converted to logging in a later step.

## 8. Result

**The entry point and logging are in place.** The project has one reusable logging configuration and one script that coordinates fingerprint verification and extraction, so running the pipeline now takes a single command and leaves a log of what happened.