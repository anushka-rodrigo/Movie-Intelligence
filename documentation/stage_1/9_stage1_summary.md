# Stage 1 Summary: Understanding the Raw Data

**Project:** Movie Intelligence
**Dataset:** The Movies Dataset (Kaggle, rounakbanik): https://www.kaggle.com/datasets/rounakbanik/the-movies-dataset
**Stage goal:** understand what we actually have before writing serious code
**Tools:** Python, pandas, Jupyter
**Last updated:** 2026-10-19

---

## 1. Summary in one page

1. **There are seven files and three id systems.** TMDB ids (the backbone), MovieLens ids (used only by ratings), and IMDb ids (a cross-check). `links` is the only table that holds both the MovieLens id and the TMDB id, so it is the bridge.
2. **Ratings reach movies only through `links`.** The path is `ratings.movieId` → `links.movieId` → `links.tmdbId` → `movies_metadata.id`. A direct join silently loses 83.2% of rated movies and attaches the rest to the wrong film.
3. **44,741 of 45,115 rated movies (99.17%) can reach metadata**, covering 99.84% of the 26,024,289 ratings.
4. **The movie tables contain repeated ids.** Credits has 44 extra copies, keywords 987, metadata 30. Most are exact copies. The 7 credits ids whose copies differ hold the same crew in a different order, and 13 metadata ids have copies that differ (in `popularity`, and in `vote_count` for 2).
5. **3 metadata records are corrupted.** Each is split across two physical rows because an unquoted overview contains a line break. The cause is confirmed, and the repair is deterministic.
6. **Many fields hide missing values.** Budget is unknown for 80.44% of movies, revenue for 83.69%, and 31.87% of keyword rows are empty lists. Pandas' own missing counts understate this.
7. **The list and dict columns are Python-style text**, parsed with `ast.literal_eval`, not JSON.
8. **The small files are samples of the full files** with renumbered users, so the project uses the full files.
9. **After cleaning, we expect 45,433 metadata rows, 45,432 credits rows, and 45,432 keywords rows.** These numbers work as tests for the cleaning script.

---

## 2. What we examined

| File | Rows | Columns | Key | Role |
|---|---:|---:|---|---|
| `movies_metadata.csv` | 45,466 | 24 | `id` (TMDB) | Main movie table |
| `credits.csv` | 45,476 | 3 | `id` (TMDB) | Cast and crew per movie |
| `keywords.csv` | 46,419 | 2 | `id` (TMDB) | Plot keywords per movie |
| `links.csv` | 45,843 | 3 | `movieId` (MovieLens) | Bridge between id systems |
| `links_small.csv` | 9,125 | 3 | `movieId` | Small version of `links` |
| `ratings.csv` | 26,024,289 | 4 | (`userId`, `movieId`) | User ratings |
| `ratings_small.csv` | 100,004 | 4 | (`userId`, `movieId`) | Sample of `ratings` |

**Excel versus pandas:** Excel's 1,048,576 for `ratings` was its row limit, not the real count. Three more (`keywords`, `links`, `movies_metadata`) were 1 too high because Excel counts the header. The Excel count for `credits` (45,505) is unexplained: the file has 45,477 physical lines, so line breaks do not account for it.

---

## 3. How the data fits together

### 3.1 The id systems

| System | Columns | Role |
|---|---|---|
| **TMDB id** | `movies_metadata.id`, `credits.id`, `keywords.id`, `links.tmdbId` | Backbone key |
| **MovieLens id** | `ratings.movieId`, `links.movieId` | Ratings only |
| **IMDb id** | `movies_metadata.imdb_id` (`tt0114709`), `links.imdbId` (`114709`) | Cross-check only |

**Worked example:** to `ratings`, Toy Story is `1`. To `movies_metadata`, `credits` and `keywords`, it is `862`.

### 3.2 Relationships

```
movies_metadata ──1 : 0..1── credits         (join on id)
       │        └──1 : 0..1── keywords       (join on id)
       │
       └─ 1 : 0..many ── links ── 1 : 0..many ── ratings
          (id = tmdbId)  BRIDGE   (movieId)      (users x movies,
                                                  many-to-many)
```

