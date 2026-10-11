# Movie Dataset: Data Quality Report

**Project:** Movie Intelligence
**Stage:** 1, Understand the Raw Data (investigation done, deliverables in progress)
**Source:** The Movies Dataset (Kaggle, rounakbanik)
**Last updated:** 2026-10-07

> **Where the numbers come from.** Every figure below comes from the pandas investigation notebook (`stage1_data_investigation.ipynb`). Items I have not yet measured are marked **TO VERIFY** and listed in section 10. Nothing marked as a finding is a guess.

---

## 1. How to read this report

| Term | Meaning |
|---|---|
| **Missing (NaN)** | Cells pandas recognises as empty. Counted with `isna()`. |
| **Hidden missing** | Cells that *look* filled but carry no real information, such as `'[]'` (empty list) or `0` in `budget`. Pandas does not count these as missing. |
| **Unique** | Distinct non-missing values (`nunique()`, which ignores NaN). |
| **Key** | The column (or columns) that should identify exactly one row. |
| **Extra copies** | Rows beyond the first for each key (`rows - unique keys`). |
| **Repeated ids** | Number of *distinct* ids that appear more than once. |
| **Copies identical / differ** | Of the repeated ids, how many have every column equal in all copies, versus at least one column different. |

**Why the old "Duplicates" column was removed.** Per-column duplicate counts only say that values repeat, which is normal for columns like `rating`. Worse, `duplicated()` counts missing values as repeats while `nunique()` ignores them, so the two numbers never reconcile. Duplicates are now reported only at **row level** and **key level** (section 4).

---

## 2. Headline findings

1. **There are two different movie-id systems.** TMDB ids (`movies_metadata.id`, `credits.id`, `keywords.id`, `links.tmdbId`) and MovieLens ids (`ratings.movieId`, `links.movieId`). `links` is the only table that holds both, so it is the bridge.
2. **Joining `ratings` directly to `movies_metadata` is wrong.** 37,550 of 45,115 rated movies (83.2%) match nothing, and the 7,565 that do match are coincidences between two unrelated numberings. No error is raised.
3. **`movies_metadata` has 3 corrupted records.** Each is split across two physical rows (6 rows in total), with the second row's values shifted 9 columns to the left. This is why `id`, `adult`, `budget`, and `popularity` have the wrong dtype. **Cause (confirmed in the raw file):** an `overview` that contains a line break and is not wrapped in quotes, so the parser ends the record at the break.
4. **Duplicate ids exist in `credits` (43 ids), `keywords` (985 ids), and `movies_metadata` (29 ids).** Keywords duplicates are all exact copies. Credits has 7 and metadata has 13 ids whose copies **disagree**.
5. **`links` has 30 repeated `tmdbId` values and 219 missing ones.** These can silently merge or multiply rows during a join.
6. **Pandas' missing counts understate the real gaps.** `budget` is unknown for 80.44% of movies and `revenue` for 83.69%. 31.87% of keyword rows are empty lists.
7. **`imdb_id` has a different format in each table** (`tt0114709` vs `114709`). A join on the raw columns matches nothing.
8. **The `_small` files are samples of the full files, with renumbered users.** `links_small` agrees with `links` on all 9,115 shared ids, and 99.67% of the distinct (`movieId`, `rating`, `timestamp`) combinations in `ratings_small` appear in `ratings`. The earlier 0-match result was an artifact of `userId` being numbered differently.
9. **`homepage` is stale** and not trustworthy. The dataset is about 9 years old.
10. **Excel row counts were unreliable.** Excel's 1,048,576 for `ratings` is its row limit. The real count is 26,024,289.
11. **The list and dict columns are Python-style text, not JSON.** Every non-empty cell parses with `ast.literal_eval`; only the empty `'[]'` cells are also valid JSON.
12. **TMDB is a reliable backbone key.** The TMDB path and the IMDb path agree for 45,322 of 45,387 comparable movies (99.86%).
13. **99.17% of rated movies (44,741 of 45,115) can reach metadata** through the `links` bridge, covering 99.84% of rating rows.

