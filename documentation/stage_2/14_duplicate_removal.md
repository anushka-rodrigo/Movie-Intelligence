# Stage 2 — Removing Duplicate Movies (C06 and C07)

## 1. Purpose

Some movies appear more than once in `movies_metadata`. Left in, they would be double-counted in every later analysis. This step keeps exactly one copy of each movie.

Function: `remove_duplicate_movies()` in `stage2_clean_metadata.py`.

## 2. What was wrong

After the repair, 29 movie ids appear more than once:

| Group | Ids | What differs between copies | Decision |
|---|---:|---|---|
| C06 | 16 | Nothing, the copies are identical | Keep one |
| C07 | 13 | `popularity` always differs, `vote_count` differs for ids 10991 and 15028 | Keep the copy with the higher `vote_count` |

Removing the extra copies should take the table from 45,463 to **45,433** rows (30 copies removed).

## 3. The rule

**Keep the copy with the highest `vote_count`. On a tie, keep the first copy in the file.**

- `vote_count` can only grow over time, so a higher count means a later snapshot of the same movie.
- `popularity` changes constantly, so it can never tell us which copy is newer. It is never used to choose.
- Identical copies always tie, so the tie-break automatically covers C06. One rule handles both groups.

## 4. The code

```python
EXPECTED_DUPLICATE_COPIES = 30


def remove_duplicate_movies(meta):
    rows_before = len(meta)
    meta = meta.copy()

    meta["_id"] = pd.to_numeric(meta["id"])
    meta["_votes"] = pd.to_numeric(meta["vote_count"])
    meta["_position"] = range(len(meta))

    repeated = meta[meta["_id"].duplicated(keep=False)]
    logger.info("Movie ids that appear more than once: %s", repeated["_id"].nunique())

    content_columns = [c for c in meta.columns if not c.startswith("_")]
    distinct_copies = repeated.drop_duplicates(subset=content_columns)
    conflict_ids = distinct_copies.loc[
        distinct_copies["_id"].duplicated(keep=False), "_id"
    ].unique()
    logger.info("Ids whose copies differ: %s", len(conflict_ids))

    votes_per_id = repeated.groupby("_id")["_votes"].nunique()
    vote_conflict_ids = votes_per_id[votes_per_id > 1].index.tolist()
    logger.info("Ids whose vote_count differs: %s", vote_conflict_ids)

    ordered = meta.sort_values(
        ["_id", "_votes", "_position"],
        ascending=[True, False, True],
        na_position="last",
    )
    kept = ordered.drop_duplicates(subset="_id", keep="first")

    kept = (
        kept.sort_values("_position")
        .drop(columns=["_id", "_votes", "_position"])
        .reset_index(drop=True)
    )

    removed = rows_before - len(kept)
    if removed != EXPECTED_DUPLICATE_COPIES:
        raise ValueError(f"Expected to remove {EXPECTED_DUPLICATE_COPIES}, removed {removed}")
    if pd.to_numeric(kept["id"]).duplicated().any():
        raise ValueError("Duplicate ids remain after de-duplication.")

    return kept
```

How it works:

- Helper columns starting with `_` are a temporary workspace. They hold the id and `vote_count` as real numbers (so `9` does not sort after `10`) and the original row position. They are removed at the end.
- `duplicated(keep=False)` marks every copy of a repeated id, including the first.
- `drop_duplicates(subset=content_columns)` removes only exact copies, so any id that still has two rows has copies that really differ.
- The three-part sort is the rule in code: id, then `_votes` high to low, then `_position` early to late. Taking the first row per id keeps the right copy.
- Sorting by `_position` at the end restores the original file order.
- The final checks stop the pipeline if the number removed is not 30 or any id is still repeated.

## 4. Testing and verification

Check script: `tests/check_duplicates.py`.

```text
Movie ids that appear more than once: 29
Ids whose copies differ: 13
Ids whose vote_count differs: [10991, 15028]
remove_duplicate_movies: 45463 rows -> 45433 rows.

Ids unique: True
```

The two ids with different vote counts show the rule working:

| Movie | Copy kept | Copy dropped |
|---|---|---|
| Pokémon: Spell of the Unknown (10991) | vote_count 144, popularity 6.48 | vote_count 143, popularity 10.26 |
| Clockstoppers (15028) | vote_count 90, popularity 4.92 | vote_count 89, popularity 5.37 |

In both cases the kept copy has the higher `vote_count` but the lower `popularity`. Choosing by popularity would have kept the older snapshot.

## 5. Result

**Duplicate movies are removed.** `movies_metadata` has 45,433 rows with unique ids, matching the expected count from the Stage 1 cleaning decisions.
