# Stage 2 — Connecting the Tables (Step 15)

## 1. Purpose

Ratings use MovieLens ids and everything else uses TMDB ids, so a rating reaches a movie only through the bridge:

```text
ratings.movielens_id -> movie_links.movielens_id -> movie_links.movie_id -> movies.movie_id
```

A mistake in this chain attaches ratings to the wrong film without raising any error. This step makes the bridge safe and proves that the chain works.

The script is:

```text
src/scripts/stage2_modules/stage2_join_tables.py
```

## 2. The rules

| Decision | What is done |
|---|---|
| **C09** | Ratings join to movies only through the bridge, never by matching the two id columns directly. |
| **C10** | The 219 links without a `tmdbId` were already dropped in the links cleaning step. |
| **C11** | The 161 bridge rows whose TMDB id is not in `movies` are excluded. |
| **C12** | The 59 bridge rows that share a TMDB id with another row are excluded. |
| **C13** | Movie 401840 is missing from credits and keywords. It stays in `movies`, and the credit tables simply have no rows for it. |
| **C14** | Every join checks its row counts and its key. |
| **C17** | Bridge rows whose IMDb id disagrees with the one in metadata are flagged with `imdb_conflict`. |

## 3. Design: quarantine, do not delete

Rows that cannot be trusted are moved into their own table, `movie_links_excluded`, with an `exclusion_reason` column. The decisions say "exclude and flag until resolved", so the rows must stay findable.

After the split, `movie_links` is a **safe bridge**: each `movie_id` appears once and each `movielens_id` appears once. Joins in later stages cannot multiply or pool ratings.

## 4. The code

### Splitting the bridge

```python
in_metadata = movie_links["movie_id"].isin(movies["movie_id"])

reason = pd.Series(None, index=movie_links.index, dtype="object")
reason[~in_metadata] = "tmdb_id_not_in_metadata"                            # C11
reason[movie_links["shared_tmdb_id"] & reason.isna()] = "shared_tmdb_id"    # C12
```

A row never gets two reasons: C11 is applied first, and C12 only where no reason is set yet. Afterwards the function checks that no rows were lost or created, and that `movie_id` and `movielens_id` are unique in the safe bridge.

### Joining ratings to the bridge

```python
linked = ratings[["movielens_id"]].merge(
    bridge[["movielens_id", "movie_id"]],
    on="movielens_id",
    how="left",
    validate="many_to_one",
)
```

- `validate="many_to_one"` is C14 in one argument. It stops the join if the bridge has a repeated `movielens_id`, which is the situation where a join quietly multiplies rows.
- `how="left"` keeps every rating, so the loss is counted instead of hidden. An inner join would drop unreachable ratings silently.
- Only the `movielens_id` column is joined, because merging all four columns of 26 million rows would roughly triple the memory.
- The function also checks that the row count did not change.

### Flagging IMDb conflicts

The safe bridge is joined to `movies` on `movie_id` with `validate="one_to_one"`. A row is flagged when both IMDb ids exist and differ. A missing id is never a conflict.

## 5. Results

### The bridge

| Part | Rows |
|---|---:|
| `movie_links` before the split | 45,624 |
| Safe bridge | **45,404** |
| Excluded: `tmdb_id_not_in_metadata` | **161** |
| Excluded: `shared_tmdb_id` | **59** |

### Joining ratings

| Join | Rating rows reachable | Rating rows lost | Rated movies reachable |
|---|---:|---:|---:|
| Without C12 (the Stage 1 figure) | 25,981,582 | 42,707 | 44,741 of 45,115 |
| Through the safe bridge | 25,972,129 | 52,160 (0.20%) | **44,682** of 45,115 |

The first line reproduces the Stage 1 coverage numbers exactly, from scratch, with the new code. The second line shows the cost of excluding the 59 ambiguous bridge rows: 59 movies and 9,453 more ratings.

### IMDb conflicts

| Check | Result |
|---|---|
| Comparable movies (both ids present) | 45,387 |
| Conflicts flagged | 65 |
| Conflicts where the metadata id belongs to another movie in links | 2 |

The two genuine conflicts are a swap. Movie 22488 (MovieLens 76701) has `tt0486420` in links but `tt0785025` in metadata, and movie 20583 (MovieLens 162380) has the reverse. The other 63 are IMDb ids that `links` has never seen.

## 6. Open item

The swapped pair has not been reviewed by hand. The decision (C17) says to flag all 65 and review the two by hand, so both stay flagged until someone checks which IMDb id belongs to which title.

## 7. Result

**The chain from ratings to movies is safe and measured.** The bridge has unique keys, every excluded row is kept with its reason, and the coverage figures agree with the Stage 1 investigation.