---

## 3. Dataset overview

| File | Rows | Columns | Key | Id system | Role |
|---|---:|---:|---|---|---|
| `movies_metadata.csv` | 45,466 | 24 | `id` | TMDB | Main movie table |
| `credits.csv` | 45,476 | 3 | `id` | TMDB | Cast and crew per movie |
| `keywords.csv` | 46,419 | 2 | `id` | TMDB | Keywords per movie |
| `links.csv` | 45,843 | 3 | `movieId` | Both (bridge) | Translates MovieLens id to TMDB and IMDb ids |
| `links_small.csv` | 9,125 | 3 | `movieId` | Both (bridge) | Small version of `links` |
| `ratings.csv` | 26,024,289 | 4 | (`userId`, `movieId`) | MovieLens | User ratings |
| `ratings_small.csv` | 100,004 | 4 | (`userId`, `movieId`) | MovieLens | Small version of `ratings` |

**Row counts versus Excel:** four of the five Excel counts were exactly 1 higher than pandas because Excel counts the header row. Two are unresolved (see section 10): `credits` (Excel 45,505 vs pandas 45,476) and `ratings` (Excel hit its limit).

---

## 4. Duplicates and keys

### 4.1 Fully duplicated rows

| Table | Rows | Fully duplicated rows |
|---|---:|---:|
| credits | 45,476 | 37 |
| keywords | 46,419 | 987 |
| movies_metadata | 45,466 | 17 |
| links | 45,843 | 0 |
| links_small | 9,125 | 0 |
| ratings | 26,024,289 | 0 |
| ratings_small | 100,004 | 0 |

### 4.2 Key tests

| Table | Key tested | Null keys | Rows sharing a key | Extra copies | Repeated ids | Copies identical | Copies differ |
|---|---|---:|---:|---:|---:|---:|---:|
| credits | `id` | 0 | 87 | 44 | 43 | 36 | **7** |
| keywords | `id` | 0 | 1,972 | 987 | 985 | 985 | 0 |
| movies_metadata | `id` | 0 | 59 | 30 | 29 | 16 | **13** |
| links | `movieId` | 0 | 0 | 0 | 0 | n/a | n/a |
| links | `tmdbId` | 219 | 278 | 248 | see 4.3 | n/a | n/a |
| ratings | (`userId`, `movieId`) | 0 | 0 | 0 | 0 | n/a | n/a |
| ratings_small | (`userId`, `movieId`) | 0 | 0 | 0 | 0 | n/a | n/a |

**Identity that explains the gap:** `extra copies - fully duplicated rows = copies differ`.
Credits: 44 − 37 = 7. Metadata: 30 − 17 = 13. Keywords: 987 − 987 = 0.

**What to do:**
- *Identical copies* (credits 36, keywords 985, metadata 16): harmless. Keep one, drop the rest.
- *Conflicting copies* (credits 7, metadata 13): need a decision about which copy wins (measured differences below).
- Some ids appear three times (confirmed): id **141971** in credits (44 extra copies across 43 ids), and ids **141971** and **159849** in keywords (987 extra copies across 985 ids).

**Which columns differ in the conflicting copies (measured):**

| Table | Conflicting ids | Columns that differ |
|---|---:|---|
| credits | 7 (4912, 69234, 99080, 110428, 132641, 159849, 298721) | `crew` only (the string lengths are identical, so the difference is in content, not size) |
| movies_metadata | 13 | `popularity` in all 13; `vote_count` also in 2 (ids 10991 and 15028, e.g. 143 vs 144) |

Four ids (4912, 69234, 110428, 132641) conflict in **both** tables. Fields that change over time (`popularity`, `vote_count`) suggest the copies are **snapshots taken at different times**. Since `vote_count` only grows, the copy with the higher count is the newer one. When only `popularity` differs there is no evidence of which is newer, so a deterministic rule must be chosen and documented.

### 4.3 The missing-value puzzle (why "Duplicates" never matched)

