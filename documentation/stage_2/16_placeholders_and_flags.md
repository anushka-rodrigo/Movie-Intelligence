# Stage 2 — Placeholders and Review Flags (C16, C18 to C22)

## 1. Purpose

The dataset uses fake values to mean "we don't know": a budget of `0`, a runtime of `0`, a `vote_average` of `0.0` on a movie nobody voted for. Left alone, they make every average, ROI figure and chart quietly wrong.

This step turns those placeholders into proper "missing" values and adds flag columns for borderline cases.

Function: `clean_placeholders()` in `stage2_clean_metadata.py`.

## 2. The rules

| Column | Becomes missing | Flag column (value kept) | Decision |
|---|---|---|---|
| `budget` | zeros and values below 1,000 | `budget_review`: 1,000 up to 10,000 | C18 |
| `revenue` | zeros and values below 1,000 | `revenue_review`: 1,000 up to 10,000 | C19 |
| `runtime` | zeros | `long_runtime`: above 300 minutes | C21 |
| `vote_average` | all zeros | `vote_average_zero_with_votes`: 0 but has votes | C22 |
| `imdb_id` | the text `'0'` | | C16 |

Not changed: `vote_count` zeros stay, because "nobody voted" is a real fact (C23). Long runtimes are real miniseries and documentaries, so they are flagged, never capped or dropped (C21).

## 3. Flag first, then blank

For `vote_average`, the suspicious movies are the ones with an average of 0 **and** real votes. If the zeros were blanked first, the evidence of which ones were suspicious would be lost. So the function computes every flag before it changes any value.

Flags are separate columns, not edits. The original value stays in the table, so a later analysis can decide whether to include borderline rows (Ground Rule 3: flag instead of overwrite).

## 4. The code

```python
LOW_VALUE_THRESHOLD = 1_000
REVIEW_UPPER_LIMIT = 10_000
LONG_RUNTIME_MINUTES = 300


def clean_placeholders(meta):
    meta = meta.copy()

    report_columns = ["budget", "revenue", "runtime", "vote_average", "imdb_id"]
    missing_before = meta[report_columns].isna().sum()

    # Flags first
    for column in ["budget", "revenue"]:
        meta[f"{column}_review"] = meta[column].between(
            LOW_VALUE_THRESHOLD, REVIEW_UPPER_LIMIT, inclusive="left"
        )

    meta["long_runtime"] = meta["runtime"] > LONG_RUNTIME_MINUTES

    meta["vote_average_zero_with_votes"] = (
        ((meta["vote_average"] == 0) & (meta["vote_count"] > 0))
        .fillna(False)
        .astype(bool)
    )

    # Then turn placeholders into missing
    for column in ["budget", "revenue"]:
        meta[column] = meta[column].mask(meta[column] < LOW_VALUE_THRESHOLD)

    meta["runtime"] = meta["runtime"].mask(meta["runtime"] == 0)
    meta["vote_average"] = meta["vote_average"].mask(meta["vote_average"] == 0)
    meta["imdb_id"] = meta["imdb_id"].mask(meta["imdb_id"] == "0")

    # Checks: no placeholders may remain
    for column in ["budget", "revenue"]:
        if (meta[column] < LOW_VALUE_THRESHOLD).any():
            raise ValueError(f"{column}: placeholder values remain.")
    if (meta["runtime"] == 0).any() or (meta["vote_average"] == 0).any():
        raise ValueError("Zero runtime or vote_average values remain.")
    if (meta["imdb_id"] == "0").any():
        raise ValueError("imdb_id '0' values remain.")

    # Report what changed
    missing_after = meta[report_columns].isna().sum()
    for column in report_columns:
        logger.info(
            "clean_placeholders: %s missing %s -> %s",
            column, missing_before[column], missing_after[column],
        )

    return meta
```

How it works:

- `series.mask(condition)` returns a copy where every row meeting the condition becomes missing. One rule (`budget < 1000`) covers both zeros and tiny values.
- `between(..., inclusive="left")` is true from 1,000 up to but not including 10,000.
- `vote_count` can contain missing values, so the comparison can come out as "unknown". `.fillna(False).astype(bool)` turns that into a clean true/false flag.
- The checks at the end stop the pipeline if any placeholder survived.

## 5. Testing and verification

Check script: `tests/check_placeholders.py`. Stage 1 counted on the raw file, which still held the 30 duplicate copies, so small drops are expected.

| Check | Stage 1 | Now | Verdict |
|---|---:|---:|---|
| `revenue_review` flags | 83 | 83 | Exact |
| `long_runtime` flags | 108 | 108 | Exact |
| `vote_average_zero_with_votes` | 99 | 99 | Exact |
| `budget_review` flags | 55 | 54 | One duplicate copy removed |
| `vote_average` missing | 2,998 | 2,995 | 3 duplicates with zero votes removed |
| `vote_count` zeros kept | 2,899 | 2,896 | The same 3 duplicates |
| Budget and revenue both present | 5,312 | 5,307 | Duplicate copies removed |

Other results:

- `runtime` missing went from 257 to 1,815. The difference is exactly **1,558**, Stage 1's zero-runtime count.
- Smallest remaining values: budget 1,000, revenue 1,081, runtime 1, `vote_average` 0.5.

## 6. The `imdb_id` `'0'` finding (C16)

The rule changed nothing: `imdb_id` stayed at 17 missing values. Checking the raw file showed exactly **3** `imdb_id` values that are not `tt` plus digits, all of them `'0'`.

That count equals the number of broken tail rows. In a tail row, the `imdb_id` slot holds the movie's `revenue`, which is `0` for all three (the Stage 1 notebook shows this). So those `'0'` values were never real placeholders. They were removed by the repair in C01, which is why C16 finds nothing to convert.

The rule stays in the code as a safeguard in case the data ever changes.

## 7. Result

**Placeholders are now "missing", and borderline values are flagged instead of changed.** The row count is still 45,433.

Two metadata items are deliberately left for later steps: C17 (the `imdb_conflict` flag, which needs the `links` table) and C28 (dropping `homepage` and `poster_path`, which belongs to the final table design).
