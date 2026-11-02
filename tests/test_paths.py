from config.paths import (
    PROJECT_ROOT,
    RAW_DATA_DIR,
    PROCESSED_DATA_DIR
)

print("Project Root:", PROJECT_ROOT)
print("Raw Data:", RAW_DATA_DIR)
print("Processed Data:", PROCESSED_DATA_DIR)

print("Raw folder exists:", RAW_DATA_DIR.exists())
print("Processed folder exists:", PROCESSED_DATA_DIR.exists())

# run the following code at root to test
# python -m tests.test_paths