| Column | Rows | NaN | `nunique()` | `duplicated()` | `duplicated()` ignoring NaN |
|---|---:|---:|---:|---:|---:|
| `movies_metadata.imdb_id` | 45,466 | 17 | 45,417 | 48 | **32** |
| `links.tmdbId` | 45,843 | 219 | 45,594 | 248 | **30** |

`duplicated()` treats the NaNs as repeats of each other (17 NaN gives 16, and 219 NaN gives 218). `nunique()` ignores them. The real repeats are 32 and 30.

---

## 5. Table profiles

Column notation: **Dtype (raw)** is what pandas loaded. **Target** is what it should become. **Verdict** is a proposal (Trust, Transform, Investigate, Ignore) to confirm in the data dictionary.

### 5.1 `credits.csv`: 45,476 rows, 3 columns

| Column | Dtype (raw) | Target | Missing | Missing % | Unique | Hidden missing | Verdict |
|---|---|---|---:|---:|---:|---|---|
| `id` | int64 | int64 | 0 | 0.00 | 45,432 | none | Trust (key, but has repeats) |
| `cast` | object | list[dict] | 0 | 0.00 | 43,019 | `'[]'`: 2,418 (5.32%) | Transform (parse) |
| `crew` | object | list[dict] | 0 | 0.00 | 44,669 | `'[]'`: 771 (1.70%) | Transform (parse) |

`id` range: 2 to 469,172. Empty lists mean *unknown*, because every real film has people who made it.

### 5.2 `keywords.csv`: 46,419 rows, 2 columns

| Column | Dtype (raw) | Target | Missing | Missing % | Unique | Hidden missing | Verdict |
|---|---|---|---:|---:|---:|---|---|
| `id` | int64 | int64 | 0 | 0.00 | 45,432 | none | Trust (key, but has repeats) |
| `keywords` | object | list[dict] | 0 | 0.00 | 25,989 | `'[]'`: 14,795 (31.87%) | Transform (parse) |

`id` range: 2 to 469,172. Same 45,432 unique ids as `credits`. An empty list may mean "never tagged", which is not necessarily "unknown".

### 5.3 `links.csv`: 45,843 rows, 3 columns

| Column | Dtype (raw) | Target | Missing | Missing % | Unique | Range | Verdict |
|---|---|---|---:|---:|---:|---|---|
| `movieId` | int64 | int64 | 0 | 0.00 | 45,843 | 1 to 176,279 | Trust (MovieLens id, unique) |
| `imdbId` | int64 | string `tt0000000` | 0 | 0.00 | 45,843 | 1 to 7,158,814 | Transform (needs `tt` plus 7-digit padding) |
| `tmdbId` | float64 | Int64 | 219 | 0.48 | 45,594 | 2 to 469,172 | Transform and investigate (30 repeats) |

`tmdbId` is float only because it contains NaN.

### 5.4 `links_small.csv`: 9,125 rows, 3 columns

| Column | Dtype (raw) | Target | Missing | Missing % | Unique | Range | Verdict |
|---|---|---|---:|---:|---:|---|---|
| `movieId` | int64 | int64 | 0 | 0.00 | 9,125 | 1 to 164,979 | Trust (agrees with `links`; 10 ids appear only here) |
| `imdbId` | int64 | string `tt0000000` | 0 | 0.00 | 9,125 | 417 to 5,794,766 | Transform |
| `tmdbId` | float64 | Int64 | 13 | 0.14 | 9,112 | 2 to 416,437 | Transform |

No repeated non-null `tmdbId` (the old "12 duplicates" were the 13 NaNs).

### 5.5 `movies_metadata.csv`: 45,466 rows, 24 columns

