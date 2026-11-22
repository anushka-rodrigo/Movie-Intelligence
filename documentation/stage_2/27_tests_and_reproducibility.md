# Stage 2 — Tests and Reproducibility (Steps 18 and 19)

## 1. Purpose

Two things must be proven before Stage 2 can be called finished:

1. **Each cleaning rule works** on its own, on small examples where the right answer is known.
2. **The pipeline is reproducible:** running it twice gives identical results, and the raw data is never changed.

The scripts are:

```text
tests/test_cleaning.py
tests/check_reproducibility.py
```

## 2. Unit tests with pytest

The earlier `check_*.py` scripts run on the real data and need minutes. The pytest tests run on tiny fake tables, so each rule is tested in isolation, in a fraction of a second. Run them with:

```powershell
python -m pytest tests -q
```

### Making the functions testable

Some functions had the real expected counts written in (3 broken records, 30 duplicate movies, 219 links without a TMDB id), which would make them reject any small example. Each of these functions now takes its expected count as an optional argument:

| Function | New argument |
|---|---|
| `repair_split_records` | `expected_records` |
| `remove_duplicate_movies` | `expected_removed` |
| `clean_links` | `expected_missing_tmdb`, `expected_extra_copies` |

Real runs use the defaults and behave exactly as before. The test supplies its own numbers.

### The 16 tests

| Area | Tests | What is proven |
|---|---:|---|
| Parsing (C26) | 2 | Text becomes real lists, missing stays missing, and a result of the wrong type is rejected |
| Duplicates (C03 to C07) | 3 | The first copy is kept, an unexpected count stops the run, and the higher `vote_count` wins even when `popularity` points the other way |
| Split records (C01) | 1 | The two halves of a broken movie are glued back together with their line break |
| Data types (C27) | 2 | Every column is converted, and an unparseable value stops the run |
| Placeholders (C18 to C22) | 1 | Zeros become missing, and borderline values are flagged without being changed |
| Links (C10, C12, C15) | 1 | The IMDb id is rebuilt, shared ids are flagged, and rows without a TMDB id are dropped |
| Ratings (C27) | 1 | The timestamp becomes a real date |
| List tables | 3 | A list column splits into a lookup and a link table, an id with two names stops the run, and the Latin-alphabet name wins with gender `0` becoming missing |
| The bridge and the join (C09 to C14) | 2 | Unsafe rows are quarantined with a reason, the loss is counted, and a bridge with a repeated key stops the join |

### Result

```text
16 passed
```

## 3. Reproducibility

`tests/check_reproducibility.py` runs the full pipeline twice, as two separate processes, and compares the manifest of each run. The manifest holds the SHA-256 hash of every output file, so identical hashes mean identical bytes.

```powershell
python -m tests.check_reproducibility
```

### Result

All 17 files were identical across the two runs:

```text
RESULT: REPRODUCIBLE
```

Three things make this work: a fixed row order (tables are sorted by key), fixed line endings, and no timestamps or random values anywhere in the outputs.

## 4. Raw data stays untouched

Every pipeline run verifies the SHA-256 fingerprints of the five raw files twice: before extraction and again after the last table is saved. If a run completes, the raw files had the same fingerprints at both ends. The raw folder is never written to by any script.

## 5. A limitation

Identical hashes prove that two runs on the same machine and software versions give the same bytes. They do not prove the bytes would be identical under a different version of pandas or Python.

## 6. Result

**The cleaning rules are tested, and the pipeline is reproducible.** Re-running the ETL always rebuilds the same 17 files from the same raw data.
