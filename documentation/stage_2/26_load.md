# Stage 2 — Loading the Processed Data (Step 17)

## 1. Purpose

The load step saves the validated tables into `data/processed/`, separate from the raw data in `data/raw_data/`. It also records a manifest of what was written, which is what makes the "run it twice" check possible.

The script is:

```text
src/scripts/stage2_modules/stage2_load.py
```

## 2. The format decision: CSV

| | CSV | Parquet |
|---|---|---|
| New library needed | No | Yes (pyarrow) |
| Loads directly into PostgreSQL (Stage 3) | Yes | No |
| Readable by eye | Yes | No |
| Size of the ratings table | Large (hundreds of MB) | Much smaller |
| Predictable bytes for the reproducibility check | Yes | Less certain |

CSV was chosen. The final tables contain no lists, so nothing is lost by using plain text. The cost is a large `ratings.csv`. All files in `data/processed/` are ignored by git, except the raw-data fingerprints file.

## 3. How the files are written

```python
table.to_csv(temp_path, index=False, encoding="utf-8", lineterminator="\n")
os.replace(temp_path, final_path)
```

- **Fixed row order.** Every table except `ratings` is sorted by its key before saving, so the file is identical on every run. Ratings keep their file order, which is already fixed, and sorting 26 million rows would only waste time.
- **Temporary file first.** Each table is written to `name.csv.tmp` and then renamed. A crash in the middle of a write can never leave a half-written table that looks complete.
- **Fixed line endings.** `lineterminator="\n"` makes the bytes the same on any operating system.
- **Re-runnable.** Running the load again overwrites its own files and touches nothing else. The raw-data fingerprints file in the same folder is never deleted.

## 4. The manifest

After writing, the load step records every file's row count and SHA-256 hash in:

```text
data/processed/processed_data_manifest.json
```

```json
{
    "movies.csv": { "rows": 45433, "sha256": "<64-character hash>" }
}
```

The SHA-256 fingerprint is the same idea as the raw-data fingerprints (document 11), now applied to the outputs. Two files with the same hash are byte-for-byte identical.

## 5. The files

| File | Rows |
|---|---:|
| `movies.csv` | 45,433 |
| `genres.csv` / `movie_genres.csv` | 20 / 91,015 |
| `production_companies.csv` / `movie_production_companies.csv` | 23,693 / 70,476 |
| `production_countries.csv` / `movie_production_countries.csv` | 161 / 49,375 |
| `spoken_languages.csv` / `movie_spoken_languages.csv` | 133 / 53,269 |
| `keywords.csv` / `movie_keywords.csv` | 19,956 / 156,602 |
| `people.csv` | 353,343 |
| `movie_cast.csv` | 562,044 |
| `movie_crew.csv` | 463,836 |
| `movie_links.csv` | 45,404 |
| `movie_links_excluded.csv` | 220 |
| `ratings.csv` | 26,024,289 |

## 6. Results

Writing all 17 files takes about 33 seconds, of which about 30 seconds is the ratings file. The whole pipeline, from fingerprint check to the final fingerprint check, completes in 77 to 87 seconds.

## 7. Result

**The processed datasets exist, are written safely, and are described by a manifest.** The raw data and the processed data live in separate folders, and the pipeline never writes to the raw folder.