| Column | Dtype (raw) | Target | Missing | Missing % | Unique | Notes | Verdict |
|---|---|---|---:|---:|---:|---|---|
| `id` | object | Int64 | 0 | 0.00 | 45,436 | TMDB id. 3 corrupted values are dates. 30 extra copies. 45,433 unique numeric ids. | Transform, then trust |
| `imdb_id` | object | string `tt0000000` | 17 | 0.04 | 45,417 | 32 real repeats. 64 not found in `links`. | Transform, cross-check only |
| `title` | object | string | 6 | 0.01 | 42,277 | Titles repeat naturally (remakes), not a key | Trust |
| `original_title` | object | string | 0 | 0.00 | 43,373 | | Trust |
| `original_language` | object | category | 11 | 0.02 | 92 | | Trust |
| `overview` | object | string | 954 | 2.10 | 44,307 | | Trust |
| `tagline` | object | string | 25,054 | 55.10 | 20,283 | | Trust (sparse) |
| `release_date` | object | datetime | 87 | 0.19 | 17,336 | | Transform |
| `status` | object | category | 87 | 0.19 | 6 | Released 45,014, Rumored 230, Post Production 98, In Production 20, Planned 15, Canceled 2 | Transform |
| `runtime` | float64 | float or Int64 | 263 | 0.58 | 353 | 1,558 zeros. Unknown total: 1,821 (4.01%). Range 0 to 1,256, mean 94.1. | Investigate |
| `budget` | object | numeric | 0 | 0.00 | 1,226 | 36,573 zeros (80.44%) = unknown. 3 non-numeric values (corrupted rows). | Transform and treat 0 as unknown |
| `revenue` | float64 | numeric | 6 | 0.01 | 6,863 | 38,052 zeros (83.69%) = unknown. Range 0 to 2,787,965,087. | Transform and treat 0 as unknown |
| `vote_average` | float64 | float | 6 | 0.01 | 92 | Range 0 to 10. All 2,899 movies with `vote_count` 0 have `vote_average` 0.0, which is a placeholder. A further 99 movies have average 0 with `vote_count` above 0: 81 of them have exactly 1 vote and the maximum is 58 votes, so these zeros are also suspect. | Transform (0 means missing when `vote_count` is 0) |
| `vote_count` | float64 | Int64 | 6 | 0.01 | 1,820 | Range 0 to 14,075. 2,899 zeros (6.38%) are real "no votes". | Transform, zeros are real |
| `popularity` | object | float64 | 5 | 0.01 | 43,758 | Non-numeric text from corrupted rows forces `object`. | Transform |
| `adult` | object | bool | 0 | 0.00 | 5 | False 45,454, True 9, 3 corrupted text values | Transform |
| `video` | object | bool | 6 | 0.01 | 2 | False 45,367, True 93. `object` only because bools plus NaN, not corruption. | Transform |
| `genres` | object | list[dict] | 0 | 0.00 | 4,069 | `'[]'`: 2,442 (5.37%) | Transform (parse) |
| `production_companies` | object | list[dict] | 3 | 0.01 | 22,708 | `'[]'`: 11,875 (26.12%) | Transform (parse) |
| `production_countries` | object | list[dict] | 3 | 0.01 | 2,393 | `'[]'`: 6,282 (13.82%) | Transform (parse) |
| `spoken_languages` | object | list[dict] | 6 | 0.01 | 1,931 | `'[]'`: 3,829 (8.42%). Can be genuine (silent films). Do not default to English. | Transform (parse) |
| `belongs_to_collection` | object | dict | 40,972 | 90.12 | 1,698 | NaN most likely means "not in a collection" (TO VERIFY) | Transform (parse) |
| `homepage` | object | string | 37,684 | 82.88 | 7,673 | Stale links, e.g. an old film redirecting to a newer sequel | **Ignore** |
| `poster_path` | object | string | 386 | 0.85 | 45,024 | Relative path only, not a usable image link on its own | Ignore (low value) |

**A note on `popularity`.** The earlier report showed 44,176 unique values. The correct figure is **43,758**. The old script read the file in chunks (`low_memory=True`), so the same number could be seen as both text and float and be counted twice. `low_memory=False` reads the column consistently.

### 5.6 `ratings.csv`: 26,024,289 rows, 4 columns