| Relationship | Cardinality | Exceptions |
|---|---|---|
| metadata to credits | 1 to 0..1 | Movie 401840 ("School's out") has no credits or keywords |
| metadata to keywords | 1 to 0..1 | Same |
| metadata to links | 1 to 0..many | 30 repeated `tmdbId` values (59 movies share one), 219 links with no `tmdbId`, 161 `tmdbId` not in metadata |
| links to ratings | 1 to 0..many | 728 `links` movies never rated |
| users to movies (via ratings) | many to many | `ratings` is the junction table |

Inside the list columns, movies relate many to many to genres, companies, countries, languages, keywords, and people. A **keyword shared by many movies is normal**, while the **same movie id in two rows** of `keywords` is a data problem.

### 3.3 Join results

| Measure | Value |
|---|---:|
| Rated movies | 45,115 |
| Lost: no `tmdbId` in `links` | 213 |
| Lost: `tmdbId` not in metadata | 161 |
| **Reachable in metadata** | **44,741 (99.17%)** |
| Rating rows reachable | 25,981,582 of 26,024,289 (99.84%) |
| Reachable movies sharing a `tmdbId` with another movie | 59 |
| TMDB and IMDb paths that agree | 45,322 of 45,387 (99.86%) |

The 374 lost movies carry only 42,707 ratings (about 114 each, against about 577 for the average rated movie), so they are rarely rated.

---

## 4. Data-quality findings

### 4.1 Corrupted records

| Finding | Detail | Decision |
|---|---|---|
| 3 metadata records split across 6 rows | Stub rows 19729, 29502, 35586 end mid-`overview`. The tail rows (19730, 29503, 35587) are shifted 9 columns left. **Cause (confirmed in the raw file):** an unquoted overview containing a line break. | Repair (C01) |
| Symptoms | `id` is text, `adult` has 5 values, `budget` has 3 non-numeric values, `popularity` is `object`, `title` is missing for exactly these 6 rows | Fixed by C01 |

### 4.2 Duplicates

| Table | Extra copies | Repeated ids | Identical | Differ | Decision |
|---|---:|---:|---:|---:|---|
| keywords | 987 | 985 | 985 | 0 | Drop extras (C03) |
| credits | 44 | 43 | 36 | 7 (same crew, different order) | Drop extras, keep the first copy (C04, C05) |
| movies_metadata | 30 | 29 | 16 | 13 (differ in `popularity`, 2 also in `vote_count`) | Drop identical (C06); keep higher `vote_count` (C07) |

Ids appearing three times: 141971 (credits and keywords) and 159849 (keywords). By the arithmetic, one metadata id also appears three times; it has not been named. The identity `extra copies − fully duplicated rows = ids whose copies differ` holds in every table. The conflicting copies look like snapshots taken at different times.

### 4.3 Hidden missing values

| Field | Hidden value | Count | % of rows | Reading |
|---|---|---:|---:|---|
| `budget` | `0` | 36,573 | 80.44 | Unknown |
| `budget` | below 1,000 | 245 | n/a | Placeholder (25 are exactly 1) |
| `revenue` | `0` | 38,052 | 83.69 | Unknown |
| `runtime` | `0` | 1,558 | 3.43 | Unknown |
| `vote_average` | `0` with `vote_count` 0 | 2,899 | 6.38 | Placeholder |
| `vote_average` | `0` with votes | 99 | 0.22 | Suspect (81 have a single vote) |
| `vote_count` | `0` | 2,899 | 6.38 | **Real** (nobody voted) |
| `keywords` | `'[]'` | 14,795 | 31.87 | Unknown or never tagged |
| `production_companies` | `'[]'` | 11,875 | 26.12 | Unknown |
| `production_countries` | `'[]'` | 6,282 | 13.82 | Unknown |
| `spoken_languages` | `'[]'` | 3,829 | 8.42 | Unknown or genuinely none (silent films) |
| `genres` | `'[]'` | 2,442 | 5.37 | Unknown |
| `cast` | `'[]'` | 2,418 | 5.32 | Unknown |
| `crew` | `'[]'` | 771 | 1.70 | Unknown |
| `imdb_id` | `'0'` | at least 1 | n/a | Placeholder |

