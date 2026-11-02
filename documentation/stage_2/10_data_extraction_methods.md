# Movie Intelligence — Stage 2 Progress Notes

## 1. What has been completed

So far, Stage 2 (ETL) has covered two things:

1. Centralizing project paths.
2. Writing and checking the data extraction function.

The goal is to make the pipeline easier to run, maintain, and test before starting any data cleaning.

---

## 2. Centralizing project paths

### The problem with hardcoded relative paths

Initially, the extraction function used:

```python
DATA = Path("../../data/raw_data")
```

This is a relative path. Its meaning depends on the directory from which Python is run. Running the same script from a different working directory can therefore make the path point somewhere else.

### The solution: `config/paths.py`

A central paths file was created so project directories are defined in one place:

```python
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw_data"
PROCESSED_DATA_DIR = DATA_DIR / "processed"

LOG_DIR = PROJECT_ROOT / "logs"
TEST_DIR = PROJECT_ROOT / "tests"

SRC_DIR = PROJECT_ROOT / "src"
SCRIPTS_DIR = SRC_DIR / "scripts"
```

### How it works

- `Path(__file__)` refers to the current `paths.py` file.
- `.resolve()` converts it into an absolute path.
- `.parent` moves one directory up.
- `.parent.parent` moves up two directories, reaching the project root because `paths.py` is inside `config/`.
- The `/` operator joins path components using `pathlib`, without manually writing Windows or Linux path separators.

For example, `RAW_DATA_DIR` points to the project's `data/raw_data` directory.

### Why this is useful

- Paths are defined once rather than repeated throughout the project.
- Moving or reorganizing folders is easier because path changes can be made centrally.
- The code is less dependent on the current working directory.
- `pathlib` handles platform-specific path separators.

The path configuration was checked with a small test script, run from the project root:

```powershell
python -m tests.test_paths
```

The check confirmed that the configured paths resolved as expected.

---

## 3. Writing the extraction function

The extraction function is in:

```text
src/scripts/stage2_ETL_pipeline.py
```

Its job at this stage is to load the five original CSV files into pandas DataFrames. It does not clean, repair, or remove records yet.

The extraction code uses the centralized raw-data path:

```python
import pandas as pd
from config.paths import RAW_DATA_DIR
```

Instead of defining another relative path inside the function, it imports `RAW_DATA_DIR` from `config/paths.py`.

### Expected row counts

The row counts below were recorded during Stage 1 and are used as extraction checks:

```python
EXPECTED_ROW_COUNTS = {
    "credits": 45_476,
    "keywords": 46_419,
    "links": 45_843,
    "movies_metadata": 45_466,
    "ratings": 26_024_289,
}
```

These are validation expectations based on the source files investigated in Stage 1. If a count differs, the pipeline should stop and the discrepancy should be investigated rather than silently accepted.

### Loading the CSV files

The function reads the five files:

```python
def extract_data():
    credits = pd.read_csv(RAW_DATA_DIR / "credits.csv")
    keywords = pd.read_csv(RAW_DATA_DIR / "keywords.csv")
    links = pd.read_csv(RAW_DATA_DIR / "links.csv")

    movies_metadata = pd.read_csv(
        RAW_DATA_DIR / "movies_metadata.csv",
        low_memory=False
    )

    ratings = pd.read_csv(
        RAW_DATA_DIR / "ratings.csv",
        dtype={
            "userId": "int32",
            "movieId": "int32",
            "rating": "float32",
            "timestamp": "int32"
        }
    )
```

A couple of loading choices are intentional:

- `low_memory=False` is used for `movies_metadata.csv` because some columns contain mixed data types. It asks pandas to infer column types using the full file rather than processing it in smaller chunks for type inference.
- Explicit `dtype` values are used for `ratings.csv`, which contains over 26 million rows. Smaller numeric types can reduce memory usage compared with pandas' usual defaults, provided the values fit those types.

### Grouping the extracted DataFrames

The loaded DataFrames are placed into a dictionary:

```python
    tables = {
        "credits": credits,
        "keywords": keywords,
        "links": links,
        "movies_metadata": movies_metadata,
        "ratings": ratings,
    }
```

This makes the datasets accessible by name, for example:

```python
tables["ratings"]
tables["movies_metadata"]
```

The key `"movies_metadata"` is used instead of the shorter `"meta"` to make the dataset's identity clearer.

### Validating row counts

Each extracted DataFrame is checked against the expected count:

```python
    for table_name, dataframe in tables.items():
        actual_rows = len(dataframe)
        expected_rows = EXPECTED_ROW_COUNTS[table_name]

        if actual_rows != expected_rows:
            raise ValueError(
                f"Row count mismatch in {table_name}: "
                f"expected {expected_rows:,}, "
                f"got {actual_rows:,}"
            )

        print(f"{table_name}: {actual_rows:,} rows - PASS")

    return tables
```

Important concepts:

- `len(dataframe)` returns the number of rows.
- `tables.items()` lets us iterate over each dictionary key and its DataFrame.
- `raise ValueError(...)` stops execution if a row count is unexpected.
- `:,` in an f-string formats large numbers with thousands separators.
- `return tables` sends the extracted DataFrames back to the code that called the function.

The `return` is important: without it, another script calling `extract_data()` would not receive the dictionary of DataFrames.

**Scope of this check:** matching row counts confirms that the expected number of records was loaded. It does not prove that every value is correct or that the files are free of data-quality issues. Those checks belong to later ETL steps.

---

## 4. Writing and running the extraction check script

A separate check script was created at:

```text
tests/check_extraction.py
```

Its code is:

```python
from src.scripts.stage2_extract_data import extract_data

tables = extract_data()

print("\nExtraction completed successfully!")
print("\nAvailable datasets:")

for name, df in tables.items():
    print(f"{name}: {df.shape}")
```

### What this script does

1. Imports the `extract_data()` function from the pipeline module.
2. Calls the function, which loads the CSV files and validates their row counts.
3. Prints a success message if extraction completes without an error.
4. Iterates through the returned dictionary and prints each DataFrame's shape.

`df.shape` returns a tuple:

```text
(number_of_rows, number_of_columns)
```

For example, `(45476, 3)` means 45,476 rows and 3 columns.

This is an extraction check/integration-style script. It is not yet a formal `pytest` test suite. Formal automated tests are planned for a later stage.

### How the command is executed

The command used in PowerShell, from the project root, was:

```powershell
python -m tests.check_extraction
```

The `-m` option tells Python to run the specified module. The dotted name `tests.check_extraction` represents the `check_extraction.py` module inside the `tests` package/directory.

Running from the project root helps Python resolve project-level imports such as `config.paths` and `src.scripts.stage2_ETL_pipeline`.

The earlier path check was run with:

```powershell
python -m tests.test_paths
```

---

## 5. Successful extraction result

The extraction check produced:

```text
credits: 45,476 rows - PASS
keywords: 46,419 rows - PASS
links: 45,843 rows - PASS
movies_metadata: 45,466 rows - PASS
ratings: 26,024,289 rows - PASS

Extraction completed successfully!

Available datasets:
credits: (45476, 3)
keywords: (46419, 2)
links: (45843, 3)
movies_metadata: (45466, 24)
ratings: (26024289, 4)
```

All five actual row counts matched the expected row counts recorded during Stage 1.

The shapes also show the number of columns loaded from each CSV:

| Dataset | Rows | Columns |
|---|---:|---:|
| credits | 45,476 | 3 |
| keywords | 46,419 | 2 |
| links | 45,843 | 3 |
| movies_metadata | 45,466 | 24 |
| ratings | 26,024,289 | 4 |

This confirms that the extraction function loaded the expected number of rows and returned all five DataFrames.

---

## 6. What is `__pycache__`?

After running Python modules, folders named `__pycache__` appeared in the project.

These are generated by Python and contain compiled bytecode files (`.pyc`). Python can reuse these files to make module imports faster.

- They are not source code.
- They do not need to be edited.
- They can be deleted; Python will recreate them when needed.
- They should not normally be committed to Git.

Add these rules to `.gitignore`:

```gitignore
# Python cache files
__pycache__/
*.py[cod]

# Virtual environments
venv/
.venv/

# Jupyter Notebook checkpoints
.ipynb_checkpoints/
```

---

## 7. Current progress and next step

**Completed:**
- Centralized project paths in `config/paths.py`.
- Verified the configured paths.
- Updated extraction to use `RAW_DATA_DIR`.
- Loaded all five original CSV files.
- Added expected row-count validation.
- Returned the extracted DataFrames in a dictionary.
- Created and ran a separate extraction check script.
- Confirmed that all five row-count checks passed.

**Next planned step:** create SHA-256 fingerprints for the raw CSV files. These fingerprints will help verify that the original source files have not changed during the ETL process.

No data cleaning or repair has been performed yet. The raw data is still being treated as the original source.