| Column | Dtype (raw) | Target | Missing | Unique | Range | Verdict |
|---|---|---|---:|---:|---|---|
| `userId` | int64 | int32 | 0 | 270,896 | 1 to 270,896 | Trust |
| `movieId` | int64 | int32 | 0 | 45,115 | 1 to 176,275 | Trust, **MovieLens id** |
| `rating` | float64 | float32 | 0 | 10 | 0.5 to 5.0 (steps of 0.5) | Trust |
| `timestamp` | int64 | datetime (seconds) | 0 | 20,549,435 | 1995-01-09 to 2017-08-04 | Transform |

Key (`userId`, `movieId`): 0 repeats.

### 5.7 `ratings_small.csv`: 100,004 rows, 4 columns

| Column | Dtype (raw) | Target | Missing | Unique | Range | Verdict |
|---|---|---|---:|---:|---|---|
| `userId` | int64 | int32 | 0 | 671 | 1 to 671 | Never mix with `ratings.userId` (separate numbering) |
| `movieId` | int64 | int32 | 0 | 9,066 | 1 to 163,949 | Trust (same id space as the full file) |
| `rating` | float64 | float32 | 0 | 10 | 0.5 to 5.0 | Trust |
| `timestamp` | int64 | datetime (seconds) | 0 | 78,141 | 789,652,009 to 1,476,640,644 | Transform |

### 5.8 Stringified list and dict columns

All 8 columns parse with **no failures**, but they are Python-style text (single quotes), not JSON. The parser for Stage 2 is **`ast.literal_eval`**, not `json.loads`.

| Column | `json_ok` | `python_literal_ok` | Missing | Note |
|---|---:|---:|---:|---|
| credits.cast | 2,418 | 43,058 | 0 | `json_ok` equals the `'[]'` count |
| credits.crew | 771 | 44,705 | 0 | same |
| keywords.keywords | 14,795 | 31,624 | 0 | same |
| meta.genres | 2,442 | 43,024 | 0 | same |
| meta.production_companies | 11,875 | 33,588 | 3 | same |
| meta.production_countries | **6,285** | 39,178 | 3 | 3 more than the 6,282 empty lists |
| meta.spoken_languages | 3,829 | 41,631 | 6 | same |
| meta.belongs_to_collection | **3** | 4,491 | 40,972 | the 3 `json_ok` are not real collections |

**Why `json_ok` equals the empty-list count:** `'[]'` is valid in both JSON and Python, while non-empty cells use single quotes, which only Python accepts.

**The 3 extra values** in `production_countries` and `belongs_to_collection` come from the 3 corrupted rows. Bare numbers such as `0.065736` or `6.0` are valid JSON, so they "parse" even though they are the wrong kind of value for the column. Lesson: **a successful parse proves the syntax is valid, not that the content is the right type.** After parsing, check that the result is a list of dicts (or a dict).

---

## 6. Hidden missing values

| Field | Hidden value | Count | % of rows | Interpretation |
|---|---|---:|---:|---|
| `credits.cast` | `'[]'` | 2,418 | 5.32 | Unknown (every film has a cast) |
| `credits.crew` | `'[]'` | 771 | 1.70 | Unknown |
| `keywords.keywords` | `'[]'` | 14,795 | 31.87 | Unknown or never tagged |
| `meta.genres` | `'[]'` | 2,442 | 5.37 | Unknown |
| `meta.production_companies` | `'[]'` | 11,875 | 26.12 | Unknown |
| `meta.production_countries` | `'[]'` | 6,282 | 13.82 | Unknown |
| `meta.spoken_languages` | `'[]'` | 3,829 | 8.42 | Unknown **or genuinely none** (silent films) |
| `meta.budget` | `0` | 36,573 | 80.44 | Unknown (a film cannot cost 0) |
| `meta.revenue` | `0` | 38,052 | 83.69 | Unknown |
| `meta.runtime` | `0` | 1,558 | 3.43 | Unknown (4.01% with the 263 NaN) |
| `meta.vote_count` | `0` | 2,899 | 6.38 | **Real observation** (no one voted) |
| `meta.imdb_id` | `'0'` | at least 1 | n/a | Placeholder for unknown (not a valid IMDb id) |

