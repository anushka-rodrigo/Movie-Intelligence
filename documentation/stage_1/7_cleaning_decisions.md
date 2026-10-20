# Cleaning Decisions List

**Project:** Movie Intelligence
**Stage:** 1, Understand the Raw Data (closing deliverable)
**Last updated:** 2026-10-19
**Evidence:** `4_metadata_summary.md` (counts), `5_data_investigation_qa.md` (reasoning), `6_data_dictionary.md` (column meanings)

> **How to use this list.** Each decision names a problem, the evidence for it, what we do, and why. The **Status** column says how settled it is. Decisions marked **My call** are judgement calls where I choose and record my own reasoning, because these are the decisions Stage 2 will rest on. I edit this file as I decide.

| Status | Meaning |
|---|---|
| **Decided** | The evidence settles it |
| **Proposed** | AI recommendation, based on the evidence. I confirm or change it. |
| **My call** | A real judgement call. I choose and write down why. |
| **Pending** | One more check is needed before deciding |

---

## 1. Ground rules

These apply to every decision below.

1. **Raw files are read-only.** Cleaned output goes to a separate folder (for example `data/processed/`).
2. **Never invent data.** No capping, no filling with a "typical" value, no defaulting a language to English. Mark the value unknown, flag it, or leave it out of the analysis.
3. **Flag instead of overwrite.** When a value is suspicious but possibly real (such as a very long runtime), add a flag column and keep the value.
4. **Check row counts after every join and every drop.** Compare with the expected number, because joins fail silently.
5. **Cleaning lives in a script**, not only in a notebook, and logs row counts before and after each step.

---

## 2. Structural repairs

| ID | Problem and evidence | Decision | Reason | Status |
|---|---|---|---|---|
| C01 | **3 metadata records are split across 6 physical rows.** The raw lines show each stub ending with a line break inside the `overview` (an overview that is not wrapped in quotes), and the next line starting with the rest of that overview. The tail is therefore shifted 9 columns left (confirmed for all three records). The bad rows have dates in `id`, text in `adult`, and numbers in `budget`. | **Repair.** For each record, join the stub's `overview`, a line break, and the tail's first value (which starts with a space), then move the tail's remaining values into columns 10 onward. Result: 3 rows instead of 6. Never drop only the bad-id rows, because that leaves 3 ghost stubs. | The cause is confirmed and the fix is deterministic. The loss from dropping would be small, but the repair is cheap and keeps real movies. | **Decided** |
| C02 | `popularity` showed 44,176 unique values in one read and 43,758 in another, because reading in chunks mixed text and float. | Load `movies_metadata.csv` with `low_memory=False`. Load `ratings.csv` with compact dtypes (int32, float32). | Consistent types per column, and the 26M-row file fits in memory. | **Decided** |

---

## 3. Duplicates

| ID | Problem and evidence | Decision | Reason | Status |
|---|---|---|---|---|
| C03 | **keywords:** 985 ids repeat, all copies identical (987 extra rows). Ids 141971 and 159849 appear three times. | Drop the extra copies, keeping one. | Pure redundancy. | **Decided** |
| C04 | **credits:** 36 repeated ids with identical copies. Id 141971 appears three times. | Drop the extra copies, keeping one. | Pure redundancy. | **Decided** |
| C05 | **credits:** 7 ids (4912, 69234, 99080, 110428, 132641, 159849, 298721) looked different because their `crew` text differs (the lengths are identical). **Parsed and compared:** in all 7, both copies hold exactly the same crew members (4 to 17 each) in a different order. No member is missing from either copy, and no field differs. | Treat them as identical copies: keep the **first copy** and drop the rest. Log the 7 ids. | The two copies carry the same information, so nothing is lost. An exact text comparison flagged them only because the order differs, so compare crew lists without regard to order. | **Decided** |
| C06 | **metadata:** 16 repeated ids with identical copies (17 fully duplicated rows). | Drop the extra copies, keeping one. | Pure redundancy. | **Decided** |
| C07 | **metadata:** 13 ids whose copies differ in `popularity` (all 13) and `vote_count` (ids 10991 and 15028). Four of these ids (4912, 69234, 110428, 132641) also conflict in `credits`. | Keep the copy with the **higher `vote_count`**. If the counts are equal, keep the first copy in the file (tie-break chosen by me). Log every id affected. Never choose by `popularity`. | `vote_count` only grows, so a higher count means a later snapshot. `popularity` changes constantly, so it cannot say which copy is newer. | **Decided** |

