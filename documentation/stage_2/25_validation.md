# Stage 2 — Validation (Step 16)

## 1. Purpose

Cleaning functions check their own work, but a pipeline also needs one final gate that looks at the finished tables as a whole. This step adds automatic alarms that run after the tables are built and before anything is saved. If a check fails, nothing is written.

The scripts are:

```text
src/scripts/stage2_modules/stage2_table_specs.py
src/scripts/stage2_modules/stage2_validate.py
```

## 2. One specification for every table

`stage2_table_specs.py` describes each of the 17 final tables in one place: its key, its expected row count, and whether it is sorted before saving. The validation and the load step both read it, so they can never disagree about what a table should look like.

The expected row counts are the numbers verified one by one while the tables were built.

## 3. How the checker works

```python
class Checker:
    def expect(self, condition, message):
        if bool(condition):
            self.passed += 1
        else:
            self.failures.append(message)
```

The checker does not stop at the first problem. It collects every failure and reports them all at once, so one run shows everything that is wrong. At the end, any failure raises an error and the pipeline stops before the load step.

## 4. What is checked

| Group | Checks | What it proves |
|---|---:|---|
| Table names | 1 | Exactly the 17 expected tables exist |
| Row counts | 17 | Every table has its verified size |
| No missing key values | 17 | Every key column is complete |
| Unique keys | 18 | Every key is unique, plus two extra checks for ratings |
| Foreign keys | 15 | No link row points at a movie, genre, company, country, language, keyword or person that does not exist |
| Value checks | 12 | Ranges and formats (see below) |
| Movie 401840 (C13) | 4 | It exists in `movies` and has no cast, crew or keywords |
| Join coverage | 5 | The ratings join matches the Stage 1 figures |
| **Total** | **89** | |

### The value checks

- `vote_average` is between 0.5 and 10, and no runtime is zero or negative.
- No budget or revenue placeholder (below 1,000) remains.
- `release_date` is between 1874 and 2020.
- Cast and crew `gender` is only 1 or 2 (or missing), and the cast billing `order` is never negative.
- Every `imdb_id` in the bridge is `tt` plus 7 digits.
- Exactly 65 IMDb conflicts are flagged.
- The excluded bridge rows have exactly the two expected reasons (161 and 59).
- Every rating is on the 0.5 to 5.0 scale.

### Proving the ratings key without a slow check

The key of `ratings` is the pair (`user_id`, `movielens_id`). Checking 26 million pairs with a normal duplicate search is slow and memory-heavy. Instead, each pair is turned into one number and the numbers are sorted:

```python
keys = ratings["user_id"].to_numpy(dtype="int64") * 1_000_000 + ratings["movielens_id"].to_numpy(dtype="int64")
keys.sort()
no_repeats = not (keys[1:] == keys[:-1]).any()
```

This works because every `movielens_id` is below 1,000,000, which is checked first. Any repeated pair would sit next to its twin after sorting.

## 5. Results

```text
Validation finished: 89 checks passed, 0 failed.
```

The whole validation takes about 5 seconds.

## 6. A limitation

The expected counts are written into the specification as fixed numbers. That is deliberate: they are the verified results of the Stage 1 investigation, so any surprise stops the pipeline. If the source data is ever replaced with a different version, these numbers must be updated on purpose.

## 7. Result

**All 17 tables pass 89 automatic checks.** The pipeline cannot save a table that has the wrong size, a repeated key, a missing key, a broken link to another table, or a value outside its valid range.