**Consequence:** averages of `budget` or `revenue`, and ROI (`revenue / budget`), are meaningless until zeros are treated as unknown. Dividing by a zero budget produces infinity. The usable sample for financial analysis is the set of movies with **both** budget and revenue greater than 0: **5,381 movies (11.84%)**. The 15 smallest positive budgets are all exactly **1.0**, which cannot be a dollar amount, so "greater than 0" is not a sufficient test. Positive budgets by size (measured): **25** are below 2, **79** below 10, **138** below 100, **245** below 1,000, **300** below 10,000, and **554** below 100,000. The most common real budgets are round figures (5,000,000 is the most frequent). Sample rows show the problem: *Modern Times* (1936) has budget 1 and revenue 8,500,000, and *Aquí Entre Nos* has budget 1 and revenue 2,755,584. **Revenue has the same problem**: tiny revenues such as 1, 3, 5 and 100 appear (e.g. *Saamy*, *East of Eden*). Proposed rule (to confirm): treat budgets below 1,000 as unknown, and apply an equivalent check to revenue (count pending).

---

## 7. Malformed records in `movies_metadata`

**Finding:** 3 logical records are split across 6 physical rows. A stub row holds the first columns of the record and is followed by a row containing the **tail** of the same record, shifted **9 columns to the left**. The 9-column shift is **confirmed for all three records** by a notebook test: every value in a corrupted row matches the column 9 positions to its right.

| Stub row index | Stub id | Corrupted row index | Value sitting in `id` column |
|---:|---:|---:|---|
| 19,729 | 82663 | 19,730 | `1997-08-20` |
| 29,502 | 122662 | 29,503 | `2012-09-29` |
| 35,586 | 249260 | 35,587 | `2014-01-01` |

**Evidence:**
- All 3 rows with a non-numeric `id` are exactly the 3 rows with an invalid `adult` value.
- In the corrupted row, consecutive original columns appear in order, shifted left: overview text, then popularity, poster path, production companies, production countries, release date.
- The corrupted row's `release_date` column holds a small number (`1`, `12`, `22`), which matches the last original column, `vote_count` (9 + 14 = 23).
- `title` is missing in exactly the 6 physical rows (19729, 19730, 29502, 29503, 35586, 35587), confirmed in the notebook. This matches the "6 missing" seen in many columns.

**Cause (confirmed by the raw lines):** each stub line in the raw file ends with a line break in the middle of the `overview` text, and the next physical line begins with the rest of that overview (for example ` - Written by Ørnås,0.065736,/ff9q...`). In the two stubs where the start of the overview is visible, it is not wrapped in quotes, so a CSV parser treats the line break as the end of the record. Everything after the break then lands 9 columns to the left, because the break fell inside column 9 (`overview`). The physical line numbers (19,762, 29,571, 35,670) run ahead of the row indexes (19,729, 29,502, 35,586) by a growing amount, which suggests other overviews with line breaks exist but were quoted correctly (hypothesis). Because the cause is known and the fix is deterministic (join the two overview pieces with the line break, then move the remaining values back into columns 10 onward), **repair is the stronger option than dropping**.

**What this explains:** `id` is text, `adult` has 5 values instead of 2, `budget` has 3 non-numeric values, and `popularity` is `object`.

**Decision (C01 in `7_cleaning_decisions.md`):** repair each record. If it were dropped instead, the **stub and its tail must be treated as one unit**, because dropping only the three bad-id rows would leave three ghost movies behind.

**Missingness pattern:** `release_date` and `status` are each missing 87 times, but only 4 rows are missing both (83 only date, 83 only status), so they are not the same rows. Most rows have 2 to 3 missing fields. Rows with 10 or more missing fields (5 of them) are the corrupted ones.

---

## 8. Relationships and joins

### 8.1 Id systems

```
TMDB ids                                         MovieLens ids
movies_metadata.id  --  credits.id               ratings.movieId
                    --  keywords.id                    |
links.tmdbId  <----------- links ------------>  links.movieId
                              |
                          links.imdbId  (IMDb ids, a third system)
```