**Expected result of C01 to C07:** metadata ends with **45,433** rows (45,466 − 3 − 30), credits with **45,432**, keywords with **45,432**.

---

## 4. Keys and joins

| ID | Problem and evidence | Decision | Reason | Status |
|---|---|---|---|---|
| C08 | Three id systems exist. The TMDB path and the IMDb path agree for 45,322 of 45,387 comparable movies (99.86%). | Use the **TMDB id as the backbone key** (`movies_metadata.id`, `credits.id`, `keywords.id`, `links.tmdbId`). | It is complete on the metadata side, and `credits` and `keywords` only carry it. | **Decided** |
| C09 | `ratings.movieId` is a MovieLens id. Joining it directly to `movies_metadata.id` loses 83.2% of rated movies and attaches the other 16.8% to the wrong film. | Always join through the bridge: `ratings.movieId` → `links.movieId` → `links.tmdbId` → `movies_metadata.id`. **Never** join ratings to metadata directly. | Two unrelated numberings share digits by coincidence, and no error is raised. | **Decided** |
| C10 | 219 `links` rows have no `tmdbId` (213 of them are rated movies). | Exclude them from the bridge. Keep them in the raw file. Report the loss. | The bridge cannot reach metadata for these movies. | **Decided** |
| C11 | 161 `links.tmdbId` values are not in metadata. | Exclude those movies when linking ratings to metadata. Report the loss. | There is no metadata row to attach to. | **Decided** |
| C12 | 30 repeated `links.tmdbId` values. 59 reachable rated movies share their `tmdbId` with another `movieId`. | Exclude these movies from joins and flag them, until each pair is resolved by comparing the metadata title and `imdb_id`. | Two MovieLens movies sharing one TMDB id would pool their ratings, and one metadata movie matching two ids would appear twice, with no error. | **Decided** (exclude and flag, chosen by me) |
| C13 | Metadata movie 401840 ("School's out", 2017) is missing from `credits` and `keywords`. | Join from metadata with **left joins** to `credits` and `keywords`. Keep 401840 with empty cast, crew and keywords. | An inner join would silently drop a real movie. | **Decided** |
| C14 | Joins can multiply or drop rows without any error. | After every join, assert the row count and the uniqueness of the key. | This is how the shared-id problem is caught. | **Decided** |
| C15 | `imdb_id` is `tt0114709` in metadata and `114709` in `links`. A raw join matches nothing. | Normalise `links.imdbId` to the form `tt` plus 7 digits. Use the IMDb id only as a **cross-check**. | The TMDB id is the backbone, and `meta.imdb_id` has 17 missing and 32 repeated values. | **Decided** |
| C16 | At least one `meta.imdb_id` is the string `'0'`. | Convert `'0'` to missing. | It is a placeholder, not a valid id. | **Decided** |
| C17 | 65 movies have an IMDb id that disagrees with `links`. 63 are ids that `links` has never seen. 2 (`tt0486420`, `tt0785025`) exist in `links` but point to another movie. | Keep the TMDB path as the truth. Add a flag column `imdb_conflict`. Review the 2 genuine conflicts by hand against the IMDb or TMDB site. | A disagreement does not show which side is wrong, and the rate is only 0.14%. | **Proposed** |

---

## 5. Missing values and placeholders

