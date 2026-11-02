# Stage 2 — Raw Data Fingerprinting

## 1. Purpose

Before cleaning or transforming the Kaggle data, we added a way to check whether the original CSV files have changed.

We use **SHA-256 fingerprints** for this. A fingerprint is a 64-character hexadecimal hash calculated from a file's exact bytes. It acts like a digital checksum for that particular file.

If the file's contents change, its SHA-256 hash will almost certainly change too. Matching hashes provide strong evidence that two files have identical contents.

A fingerprint does not lock a file, prevent editing, or prove where the file came from. It lets us compare a file against a previously recorded version.

## 2. Calculating a SHA-256 fingerprint

The script is:

```text
src/scripts/stage2_fingerprint_data.py
```

It uses Python's built-in `hashlib` library:

```python
import hashlib

def calculate_sha256(file_path):
    sha256_hash = hashlib.sha256()

    with open(file_path, "rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            sha256_hash.update(chunk)

    return sha256_hash.hexdigest()
```

How it works:

- `hashlib.sha256()` creates a SHA-256 hash calculator.
- `open(file_path, "rb")` opens the file in binary read mode. Hashing the bytes means we calculate a fingerprint from the file's exact contents.
- `file.read(1024 * 1024)` reads up to 1 MB at a time.
- Reading in chunks avoids loading a large file, such as the 26-million-row ratings CSV, entirely into memory just to hash it.
- `sha256_hash.update(chunk)` adds each chunk to the hash calculation.
- `hexdigest()` returns the final hash as a 64-character hexadecimal string.

The script applies this function to the five raw files: `credits.csv`, `keywords.csv`, `links.csv`, `movies_metadata.csv`, and `ratings.csv`. It uses `RAW_DATA_DIR` from `config/paths.py`, so it does not depend on a hardcoded relative path.

## 3. Saving fingerprints in JSON

The script stores the fingerprints in:

```text
data/processed/raw_data_fingerprints.json
```

The JSON file maps each raw filename to its SHA-256 hash:

```json
{
    "credits.csv": "<64-character SHA-256 hash>",
    "keywords.csv": "<64-character SHA-256 hash>",
    "links.csv": "<64-character SHA-256 hash>",
    "movies_metadata.csv": "<64-character SHA-256 hash>",
    "ratings.csv": "<64-character SHA-256 hash>"
}
```

The actual file contains the hashes calculated from the current raw CSV files.

The script uses Python's built-in `json` library:

- `json.dump(..., indent=4)` writes the fingerprint dictionary to a readable JSON file.
- `json.load(...)` reads the saved fingerprints back into Python.

The first run creates the manifest if it does not exist. Later runs compare the newly calculated hashes with the saved values. If a hash differs or a filename is missing from the manifest, the script reports a change and raises an error. It does not silently replace the saved baseline.

## 4. Testing and verification

The check script is:

```text
tests/check_fingerprints.py
```

It calls both functions:

```python
from src.scripts.stage2_fingerprint_data import (
    fingerprint_raw_data,
    save_or_verify_fingerprints,
)

fingerprints = fingerprint_raw_data()
save_or_verify_fingerprints(fingerprints)
```

Run it from the project root in PowerShell:

```powershell
python -m tests.check_fingerprints
```

We ran this command twice. Both runs printed the five hashes and:

```text
All raw data fingerprints verified successfully!

Fingerprinting and verification completed successfully!

Total files fingerprinted: 5
```

This confirmed that:

1. The five raw CSV files could be read and fingerprinted.
2. Their hashes matched the values stored in the JSON manifest.
3. Re-running the check produced the same results, so the raw files had not changed since the manifest was created.

This is a repeatability and integrity check against our saved baseline. It does not independently authenticate the original Kaggle download.

## 5. Why keep the manifest?

The JSON manifest is small metadata about the source files, not a copy of the datasets. It is useful to keep under version control so the project has a record of the exact raw-file contents used.

The original CSV files remain separate in `data/raw_data/` and are not committed to Git. The fingerprint manifest is stored in `data/processed/` and is intended to be committed.

## 6. Result

**Raw data fingerprinting is complete.** The project can now calculate SHA-256 hashes for its five source CSV files, save the initial hashes in a JSON manifest, and verify future runs against that saved baseline.

The raw files have not been modified by this process. Fingerprinting only reads them.