Only **5,381 movies (11.84%)** have both budget and revenue above 0, and **5,312 (11.68%)** once budget and revenue below 1,000 are treated as missing (C18, C19).

### 4.4 Types and parsing

- 8 columns hold Python-style text. All non-empty cells parse with `ast.literal_eval`, with 0 failures.
- `json_ok` equals the `'[]'` count because `'[]'` is valid in both JSON and Python.
- 3 numbers from the corrupted rows "parse" in `production_countries` and `belongs_to_collection` even though they are the wrong type. A successful parse proves syntax, not content, so check the parsed type as well.
- The `imdb_id` format differs between tables (`tt0114709` versus `114709`), so a raw join matches nothing.

### 4.5 Plausibility

| Check | Finding | Decision |
|---|---|---|
| Rating timestamps | 1995-01-09 to 2017-08-04 | Convert from Unix seconds |
| Runtime above 300 minutes | 108 movies, mostly real TV miniseries and documentaries (Centennial 1,256, Jazz 1,140, Baseball 1,140) | Flag, never cap or drop (C21) |
| Rating scale | The Kaggle description says 1 to 5, the data has a minimum of 0.5 | Trust the data |
| `homepage` | Stale (an old film's link redirects to a newer sequel) | Ignore |

### 4.6 The small files

`links_small` agrees with `links` on all 9,115 shared ids (10 ids appear only in the small file). 99.67% of the distinct (`movieId`, `rating`, `timestamp`) combinations in `ratings_small` appear in `ratings`, and 99.25% of small users map to exactly one full user. So `ratings_small` is a sample with renumbered users. Never combine `userId` values across the two files.

---

## 5. Field trustworthiness

| Verdict | Fields |
|---|---|
| **Trust** | `title`, `original_title`, `original_language`, `overview` (after repair), `tagline`, `rating`, `userId`, `movieId`, `links.movieId` |
| **Transform** | `movies_metadata.id`, `imdb_id`, `release_date`, `status`, `adult`, `video`, `budget`, `revenue`, `vote_average`, `vote_count`, all list and dict columns, `links.imdbId`, `links.tmdbId`, `timestamp` |
| **Investigate** | `runtime` (flag long values, zeros are missing), `popularity` (a time-varying snapshot), `ratings_small.userId` (do not mix) |
| **Ignore** | `homepage`, `poster_path` |

The full column-by-column meanings are in `6_data_dictionary.md`.

---

## 6. Decisions made

30 decisions are recorded in `7_cleaning_decisions.md`.

| Status | Count | Examples |
|---|---:|---|
| Decided | 27 | Repair the split records (C01), TMDB as the backbone (C08), never join ratings to metadata directly (C09), order-only crew duplicates (C05), budget and revenue thresholds of 1,000 (C18, C19), `ast.literal_eval` (C26) |
| Proposed | 3 | Flag IMDb conflicts (C17), leave out `homepage` and `poster_path` (C28), keep `popularity` and `video` as low priority (C30) |
| Your call | 0 | none left |
| Pending | 0 | none left |


### Expected row counts after cleaning

| Table | Raw | Expected | How |
|---|---:|---:|---|
| `movies_metadata` | 45,466 | **45,433** | 45,466 − 3 (split records) − 30 duplicate copies |
| `credits` | 45,476 | **45,432** | 45,476 − 44 duplicate copies |
| `keywords` | 46,419 | **45,432** | 46,419 − 987 duplicate copies |
| `links` | 45,843 | 45,843 (45,624 after dropping 219 with no `tmdbId`) | |
| `ratings` | 26,024,289 | 26,024,289 | Unchanged |

**Cross-check:** metadata should have exactly 1 id that `credits` and `keywords` lack (401840).

---

## 7. Deliverables

| File | What it is |
|---|---|
| `4_metadata_summary.md` | Data-quality report: every table profiled, with corrected numbers |
| `5_data_investigation_qa.md` | The questions, answers and reasoning from the learning process, with overall findings |
| `6_data_dictionary.md` | Every column: meaning, types, missing values, verdict |
| `7_cleaning_decisions.md` | 30 decisions with evidence, reason and status, plus expected row counts |
| `8_relationship_diagram.md` | Diagram, cardinalities, join recipes, silent risks |
| `9_stage1_summary.md` | This document |
| `stage1_data_investigation.ipynb` | The investigation notebook with saved outputs |

---

## 8. Milestone 1 checklist

| Required item | Status |
|---|---|
| Data dictionary | **Done** |
| Data-quality report | **Done** |
| Relationship diagram | **Done** |
| List of cleaning decisions | **Done** (27 of 30 decided; 3 low-impact proposals remain: C17, C28, C30) |
| Clear understanding of ids and joins | **Not yet confirmed.** See section 10. |

---

## 9. Carried into the next stage

**Optional checks (they feed Stage 2 decisions, they do not block Stage 1):**
1. Resolve the 59 shared-`tmdbId` movies and review the 2 genuine IMDb conflicts (C12, C17).
2. Test why movie 401840 is missing from credits and keywords (hypothesis: added to TMDB after the snapshot).
3. Check the exact keys inside the `cast`, `keywords` and collection fields after parsing (the `crew` keys are confirmed: `credit_id`, `department`, `gender`, `id`, `job`, `name`, `profile_path`).
4. Explain the Excel count for `credits`, a low priority.

**Decisions recorded** (section 9 of `7_cleaning_decisions.md`): all seven are filled in. Three proposals remain open: C17, C28 and C30.

**Unconfirmed meanings** (see the end of `6_data_dictionary.md`): what `video` flags, whether budget and revenue are always US dollars, and what a missing `belongs_to_collection` means.

---

## 10. Closing Stage 1: the milestone self-check

The milestone says you should be able to **explain every dataset and its relationships without looking at the code**. Your first attempt got the TMDB backbone right but placed `ratings` in the wrong id system and named the bridge as an id rather than a table. After review, the correct picture is in section 3 of this document.

**Stage 1 is closed when you can answer these three questions from memory, without this document:**

1. Fill in the blanks: `ratings.movieId` is in the ______ id system, `links` holds ______ and ______ side by side, and `movies_metadata.id` is in the ______ id system.
2. In one or two sentences: why does `ratings.movieId = movies_metadata.id` give *wrong* matches, and not only missing ones?
3. Trace `movieId` 1 to its movie. Name the two lookups and the number you find at each step.

**Answers** (check yourself after trying):
1. MovieLens; the MovieLens id and the TMDB id; TMDB.
2. They are two different numbering schemes that share digits by coincidence, so some ids match but point to different films, with no error.
3. `ratings.movieId` 1 → `links` row `movieId` 1 gives `tmdbId` 862 → `movies_metadata.id` 862 is Toy Story.

---

## 11. Lessons about method

1. **State a claim, test it, then record what you found.** Several early claims turned out wrong when tested: that the small files were not samples, that runtime should be capped, and that IMDb ids were more reliable.
2. **Joins fail silently.** Check id systems, formats and dtypes before joining, and check row counts after.
3. **Pandas' missing counts are a floor.** Look for placeholders such as `'[]'`, `0` and `'0'`.
4. **Judge duplicates at row and key level**, not per column, and separate identical copies from conflicting ones.
5. **Never fill a gap with a plausible default or a cap.** Flag it, exclude it, or find a second source of evidence.
6. **A successful parse proves the syntax, not the content.** Check the type of what you parsed.
7. **Read the numbers and the sample rows before concluding.** The answers to several questions were sitting in the outputs.
8. **A notebook is only trustworthy if it runs cleanly from the top.** Restart the kernel and run all cells.