| ID | Problem and evidence | Decision | Reason | Status |
|---|---|---|---|---|
| C18 | **budget:** 36,573 zeros (80.44%) and 245 positive values below 1,000 (25 are exactly 1). Real budgets are round figures such as 5,000,000. 55 more fall between 1,000 and 10,000. | Set zeros to missing. Set budgets **below 1,000** to missing. Flag the 55 between 1,000 and 10,000 for review. | A film cannot cost 0 or 1. *Modern Times* (1936) shows budget 1 with revenue 8,500,000, which proves the 1 is a placeholder. | **Decided** (threshold 1,000, chosen by me) |
| C19 | **revenue:** 38,052 zeros (83.69%) and 7,408 positive values. 155 positive values are below 1,000 (12 are exactly 1), 238 below 10,000 and 581 below 100,000. Of the 155 tiny revenues, 16 sit next to a budget of 1,000 or more (a contradiction), 44 next to a tiny budget (1 to 999), and 95 next to a budget of 0 (budget unknown). | Set zeros to missing. Set revenues **below 1,000** to missing (the same threshold as budget). Flag the 83 values from 1,000 to under 10,000 for review. **Do not rescale** any value. | A released film does not earn under $1,000, and 16 of the 155 contradict a real budget. Unlike budget, the counts do not level off (343 more fall between 10,000 and 100,000), so the threshold stays conservative and the borderline band is flagged. | **Decided** (from the counts) |
| C20 | Only 5,381 movies (11.84%) have both budget and revenue above 0. With the thresholds from C18 and C19 (both 1,000) the usable sample is **5,312 movies (11.68%)**. | Report the usable financial sample after cleaning. Use it only for budget, revenue and ROI questions. | The sample is probably skewed toward well-documented films. | **Decided** |
| C21 | **runtime:** 1,558 zeros (1,821 unknown with the 263 NaN). 108 movies run over 300 minutes. They are real TV miniseries and documentary series (Centennial 1,256, Jazz 1,140, Baseball 1,140). | Set zeros to missing. Add a flag `long_runtime` for runtime above 300. **No capping and no dropping.** | They are real data. They are excluded only from analyses they would distort. | **Decided** |
| C22 | **vote_average:** all 2,899 movies with `vote_count` 0 have average 0.0. 99 more have average 0 with votes (81 of them with a single vote, maximum 58). | Set `vote_average` 0 to missing everywhere (2,998 movies). Flag the 99. | A movie with no votes has no average, and an average of exactly 0 over many votes is not credible. | **Decided** (chosen by me) |
| C23 | **vote_count:** 2,899 zeros (6.38%). | Keep the zeros. | Nobody voted, which is a real observation. | **Decided** |
| C24 | Empty lists `'[]'`: `cast` 2,418, `crew` 771, `keywords` 14,795 (31.87%), `genres` 2,442, `production_companies` 11,875 (26.12%), `production_countries` 6,282, `spoken_languages` 3,829. | Parse them as empty lists and treat them as **unknown** for cast, crew, genres, companies and countries. For `keywords`, treat as unknown or never tagged. **Never fill `spoken_languages` with English.** Keep `original_language` as a separate field. | Defaulting to English would mislabel every non-English film in the empty rows. Silent films genuinely have no spoken language. | **Decided** |
| C25 | Other missing values: `tagline` 55.10%, `overview` 2.10%, `release_date` 87, `status` 87, `runtime` 263. | Leave as missing. No imputation. Exclude a row only from the analysis that needs the missing field (for example, time analyses skip the 87 missing dates). | Filling gaps would invent data. | **Decided** |

---

## 6. Types and parsing

| ID | Problem and evidence | Decision | Reason | Status |
|---|---|---|---|---|
| C26 | 8 columns hold Python-style text (single quotes). All non-empty cells parse with 0 failures. The `json_ok` count equals the `'[]'` count. 3 values in `production_countries` and `belongs_to_collection` are numbers that parse but are the wrong type. | Parse with **`ast.literal_eval`**, not `json.loads`. After parsing, check that each result is a list (or a dict for `belongs_to_collection`). | A successful parse only proves the syntax. The 3 wrong-type cells disappear after C01, and the type check proves it. | **Decided** |
| C27 | Wrong raw dtypes (see the data dictionary). | `id` to Int64 (after C01). `adult` and `video` to bool. `status` and `original_language` to category. `release_date` to datetime. `vote_count` to Int64. `popularity`, `budget`, `revenue` to numeric. `links.tmdbId` to Int64. `timestamp` from Unix seconds to datetime. | Wrong types cause silent errors. The `tmdbId` is float only because of its NaN values. | **Decided** |