Correct join chain: `ratings.movieId` → `links.movieId` → `links.tmdbId` → `movies_metadata.id`

### 8.2 Join tests (id overlap)

| Left | Right | In both | Only left | Only right |
|---|---|---:|---:|---:|
| meta.id | credits.id | 45,432 | 1 | 0 |
| meta.id | keywords.id | 45,432 | 1 | 0 |
| credits.id | keywords.id | 45,432 | 0 | 0 |
| meta.id | links.tmdbId | 45,433 | 0 | 161 |
| ratings.movieId | links.movieId | 45,115 | 0 | 728 |
| ratings.movieId | meta.id (**wrong join**) | 7,565 | 37,550 | 37,868 |

**Reading the table:**
- `credits` and `keywords` contain exactly the same ids and cover every metadata movie except 1: **id 401840, "School's out"** (released 2017-05-30, status Released, 0 votes). It is a normal row, not one of the corrupted records. Hypothesis (to verify): it was added to TMDB after the credits and keywords snapshot was taken.
- 161 `links.tmdbId` values point at movies that do not exist in metadata.
- 728 movies in `links` have never been rated.
- The last row is the proof that the two id systems differ. Only 16.8% of rated movies match by coincidence of numbers.

**Reachability through the bridge (measured):**

| Step | Movies |
|---|---:|
| Rated movies | 45,115 |
| Lost: no `tmdbId` in `links` | 213 |
| Lost: `tmdbId` not in metadata | 161 |
| **Reachable in metadata** | **44,741 (99.17%)** |

- 213 (not 219) lost for a missing `tmdbId`, because 6 of the 219 `links` rows with no `tmdbId` were never rated.
- By rating rows, **25,981,582 of 26,024,289 (99.84%)** are reachable. The 374 lost movies carry only 42,707 ratings (about 114 each, against about 577 for the average rated movie), so they are rarely rated.
- **59** reachable movies share their `tmdbId` with another `movieId` (the silent-risk case). They need a rule or exclusion before any join.

**Three problems inside `links`:**

| Problem | Count | Effect on a join | Visible? |
|---|---:|---|---|
| Missing `tmdbId` | 219 | Rows drop out | Yes, countable |
| `tmdbId` not in metadata | 161 | Rows drop out | Yes, countable |
| Repeated `tmdbId` | 30 | Rows **multiply or merge** | **No, silent** |

### 8.3 IMDb id format

| Table | Column | Example | Type |
|---|---|---|---|
| movies_metadata | `imdb_id` | `tt0114709` | string |
| links | `imdbId` | `114709` | int |

After rebuilding the `tt` plus 7-digit form: 45,353 match, 64 only in metadata, 490 only in links.

**Which key to use between metadata and links:**

| Key | Metadata side | Links side | Metadata movies with no match |
|---|---|---|---:|
| TMDB (`id` vs `tmdbId`) | 0 missing, 30 extra copies | 219 missing, 30 repeats | 0 |
| IMDb (`imdb_id` vs `imdbId`) | 17 missing, 32 repeats | 0 missing, 0 repeats | 64 |

TMDB is the backbone key because `credits` and `keywords` only carry it. IMDb is a cross-check.

**Agreement test (measured):** after excluding the 59 ambiguous rows on each side, **45,387** movies were compared. **45,322 agree and 65 disagree (0.14%)**. The two id paths agree for 99.86% of movies, so TMDB is reliable as the backbone. A disagreement does not say which side is wrong; settling that needs an external source (the IMDb or TMDB site). **How the 65 relate to the 64 (measured):** 63 of the 65 disagreeing `imdb_id` values are among the 64 metadata ids that do not exist in `links` at all. So almost all disagreements are metadata ids that `links` has never seen. The 2 exceptions (`tt0486420`, `tt0785025`) exist in `links` but are attached to a different movie, which is a genuine conflict. The one metadata id missing from `links` that is not a disagreement is the string `'0'`, a placeholder for an unknown IMDb id (that row is not in the compared set; why is still to be checked).

### 8.4 The `_small` files

