# Stage 2 — Cleaning the Ratings Table (C27)

## 1. Purpose

`ratings` is the smallest cleaning job and the biggest table: 26,024,289 rows. The only change needed is converting the timestamp from "seconds since 1970" into a real date. The other three columns were already clean in Stage 1, so this step proves it with checks.

The script is:

```text
src/scripts/stage2_modules/stage2_clean_ratings.py
```

## 2. The rules

| Decision | What is done |
|---|---|
| **C27** | `timestamp` is converted from Unix seconds to a real datetime. |
| **C02** | Compact types (`int32`, `float32`) were already applied during extraction, so the table fits in memory. |
| **C29** | Only the full `ratings` file is used. `ratings_small` is never combined with it, because its user ids are numbered separately. |
| **C09** | `movieId` is a MovieLens id. It must never be joined directly to `movies_metadata.id`. It only reaches metadata through `links`. |

The row count does not change.

## 3. Two design choices

- **No `.copy()`.** The other cleaning steps copy the table so the input is never modified. A copy of 26 million rows would double the memory. `assign()` instead builds a new table that replaces only the `timestamp` column and reuses the other three.
- **Expensive checks wait for the Validate phase.** Proving that every (`userId`, `movieId`) pair is unique means hashing 26 million rows. Stage 1 already showed there are no repeats, so the full re-check belongs in the validation phase, not in every cleaning run.

## 4. The code

```python
EXPECTED_RATING_VALUES = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0]
EARLIEST_ALLOWED = pd.Timestamp("1995-01-01")
LATEST_ALLOWED = pd.Timestamp("2017-12-31")


def clean_ratings(ratings):
    rows_before = len(ratings)

    ratings = ratings.assign(timestamp=pd.to_datetime(ratings["timestamp"], unit="s"))

    if len(ratings) != rows_before:
        raise ValueError("ratings: the row count changed.")
    if ratings.isna().any().any():
        raise ValueError("ratings: missing values found.")

    rating_values = sorted(ratings["rating"].unique().tolist())
    if rating_values != EXPECTED_RATING_VALUES:
        raise ValueError(f"ratings: unexpected rating values {rating_values}")

    first, last = ratings["timestamp"].min(), ratings["timestamp"].max()
    if first < EARLIEST_ALLOWED or last > LATEST_ALLOWED:
        raise ValueError(f"ratings: timestamps outside the expected range: {first} to {last}")

    logger.info("clean_ratings: %s rows, timestamps from %s to %s.", len(ratings), first, last)
    return ratings
```

How it works:

- `pd.to_datetime(..., unit="s")` tells pandas the numbers are seconds since 1 January 1970.
- `ratings.isna().any().any()` asks whether any column contains any missing value. The first `.any()` works per column, the second across columns.
- The rating scale must be exactly ten values in steps of 0.5. A stray value such as 0.0 or 5.5 stops the pipeline.
- The date bounds are wide on purpose (all of 1995 to 2017), so only a real surprise trips them. The exact first and last dates are logged.
- Everything here is a check, not a repair: the data was already clean, and the function proves that instead of assuming it.

## 5. Testing and verification

The check script is `tests/check_ratings.py`.

| Check | Expected | Result |
|---|---|---|
| Rows | 26,024,289 before and after | 26,024,289 before and after |
| Timestamp range | 1995-01-09 to 2017-08-04 | 1995-01-09 11:46:44 to 2017-08-04 06:57:50 |
| Rating values | exactly 10, from 0.5 to 5.0 | exactly 10, from 0.5 to 5.0 |
| Data types | `timestamp` becomes a datetime | `datetime64[s]` |
| Memory | about 416 MB to 520 MB | 416 MB to 520 MB |

The rating counts add up to exactly 26,024,289, so no rating is missing from the distribution. The most common rating is 4.0 (6,998,802 rows), followed by 3.0, and half-star ratings are the least common.

The memory change is the trade-off behind every type choice: the timestamp grew from 4 bytes to 8 bytes per row, about 100 MB across 26 million rows.

## 6. Result

**The ratings table is cleaned.** It has the same 26,024,289 rows, with a real datetime column, no missing values, and a verified rating scale.

**Phase C is complete.** All five tables are cleaned individually, in memory. The next phase connects them: it applies the exclusions for C11 and C12, adds the `imdb_conflict` flag (C17), and decides the final table shapes.