---

## 7. Columns and files to leave out

| ID | Problem and evidence | Decision | Reason | Status |
|---|---|---|---|---|
| C28 | `homepage` is 82.88% empty and the rest is stale (an old film's link redirects to a newer sequel). `poster_path` is only a relative path. | Leave both out of the cleaned table. Keep them in the raw file. | Low value and not trustworthy. | **Proposed** |
| C29 | `ratings_small` is a sample of `ratings` (99.67% of its distinct combinations match). Its `userId` is numbered separately (1 to 671 vs 1 to 270,896). `links_small` agrees with `links` on all 9,115 shared ids. | Use the full files as the source of truth. Use the small files only for fast prototyping. **Never combine `userId` values across the two files.** | The small files add nothing, and mixing users would corrupt any user-level analysis. | **Decided** |
| C30 | `popularity` is a time-varying snapshot (it differs between duplicate copies). `video` has an unconfirmed meaning. | Keep both in the cleaned table but treat them as low priority. Do not rely on `popularity` to decide anything. | They may be useful later, but their meaning is not firm. | **Proposed** |

---

## 8. Expected row counts after cleaning

Use these as checks. If the cleaned counts differ, something went wrong.

| Table | Raw rows | Expected after cleaning | How |
|---|---:|---:|---|
| `movies_metadata` | 45,466 | **45,433** | 45,466 − 3 (C01) − 30 duplicate copies (C06, C07) |
| `credits` | 45,476 | **45,432** | 45,476 − 44 duplicate copies (C04, C05) |
| `keywords` | 46,419 | **45,432** | 46,419 − 987 duplicate copies (C03) |
| `links` | 45,843 | 45,843 (45,624 after C10) | Not de-duplicated. C10 drops the 219 with no `tmdbId`. |
| `ratings` | 26,024,289 | 26,024,289 | Unchanged. Reachable through the bridge: 44,741 of 45,115 movies before C12. |

**Cross-check:** after cleaning, metadata should have exactly **1** id that `credits` and `keywords` lack (401840).

---

## 9. Decisions recorded

Decisions were recorded on 2026-10-19. Rows marked **(from the outputs)** were answered from my check results rather than chosen by me. I can change any of them if I disagree.

| ID | Question | AI recommendation | Decision |
|---|---|---|---|
| C01 | Repair or drop the 3 split records? | Repair | **Repair** (chosen by me) |
| C05 | Which copy wins for the 7 conflicting `crew` lists? | Compare parsed lists | **Keep the first copy.** The 7 pairs hold the same crew in a different order. (from the outputs) |
| C07 | What is the tie-break when `vote_count` is equal? | First copy in the file | **First copy in the file** (chosen by me) |
| C12 | How do I handle the 59 movies with a shared `tmdbId`? | Exclude and flag until resolved | **Exclude and flag until resolved** (chosen by me) |
| C18 | What is the budget threshold? | 1,000 | **1,000** (chosen by me) |
| C19 | What is the revenue threshold? | Decide after counting | **1,000, with 1,000 to 10,000 flagged.** 155 values below 1,000, 16 of them next to a real budget. (from the outputs) |
| C22 | Do I treat all `vote_average` 0 as missing? | Yes (2,998 movies) | **Yes** (chosen by me) |
---

## 10. What this list deliberately does not do

- **No capping** of long runtimes.
- **No default** of unknown spoken languages to English.
- **No filling** of missing budget, revenue or runtime with averages.
- **No dropping** of movies only because a field is missing.
- **No mixing** of the small and full ratings files.

---

## 11. Remaining work (does not block this list)

1. Review the 2 genuine IMDb conflicts and resolve the 59 shared-`tmdbId` movies (C12, C17).
2. Confirm or change the three remaining AI proposals: C17 (flag IMDb conflicts), C28 (leave out `homepage` and `poster_path`), and C30 (keep `popularity` and `video` as low priority).