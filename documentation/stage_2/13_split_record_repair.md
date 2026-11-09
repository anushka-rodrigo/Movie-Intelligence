# Stage 2 — Repairing the Split Metadata Records (C01)

## 1. Purpose

Three movies in `movies_metadata.csv` are broken across two lines each, so pandas reads 6 rows instead of 3. This step glues each pair back into one row.

The script is:

```text
src/scripts/stage2_modules/stage2_clean_metadata.py
```

Function: `repair_split_records()`.

## 2. What was wrong

From the Stage 1 investigation:

- Each of the 3 movies has an `overview` that contains a line break and is not wrapped in quotes.
- The CSV reader treats the line break as the end of the row. The movie is split into a **stub row** (the first 10 columns, ending with the first half of the overview) and a **tail row** (the second half of the overview, then the remaining 14 values).
- The tail row's values sit **9 columns too far left**. A date ends up in `id`, text ends up in `adult`, and the `title` is missing from the stub.

The three pairs are at rows 19729/19730, 29502/29503 and 35586/35587.

## 3. The repair rule (decision C01)

For each tail row:

1. Find the tail rows: the rows whose `id` is not a number.
2. The stub is the row just before the tail.
3. New `overview` = stub overview + a line break + the tail's first value.
4. Copy the tail's other 14 values into the stub's columns 10 to 23 (a shift of 9).
5. Drop the tail rows.

Dropping only the bad rows would leave 3 incomplete stubs, so the repair keeps all 3 real movies.

## 4. The code

```python
SHIFT = 9
EXPECTED_SPLIT_RECORDS = 3


def repair_split_records(meta):
    """C01: glue the 3 split metadata records back into single rows."""
    rows_before = len(meta)

    meta = meta.copy().astype("object")
    columns = list(meta.columns)

    id_as_number = pd.to_numeric(meta["id"], errors="coerce")
    tail_labels = list(meta.index[id_as_number.isna()])

    if len(tail_labels) != EXPECTED_SPLIT_RECORDS:
        raise ValueError(
            f"Expected {EXPECTED_SPLIT_RECORDS} split records, "
            f"found {len(tail_labels)}"
        )

    for tail_label in tail_labels:
        stub_label = tail_label - 1

        if pd.notna(meta.at[stub_label, "title"]):
            raise ValueError(f"Row {stub_label} does not look like a stub")

        meta.at[stub_label, "overview"] = (
            meta.at[stub_label, "overview"]
            + "\n"
            + meta.at[tail_label, columns[0]]
        )

        for j in range(1, 15):
            meta.at[stub_label, columns[j + SHIFT]] = meta.at[tail_label, columns[j]]

        logger.info("Repaired split record at rows %s and %s.", stub_label, tail_label)

    meta = meta.drop(index=tail_labels).reset_index(drop=True)

    if len(meta) != rows_before - EXPECTED_SPLIT_RECORDS:
        raise ValueError("Row count after repair is wrong.")
    if pd.to_numeric(meta["id"], errors="coerce").isna().any():
        raise ValueError("Some ids are still not numeric after repair.")

    return meta
```

How it works:

- `.copy()` means the extracted table is never changed.
- `.astype("object")` lets every column hold text and numbers temporarily, because the tail rows put text into columns that are normally numeric. Step 7 sets the proper types afterwards.
- `.at[row, column]` reads or writes a single cell.
- `columns[j + SHIFT]` is the Stage 1 finding in code: tail column `j` belongs in column `j + 9`.
- The `raise` statements are validation. If the file ever changes and there aren't exactly 3 broken records, the pipeline stops instead of guessing.

## 5. Testing and verification

The check script is `tests/check_repair.py`. Run from the project root:

```powershell
python -m tests.check_repair
```

Result:

```text
Rows before: 45466 | after: 45463
title:        Midnight Man
release_date: 1997-08-20
runtime:      104.0
vote_count:   1
overview ends: 'trouble between China and Great Britain.\n - Written by Ørnås'

Missing titles left: 0
```

This matches the values predicted by the Stage 1 notebook, and the overview keeps its original line break.

## 6. Result

**The 3 split records are repaired.** The metadata table has 45,463 rows, every id is numeric, and no titles are missing.
