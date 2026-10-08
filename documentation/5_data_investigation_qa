# Stage 1 Data Understanding: Questions and Answers

**Project:** Movie Intelligence
**Stage:** 1, Understand the Raw Data
**Format:** each question is followed by its answer and the reasoning behind it. The overall findings are at the end.
**Companion document:** `4_metadata_summary.md` (the full data-quality report with every number).

---

## Contents

1. [Question 1: Duplicated ids](#question-1-duplicated-ids)
2. [Question 2: Malformed metadata rows](#question-2-malformed-metadata-rows)
3. [Question 3: Hidden missing values](#question-3-hidden-missing-values)
4. [Question 4: The id system and joins](#question-4-the-id-system-and-joins)
5. [Question 5: IMDb ids, the small files, and plausibility](#question-5-imdb-ids-the-small-files-and-plausibility)
6. [Overall findings](#overall-findings)

---

## Question 1: Duplicated ids

**Evidence from the notebook:**

| Table | Rows | Extra copies of an id | Ids that repeat | Copies identical | Copies differ | Fully duplicated rows |
|---|---:|---:|---:|---:|---:|---:|
| credits | 45,476 | 44 | 43 | 36 | 7 | 37 |
| keywords | 46,419 | 987 | 985 | 985 | 0 | 987 |
| movies_metadata | 45,466 | 30 | 29 | 16 | 13 | 17 |

### Q1.1: What kind of duplication is it in each table, and what would you do about it?

**Answer**

| Table | What the duplication is | Action |
|---|---|---|
| keywords | 985 ids repeat and **all** copies are identical. Pure redundancy. | Keep one copy, drop the rest. |
| credits | 36 ids are identical copies. **7 ids conflict.** | Drop identical extras. Inspect the 7 and decide which copy wins. |
| movies_metadata | 16 ids are identical copies. **13 ids conflict.** | Drop identical extras. Inspect the 13 and decide which copy wins. |

**Reasoning**
- The question to ask is *what does the repeated thing represent?* A keyword such as "love" appearing in many movies' lists is normal. But what the `keywords` table repeats is the **movie id** itself: the same movie sits in the table twice. A movie cannot be in the table twice, so this is redundancy.
- Two kinds of repeated id need two different actions. Identical copies are harmless. Conflicting copies need a human decision, because dropping the wrong one loses correct data.

> **Your first answer:** *Needs work.* You described keywords duplication as acceptable because a keyword can belong to many movies. That mixes up two levels: values inside a list, versus rows in the table.

### Q1.2: Which table's duplicates worry you most, and why?

**Answer:** `movies_metadata` is the table to clean most carefully, because it is the central table that everything else joins to. But **any table you will join** matters, because duplicate ids silently multiply rows.

**Reasoning**
- Join metadata to a table in which one id appears twice, and that movie appears twice in the result. No error is raised, and later totals and averages count it twice.
- "Keywords might not be important" is a claim you can check against `2_project_scope.md` and `3_main_analytical_questions.md`. Table importance should be decided from the project questions, not from a hunch.

> **Your first answer:** *Needs work.* Right instinct about metadata, but the strongest reason (silent row multiplication) was missing.

### Q1.3: Why do "fully duplicated rows" and "extra copies of an id" match in keywords but not in credits or meta?

**Answer:** The gap between them equals the number of ids whose copies disagree.

| Table | Extra copies | Fully duplicated rows | Gap | Copies differ |
|---|---:|---:|---:|---:|
| credits | 44 | 37 | 7 | 7 |
| keywords | 987 | 987 | 0 | 0 |
| movies_metadata | 30 | 17 | 13 | 13 |

**Reasoning**
- Rows that repeat an id **and** match in every column are counted as "fully duplicated". Rows that repeat an id but differ somewhere are counted only as extra copies.
- In keywords every repeat is an exact copy, so the two counts are equal. In credits and metadata, the leftover rows are the ones whose content conflicts.

**What each column means** (worked example: credits, 45,476 rows)

| Column | Meaning | Credits value |
|---|---|---:|
| Extra copies of an id | Rows beyond the first for each id (rows minus unique ids) | 45,476 − 45,432 = 44 |
| Ids that repeat | Distinct ids that appear more than once | 43 |
| Copies identical | Of those ids, how many have every column the same | 36 |
| Copies differ | Of those ids, how many have at least one column different | 7 |
| Fully duplicated rows | Rows identical in every column to an earlier row | 37 |

Two relationships to remember: identical + differ = ids that repeat (36 + 7 = 43), and when extra copies exceed ids that repeat, some id appears three or more times (44 vs 43 means one id appears three times).

> **Your answer (carry-over):** *Correct.* You said keywords copies are identical and can be dropped, while credits and metadata contain rows that must be viewed or fixed.

---

## Question 2: Malformed metadata rows

**Evidence from the notebook:** 3 rows have a non-numeric `id`. In them, the `id` column holds `1997-08-20`, the `adult` column holds text such as `- Written by Ørnås`, `belongs_to_collection` holds `0.065736`, and `budget` holds `/ff9qCepilowshEtG2GYWwzt2bs4.jpg`. The row just before each one is mostly empty.

### Q2.1: What happened to these rows?

**Answer:** Each movie's record was broken into **two physical rows**, and the second row's values are shifted **9 columns to the left**.

**Reasoning**
- Each stray value belongs to a different, specific column: the date is a `release_date`, the `.jpg` is a `poster_path`, the text is the end of an `overview`, the decimal is a `popularity`.
- They appear in their original order. That points to a record that was split, not random corruption.
- The shift is exactly 9: the `adult` position (column 0) holds `overview`-tail text, which sits at original position 9.

> **Your first answer:** *Needs work.* You matched the stray values to the correct columns, but the cause you gave ("a scraping error that lost the data") was a guess, and your own Q2.2 answer contradicted it.

### Q2.2: What do you notice about the row just before each bad row?

**Answer:** It is a **stub**: the first columns (including the real id) are filled and the rest is empty. The stub and the bad row are two halves of **one movie**.

**Reasoning**
- The stubs have real ids: 82663 (row 19,729), 122662 (row 29,502), and 249260 (row 35,586). The id was never lost; it sits in the stub.
- The bad row's `release_date` column holds a small number (`1`, `12`). Original position 14 + the 9-column shift = position 23, which is `vote_count`. That matches.
- Always test a hypothesis against your other findings. Your Q2.1 theory said the id data was missing; the stub shows it is not.

> **Your answer:** *Correct.* This was your best answer and the real explanation.

### Q2.3: How does this one problem explain `id` being a string, `adult` having 5 values, and `popularity` being `object`?

**Answer:** Pandas assigns **one dtype to the whole column**. A single value that cannot be parsed forces the entire column to a more general type (text or `object`).

| Symptom | Cause |
|---|---|
| `id` is a string | 3 date values in the id column |
| `adult` has 5 unique values | 2 legitimate (False 45,454, True 9) + 3 corrupted text values |
| `budget` has 3 non-numeric strings | The 3 corrupted rows |
| `popularity` is `object` | Non-numeric values from the corrupted rows |
| `video` is `object` | **A different cause:** the column holds True/False plus NaN (6), not corruption |

**Reasoning:** two different causes can produce the same symptom. Do not assume one explanation covers every oddity.

> **Your first answer:** *Needs work.* You named the type problems but not the mechanism.

### Q2.4: Repair or drop?

**Answer:** Either is defensible. The real decision rule is: **treat each stub plus its tail as one unit.**

| Option | Argument |
|---|---|
| Drop | 3 records out of 45,466 is about 0.007%. Repairs are manual and could introduce errors. |
| Repair | Only 3 movies, so a careful fix is cheap and keeps real data. |

**Reasoning**
- This is **6 physical rows but 3 logical records.** Dropping only the 3 bad-id rows leaves 3 ghost stubs (an id with no title, date, or status).
- Whatever is chosen goes into the cleaning-decisions list with the row numbers and the reason.
- **Your pick:** repair if possible, otherwise drop. Acceptable. The decision is not yet logged.

> **Your first answer:** *Needs work.* One-sided argument, and the stub consequence was missing.

---

## Question 3: Hidden missing values

**Evidence from the notebook:**

| Field | Hidden value | Count | % of rows |
|---|---|---:|---:|
| credits.cast | `'[]'` | 2,418 | 5.32 |
| credits.crew | `'[]'` | 771 | 1.70 |
| keywords.keywords | `'[]'` | 14,795 | 31.87 |
| meta.genres | `'[]'` | 2,442 | 5.37 |
| meta.production_companies | `'[]'` | 11,875 | 26.12 |
| meta.production_countries | `'[]'` | 6,282 | 13.82 |
| meta.spoken_languages | `'[]'` | 3,829 | 8.42 |
| meta.budget | `0` | 36,573 | 80.44 |
| meta.revenue | `0` | 38,052 | 83.69 |
| meta.runtime | `0` | 1,558 | 3.43 |
| meta.vote_count | `0` | 2,899 | 6.38 |

### Q3.1: What do the budget and revenue percentages tell you about what a `0` means?

**Answer:** Budget is `0` for **80.44%** of movies and revenue for **83.69%**. A zero here means **unknown**, not "free" or "earned nothing".

**Reasoning**
- No real film is made for a budget of 0, so a zero is a placeholder for "no data".
- The 3 non-numeric budget values are the corrupted rows from Question 2.

> **Your answer:** *Correct.*

### Q3.2: For each field, is the empty or zero value real information, or a placeholder for unknown?

**Answer**

| Field | Reading | Why |
|---|---|---|
| cast, crew | Unknown | Every real film has people who made it |
| keywords `'[]'` | Unknown **or** never tagged | "Never tagged" is not the same as "unknown" |
| genres, production companies, production countries `'[]'` | Mostly unknown | Every film has a genre and was made by someone |
| spoken_languages `'[]'` | Unknown **or genuinely none** | A silent film has no spoken language |
| budget, revenue, runtime zero | Unknown | A film cannot cost 0 or run 0 minutes |

**Reasoning**
- Do **not** fill unknown spoken languages with English. That invents data and would mislabel every non-English film among the 3,829 rows. Use the evidence in `original_language` instead.
- `runtime` (1,558 zeros, 4.01% unknown including the 263 NaN) passes the same test as budget.

> **Your first answer:** *Needs work.* You treated every `'[]'` as "data exists but is missing", and the English default is the clearest error.

### Q3.3: What goes wrong if you compute average budget or ROI without handling the zeros?

**Answer:** The results are distorted, and the distortion has a specific direction and mechanism.

**Reasoning**
- **Average budget:** 36,573 zeros pull the mean far **down**, and the average describes the unknown rather than the real movies.
- **ROI (revenue ÷ budget):** a budget of 0 produces infinity, and 0 ÷ 0 produces NaN. Where only one of the two is zero, the ratio is misleading rather than an error.
- The number that matters is **how many movies have both budget and revenue above 0**. That is the usable sample for any financial analysis, and it is probably much smaller than 45,466. (Count still to verify.)
- Also check the smallest positive budgets. A budget of 7 is probably not 7 dollars.

> **Your first answer:** *Needs work.* Right direction, but no mechanism and no numbers.

### Q3.4: Should `vote_count = 0` (2,899 rows) get the same treatment as budget?

**Answer:** No. A zero vote count is a **real observation**: nobody voted.

**Reasoning**
- A zero budget is physically impossible, so it signals missing data. A zero vote count is plausible.
- One extension to check: look at `vote_average` for those same 2,899 rows. If a movie has no votes, whatever its average holds is a placeholder rather than a real rating.

> **Your answer:** *Correct.*

---

## Question 4: The id system and joins

**Evidence from the notebook:**

| Comparison | In both | Only left | Only right |
|---|---:|---:|---:|
| meta.id vs credits.id | 45,432 | 1 | 0 |
| meta.id vs keywords.id | 45,432 | 1 | 0 |
| credits.id vs keywords.id | 45,432 | 0 | 0 |
| meta.id vs links.tmdbId | 45,433 | 0 | 161 |
| ratings.movieId vs links.movieId | 45,115 | 0 | 728 |
| ratings.movieId vs meta.id | 7,565 | 37,550 | 37,868 |

### Q4.0: Interpret the bridge test (one movie followed through the system)

Output of the test:

```
movieId  imdbId  tmdbId
      1  114709   862.0     <- links row for MovieLens id 1
id   title
862  Toy Story               <- meta, looked up through the bridge (tmdbId 862)
Empty DataFrame              <- meta, looked up with id 1 directly
```

**Answer:** One movie has **two different numbers**. To `ratings`, Toy Story is `1`. To `meta`, `credits` and `keywords`, it is `862`. Metadata has no movie with id `1` at all. The two systems are separate numberings that sometimes share digits.

**Reasoning**
- `links` is the only table that has both numbers side by side, so it is the translator.
- `862.0` is a float only because the `tmdbId` column contains missing values.

### Q4.1: Which id system does each table use?

**Answer**

| System | Tables and columns |
|---|---|
| **TMDB ids** | `meta.id`, `credits.id`, `keywords.id`, `links.tmdbId` |
| **MovieLens ids** | `ratings.movieId`, `links.movieId` |
| IMDb ids (a third system) | `meta.imdb_id`, `links.imdbId` |

### Q4.2: Why is the last row of the join table so low, and what goes wrong with a direct join?

**Answer:** Joining `ratings.movieId` to `meta.id` mixes two unrelated numberings. Two things go wrong, and **neither raises an error**:
- **Lost data:** 37,550 of 45,115 rated movies (83.2%) match nothing.
- **Wrong data:** the 7,565 matches are coincidences of digits. MovieLens id 862 is a different film from TMDB 862, but the join would attach its ratings to Toy Story.

**Reasoning:** wrong numbers look exactly like right numbers, which makes this worse than lost rows.

> **Your first answer:** *Half right.* You sensed the ids might not map directly, which is the key idea. The silent wrong matches were the part you missed.

### Q4.3: What chain of joins attaches a rating to a metadata movie, and how much is lost?

**Answer:** `ratings.movieId` → `links.movieId` → `links.tmdbId` → `meta.id`

**Reasoning**
- Two losses are possible along this chain: the **219** `links` rows with no `tmdbId`, and the **161** `tmdbId` values not present in metadata.
- The exact count of rated movies that can be reached is **still to be measured**. It is at most 45,115 minus those losses, applied only to rated movies.

### Q4.4: Which of the three `links` problems is the most dangerous, even though it is the smallest?

**Answer:** The **30 repeated `tmdbId` values**.

| Problem | Count | Effect on a join | Visible? |
|---|---:|---|---|
| Missing `tmdbId` | 219 | Rows drop out | Yes, countable |
| `tmdbId` not in metadata | 161 | Rows drop out | Yes, countable |
| Repeated `tmdbId` | 30 | Rows **multiply or merge** | **No, silent** |

**Reasoning**
- Two MovieLens movies sharing one TMDB id get their ratings pooled onto one metadata movie. In the other direction, one metadata movie matches two `movieId` values, its row appears twice, and totals are counted double.
- `meta.id` has its own 30 extra copies, which cause the same fan-out.
- **Rule: after every join, compare the row count with what you expected.**

### Q4.5: Which `meta` movie is missing from `credits` and `keywords`? (take-home)

**Answer:** Not yet answered. `meta` has 45,433 unique numeric ids and `credits` and `keywords` each have 45,432, so exactly one metadata id is absent. It may relate to the malformed records from Question 2.

---

## Question 5: IMDb ids, the small files, and plausibility

### Q5.1: What if you joined the raw IMDb columns? Which key would you trust between `meta` and `links`?

**Evidence:** `meta.imdb_id` looks like `tt0114709`; `links.imdbId` looks like `114709`. After rebuilding the `tt` plus 7-digit form: 45,353 match, 64 only in meta, 490 only in links.

**Answer, part a (the raw join):** **Every** row fails to match, because `'tt0114709'` never equals `114709`. A pandas `merge` on a string against an integer column raises an error. A set-based overlap check reports **0 matches** with no warning. The silent version is the dangerous one, which is why formats and dtypes are checked before every join.

**Answer, part b (which key):** TMDB is the **backbone key**, and IMDb is a cross-check.

| Key | Meta side | Links side | Meta movies with no match |
|---|---|---|---:|
| TMDB (`id` vs `tmdbId`) | 0 missing, 30 extra copies | 219 missing, 30 repeats | 0 |
| IMDb (`imdb_id` vs `imdbId`) | 17 missing, 32 repeats | 0 missing, 0 repeats | 64 |

**Reasoning**
- `links.imdbId` is perfect on its own side, but a join needs **both** sides, and `meta.imdb_id` has gaps and repeats.
- `credits` and `keywords` carry only the TMDB id.
- "More reliable" is a claim to test. Whether the TMDB path and the IMDb path land on the **same movie** is still to be checked.

> **Your first answer:** *Needs work* on both parts. "Some values lost" understates the failure, and the choice of IMDb needed the scoreboard to support it.

### Q5.2: Are the `_small` files samples of the full files, and what do you do with them?

**Evidence**

| Check | Result |
|---|---|
| `links_small.movieId` ⊆ `links.movieId` | **False** |
| `ratings_small.movieId` ⊆ `links_small.movieId` | True |
| `ratings_small` rows found in `ratings` | **0 of 100,004** |

**Answer:** No. The small files are **not samples** of the full files. The recommendation is to treat the **full files as the source of truth** and not mix them with the small ones.

**Reasoning**
- "They contain data missing from the main files" is an untested hypothesis. The risky possibility is that the **same `movieId` points to different movies** in the two files, which would corrupt any mixed join silently.
- Check `2_project_scope.md` in case it says otherwise.

> **Your first answer:** *Needs work.* You correctly saw they are not subsets, but the "contains missing data" claim was untested and you did not say what to do with them.

### Q5.3: Plausibility calls: timestamps, runtime zeros, and a runtime cap

**Answer**

| Item | Verdict |
|---|---|
| Rating timestamps (1995-01-09 to 2017-08-04) | Trust. The range matches the dataset's age. Convert from Unix seconds to datetime. |
| Runtime zeros | Unknown. Treat as missing (1,558 zeros, 1,821 unknown with NaN, 4.01%). |
| Capping runtime at 180 or 240 minutes | **Wrong.** Do not overwrite values. |

**Reasoning**
- A runtime of 240 is not the longest real film, and replacing 1,256 with 240 **invents data**. That is the same objection as defaulting a language to English.
- The correct process: look at rows above a threshold (say 300 minutes), judge whether the titles are plausible, then **flag or exclude** them for specific analyses. Never silently change them.

> **Your answers:** timestamps *Correct* (your reasoning used the dataset's age), runtime zeros *Correct*, capping *Wrong*.

---

## Overall findings

### 1. The two id systems

```
TMDB ids                                         MovieLens ids
movies_metadata.id  --  credits.id               ratings.movieId
                    --  keywords.id                    |
links.tmdbId  <----------- links ------------>  links.movieId
                              |
                          links.imdbId  (IMDb ids, a third system)
```

Correct join chain: `ratings.movieId` → `links.movieId` → `links.tmdbId` → `movies_metadata.id`.

### 2. What cannot be joined reliably

| Problem | Count | Consequence |
|---|---:|---|
| Direct join `ratings` to `meta` | 37,550 rated movies unmatched, 7,565 coincidental matches | Lost and wrong data, no error |
| `links` rows with no `tmdbId` | 219 | Rated movies unreachable in metadata |
| `links.tmdbId` not in metadata | 161 | Same |
| Repeated `links.tmdbId` | 30 | Rows multiply or merge silently |
| `meta` ids missing from `credits` and `keywords` | 1 | One movie has no cast or keywords |
| `meta.imdb_id` not found in `links` | 64 | IMDb path is incomplete |

### 3. Data problems and the proposed response

| Problem | Count | Proposed action | Status |
|---|---:|---|---|
| Keywords duplicate rows (identical) | 985 ids | Drop extra copies | Proposed |
| Credits and metadata duplicate ids (identical) | 36 and 16 | Drop extra copies | Proposed |
| Credits and metadata duplicate ids (conflicting) | 7 and 13 | Inspect, then decide which copy wins | To investigate |
| Split metadata records | 3 records (6 rows) | Repair or drop, always as stub plus tail | Decision pending |
| Budget and revenue zeros | 80.44% and 83.69% | Treat as unknown (NaN) | Proposed |
| Runtime zeros | 1,558 | Treat as unknown, flag high values, never cap | Proposed |
| Empty-list fields | up to 31.87% | Treat as unknown or none, depending on the field | Proposed |
| IMDb id format mismatch | all rows | Normalise to `tt` plus 7 digits | Proposed |
| `homepage` stale | 82.88% missing, rest outdated | Ignore the field | Proposed |
| `_small` files | n/a | Use full files as the source of truth | Proposed |

### 4. Fields to trust, transform, or ignore (summary)

- **Trust:** `title`, `original_title`, `overview`, `original_language`, `rating`, `userId`.
- **Transform:** every list or dict field (parse), `id`, `imdb_id`, `release_date`, `status`, `adult`, `video`, `popularity`, `budget`, `revenue`, `vote_count`, `timestamp`.
- **Investigate:** `runtime` (high values), `vote_average` (zeros), the `_small` files.
- **Ignore:** `homepage`, `poster_path`.

### 5. Lessons about method (for the next stages)

1. **State a claim, test it, then record what you found.** "I checked, and found X" beats "I think X". Three claims in this stage were untested guesses that the data later corrected: IMDb is more reliable, the small files contain missing data, and runtime should be capped.
2. **Joins fail silently.** Check id systems, formats, and dtypes before joining, then check row counts after.
3. **Pandas' missing counts are a floor, not the truth.** Look for placeholders such as `'[]'` and `0`.
4. **Duplicates must be judged at row and key level**, not per column.
5. **Do not fill gaps with a plausible default or a cap.** Flag, exclude, or use a second source of evidence.

### 6. Self-assessment by question

| Question | Parts | Result |
|---|---|---|
| Q1 Duplicates | 1.1 Needs work, 1.2 Needs work, 1.3 Correct (after review) | Concept understood, evidence use needs practice |
| Q2 Malformed rows | 2.1 Needs work, 2.2 Correct, 2.3 Needs work, 2.4 Needs work | Strong observation, weaker on mechanism |
| Q3 Hidden missing | 3.1 Correct, 3.2 Needs work, 3.3 Needs work, 3.4 Correct | Good instincts on what a zero means |
| Q4 Ids and joins | Taught, then interpreted | Core idea now clear |
| Q5 IMDb, small files, plausibility | 5.1 Needs work, 5.2 Needs work, 5.3 timestamps and zeros Correct, cap Wrong | Test claims before stating them |

### 7. Still to do before Stage 1 is closed

1. Count rated movies reachable through the bridge (and the percentage lost).
2. Identify the one `meta` id missing from `credits` and `keywords`.
3. Check whether the TMDB path and the IMDb path agree on the same movie.
4. Check whether shared `movieId` values in `links` and `links_small` point to the same `tmdbId`.
5. Inspect `runtime` values above 300 and the conflicting duplicate ids.
6. Write the data dictionary, cleaning-decisions list, and relationship diagram (the data-quality report is in `4_metadata_summary.md`).

**Milestone check:** can you explain the two id systems and the join chain without opening the notebook? If yes, Stage 1 is complete.