# Stage 2 — Cleaning the Links Table (C10, C12, C15, C27)

## 1. Purpose

`links` is the **bridge** between the MovieLens ids used by `ratings` and the TMDB ids used by every other table:

```text
ratings.movieId -> links.movieId -> links.tmdbId -> movies_metadata.id
```

A mistake in the bridge silently corrupts every rating join later. This step gives it the right types, a readable IMDb id, a flag on the dangerous rows, and removes the rows that lead nowhere.

The script is:

```text
src/scripts/stage2_modules/stage2_clean_links.py
```

## 2. The rules

| Decision | What is done |
|---|---|
| **C27** | `tmdbId` becomes `Int64`. It is a decimal only because it has missing values. |
| **C15** | `imdbId` is a plain number (`114709`). It is rebuilt as `tt` plus 7 digits (`tt0114709`), the form metadata uses. |
| **C12** | 30 extra copies of `tmdbId` exist. Every row that shares a `tmdbId` is flagged, so it can be excluded from joins later. |
| **C10** | The 219 rows with no `tmdbId` cannot reach metadata. They are dropped from the cleaned bridge and stay in the raw file. |

Result: 45,843 rows become **45,624**.

## 3. Why the order matters

Pandas treats missing values as copies of each other, so 219 missing values look like 218 "duplicates". This is the puzzle recorded in the Stage 1 summary (section 4.3). The shared-id check therefore removes the missing values first. The flag is computed before the rows without a `tmdbId` are dropped.

## 4. The code

```python
EXPECTED_ROWS_WITHOUT_TMDB_ID = 219    # C10
EXPECTED_EXTRA_TMDB_COPIES = 30        # C12 (the first copy is not counted)


def clean_links(links):
    rows_before = len(links)
    links = links.copy()

    if links["movieId"].duplicated().any():
        raise ValueError("links: movieId is not unique.")

    # C27
    links["tmdbId"] = links["tmdbId"].astype("Int64")

    # C15: 114709 -> tt0114709
    links["imdbId"] = "tt" + links["imdbId"].astype(str).str.zfill(7)
    if not links["imdbId"].str.fullmatch(r"tt\d{7}").all():
        raise ValueError("links: some imdbId values are not 'tt' plus 7 digits.")
    if links["imdbId"].duplicated().any():
        raise ValueError("links: imdbId is not unique.")

    # C12: flag every row whose tmdbId is shared with another row
    extra_copies = links["tmdbId"].dropna().duplicated().sum()
    if extra_copies != EXPECTED_EXTRA_TMDB_COPIES:
        raise ValueError(
            f"links: expected {EXPECTED_EXTRA_TMDB_COPIES} extra tmdbId copies, found {extra_copies}"
        )
    links["shared_tmdb_id"] = links["tmdbId"].notna() & links["tmdbId"].duplicated(keep=False)

    # C10: drop rows with no tmdbId
    missing_tmdb = links["tmdbId"].isna()
    if missing_tmdb.sum() != EXPECTED_ROWS_WITHOUT_TMDB_ID:
        raise ValueError("links: unexpected number of rows without tmdbId.")
    links = links[~missing_tmdb].reset_index(drop=True)

    return links
```

How it works:

- `"tt" + ...astype(str).str.zfill(7)` turns the number into text, pads it with zeros on the left to 7 characters, and adds `tt`.
- `str.fullmatch(r"tt\d{7}")` checks that every value is exactly `tt` followed by 7 digits.
- `dropna().duplicated()` counts the real repeats (30), ignoring the missing values.
- `duplicated(keep=False)` marks every row that shares an id, including the first copy, because a join can go wrong on either one.
- The flag is a new column, not a deletion (Ground Rule 3: flag instead of overwrite). The exclusion itself happens in the join step.
- The `raise` checks protect the figures from the cleaning decisions: unique keys, 30 extra copies, 219 missing.

## 5. Left for the join step

Two links decisions need the cleaned metadata table, so they are not part of this step:

- **C11:** the 161 `tmdbId` values that are not in metadata are excluded when ratings are linked to metadata.
- **C17:** the `imdb_conflict` flag, which compares `links.imdbId` with `movies_metadata.imdb_id`.

## 6. Testing and verification

The check script is `tests/check_links.py`.

| Check | Expected | Result |
|---|---|---|
| Rows | 45,843 to 45,624 | 45,843 to 45,624 |
| Rows sharing a `tmdbId` | about 59 | 59 rows, 29 distinct `tmdbId` values (28 pairs and one triple) |
| Data types | `tmdbId` Int64, flag bool | Correct |
| First row | movieId 1, `tt0114709`, tmdbId 862 | Correct (Toy Story) |
| `movieId` unique | yes | yes |

The flagged sample shows the danger C12 describes: two different `movieId` values pointing at one `tmdbId`, for example 6003 and 144606 both claiming 4912, and 174533 and 4241 both claiming 10991.

## 7. Result

**The bridge table is cleaned and its risky rows are flagged.** It has 45,624 rows, unique keys, a readable IMDb id, and a `shared_tmdb_id` flag on the 59 rows that must be excluded from joins until they are resolved.