| Check | Result |
|---|---|
| `links_small.movieId` in `links.movieId` | 9,115 of 9,125 (10 appear only in `links_small`) |
| Shared ids that agree on `tmdbId` and `imdbId` | **9,115 of 9,115** |
| `ratings_small.movieId` in `links_small.movieId` | True |
| `ratings_small` vs `ratings`, 4-column match including `userId` | 0 of 100,004 (a **flawed test**, because `userId` is renumbered) |
| Same match **without** `userId` (distinct `movieId`, `rating`, `timestamp`) | **99,671 of 100,004 (99.67%)**; 333 do not match |
| Small users that map to exactly one full user | **99.25%** |

- `ratings_small` **is a sample** of `ratings`, with users renumbered (1 to 671 in the small file, 1 to 270,896 in the full file). The `links` files use the same MovieLens id space.
- **Never combine `userId` values across the two files.**
- Still unexplained: 333 combinations (0.33%) that do not match, and 10 `movieId` values found only in `links_small`. Both are small enough to ignore for now, but worth a note.
- Working default: use the full files as the source of truth. The small files are redundant and are useful only for fast prototyping.

---

## 9. Plausibility checks

| Check | Result | Verdict |
|---|---|---|
| Rating timestamps | 1995-01-09 to 2017-08-04 | Plausible. Convert from Unix seconds. |
| Runtime zeros | 1,558 zeros (1,821 unknown with the NaN) | Unknown. Treat as missing. |
| Runtime above 300 minutes | 108 movies. Top: Centennial 1,256, Jazz 1,140, Baseball 1,140, Berlin Alexanderplatz 931, Heimat 925 | **Not data errors.** These are real TV miniseries and documentary series. **Do not cap or drop.** Flag them (`runtime > 300`) and exclude only from analyses they would distort. The dataset therefore includes more than feature films. |

---

## 10. Open items

| # | Item | Status |
|---:|---|---|
| 1 | Reachable rated movies through the bridge | **Done:** 44,741 of 45,115 (99.17%); 99.84% of rating rows |
| 2 | Which `meta` id is missing from `credits` and `keywords` | **Done:** 401840, "School's out" (not a corrupted record) |
| 3 | Do the TMDB and IMDb paths agree? | **Done:** 45,322 of 45,387 agree (99.86%) |
| 4 | Do shared `movieId` values in `links` and `links_small` agree? | **Done:** all 9,115 agree |
| 5 | Movies with `runtime` over 300 | **Done:** 108, mostly miniseries and documentaries |
| 6 | Inspect the conflicting duplicate ids | **Done:** credits differ in `crew`; metadata in `popularity` (and `vote_count` for 2). Keep-rule goes in the cleaning decisions. |
| 7 | Movies with both budget and revenue above 0 | **Done:** 5,381 (11.84%) |
| 8 | `vote_average` when `vote_count` is 0 | **Done:** always 0.0, a placeholder |
| 9 | Split-record details | **Done:** 6 missing titles and the 9-column shift confirmed for all 3 records |
| 10 | Triple-id cases | **Done:** 141971 (credits, keywords) and 159849 (keywords) |
| 11 | Are the 65 IMDb disagreements the 64 ids missing from `links`? | **Done:** 63 overlap; 2 are real conflicts; 1 id is the placeholder `'0'` |
| 12 | Positive budgets below 1,000 and below 10,000 | **Done:** 245 and 300 |
| 13 | `vote_count` of the 99 movies with `vote_average` 0 and votes | **Done:** 81 have exactly 1 vote, maximum 58 |
| 14 | Do `ratings_small` rows match `ratings` without `userId`? | **Done:** 99.67% match; 99.25% of users map to one full user |
| 15 | Raw lines of the split records (confirm the line-break-in-overview cause) | **Done:** confirmed, an unquoted overview containing a line break |
| 16 | Revenue counterpart of the tiny-budget check (count of tiny positive revenues) | Pending |
| 17 | Why Excel showed 45,505 rows for `credits` (the file has 45,477 physical lines) | Unresolved, low priority |