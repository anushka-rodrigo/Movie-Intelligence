# Stage 2 — Building the Final Tables (Step 14)

## 1. Purpose

Document 22 decided the shape of the processed data: sixteen tables, each with one grain. This step builds them from the cleaned tables and checks each one.

The script is:

```text
src/scripts/stage2_modules/stage2_build_tables.py
```

The functions are tested on their own. They are not yet connected to the main pipeline, which happens together with the join step and the Load step.

## 2. The reusable pieces

### Exploding a list column

```python
def explode_entries(table, id_column, list_column):
    """One row per list entry: the movie id, plus the fields of each dictionary."""
    exploded = table[[id_column, list_column]].explode(list_column)
    exploded = exploded.dropna(subset=[list_column]).reset_index(drop=True)

    entries = pd.DataFrame(exploded[list_column].tolist())
    entries.insert(0, id_column, exploded[id_column])
    return entries
```

- `explode` gives one row per list item. A movie with an empty or missing list becomes one empty row, which is removed. Movies with no entries therefore do not appear in link tables.
- `pd.DataFrame(list_of_dicts)` turns the dictionaries into columns.

### Splitting into a lookup table and a link table

`build_lookup_and_link()` is one function for every list-of-dictionaries column. The differences between tables are passed in as arguments: the list column, the dictionary field that identifies an entry, and the output column names.

It runs three checks, and any failure stops the pipeline:

1. **Nothing lost or invented:** the number of entries equals the total list length before splitting.
2. **One name per key:** each id maps to exactly one name.
3. **No repeated pairs:** a movie cannot list the same entry twice.

The result is a lookup table (one row per entry) and a link table (one row per movie-entry pair).

## 3. Results for the list columns

| Source | Lookup table | Lookup rows | Link rows | Movies covered |
|---|---|---:|---:|---:|
| `genres` | `genres` | 20 | 91,015 | 42,991 |
| `production_companies` | `production_companies` | 23,693 | 70,476 | 33,565 |
| `production_countries` | `production_countries` | 161 | 49,375 | 39,154 |
| `spoken_languages` | `spoken_languages` | 133 | 53,269 | 41,606 |
| `keywords` | `keywords` | 19,956 | 156,602 | 31,092 |

Each "movies covered" figure equals the number of movies minus the movies with an empty list, so the test checks itself. All three checks passed on every table.

Notes:

- Genres were built first and used to design the generic function. After the refactor, genres gave identical results (20 rows, 91,015 link rows), which showed that the refactor changed nothing.
- Language names are stored in their own language ("Français", "Deutsch"). The two-letter `language_code` is the stable key.
- The keywords table is built from the cleaned `keywords` table, which is already keyed by movie, so it uses the same function with no changes.

## 4. People, cast and crew

Cast and crew have different fields and share one table of people, so they were investigated before being built (`tests/explore_people.py`).

### What the investigation found

| Question | Answer |
|---|---|
| Cast fields | `cast_id`, `character`, `credit_id`, `gender`, `id`, `name`, `order`, `profile_path` |
| Crew fields | `credit_id`, `department`, `gender`, `id`, `job`, `name`, `profile_path` |
| Is `credit_id` unique? | Yes, no repeats in cast or crew, so it is the key of both credit tables |
| Entries | 562,044 cast and 463,836 crew |
| Distinct people | 353,343 |
| Ids with two names | 15 (the same person in two spellings, for example Morris Chestnut and Моррис Честнат) |
| Ids with two gender values | 12 |
| Gender `0` | 495,797 of 1,025,880 entries (48%) |

### Rules

1. **Name conflicts:** prefer a spelling that uses only plain Latin letters. If several qualify, the first appearance wins. The 15 ids are logged.
2. **`gender` stays on each credit row, not in `people`.** The source records it per credit, and 12 people disagree with themselves across credits.
3. **Gender `0` becomes missing.** It is TMDB's code for "not specified" (1 = female, 2 = male).
4. **Dropped:** `profile_path` and `cast_id`. The `credit_id` already identifies each credit.

### A rule that had to be corrected

The first version kept the first appearance for every person. The test output showed that for two of the 15 people this picked the Russian spelling, because it came first in the file. The rule was changed to prefer a Latin-alphabet spelling. After the change, all 15 outcomes were checked by eye and every one was the English spelling (for example Morris Chestnut, Erika Eleniak, Jason Momoa).

```python
people_entries["_ascii"] = people_entries["name"].apply(lambda name: name.isascii())

people = (
    people_entries.sort_values(["person_id", "_ascii"], ascending=[True, False])
    .drop_duplicates(subset="person_id", keep="first")
    .drop(columns="_ascii")
    .reset_index(drop=True)
)
```

The rule is simple, not perfect. A person whose two spellings are "Penélope Cruz" and "Penelope Cruz" would get the second. With 15 people out of 353,343 affected, this was judged acceptable.

### Results

| Check | Expected | Result |
|---|---|---|
| People | 353,343 | 353,343 |
| Cast credits | 562,044 | 562,044 |
| Crew credits | 463,836 | 463,836 |
| Movies with cast | 43,018 | 43,018 |
| Movies with crew | 44,661 | 44,661 |
| Missing gender | 495,797 | 495,797 |
| Toy Story | Tom Hanks, Tim Allen, Don Rickles, director John Lasseter | Correct |

The missing-gender count equals exactly the number of zeros found in the investigation, which proves the conversion lost and invented nothing.

## 5. The core tables

Three tables already have the right grain. They only needed the agreed names and the unwanted columns removed.

| Table | Changes |
|---|---|
| `movies` | `id` becomes `movie_id`. The four list columns are removed (they have their own tables). `homepage` and `poster_path` are dropped (C28). `belongs_to_collection` becomes `collection_id` and `collection_name`. |
| `movie_links` | `movieId` becomes `movielens_id`, `tmdbId` becomes `movie_id`, `imdbId` becomes `imdb_id`. The `shared_tmdb_id` flag stays. |
| `ratings` | `userId` becomes `user_id`, `movieId` becomes `movielens_id`. |

The naming enforces the Stage 1 warning (C09): `movie_id` is always the TMDB id and `movielens_id` is always the MovieLens id. Because the names differ, joining ratings straight to movies cannot be typed by accident.

A movie belongs to at most one collection, so the collection stays as two plain columns. A check confirms that each `collection_id` has exactly one name.

| Check | Expected | Result |
|---|---|---|
| `movies` | 45,433 rows, 23 columns | 45,433 rows, 23 columns |
| Movies in a collection | 4,488 | 4,488 |
| Toy Story collection | Toy Story Collection | Toy Story Collection (id 10194) |
| `movie_links` | 45,624 rows | 45,624 rows |
| `ratings` | 26,024,289 rows | 26,024,289 rows |

The `ratings` function only renames columns. Its one check is a guard that no TMDB `movie_id` column is present. The expensive uniqueness check on (`user_id`, `movielens_id`) is left for the Validate phase.

## 6. Result

**All sixteen tables can now be built from the cleaned data, and every table has passed its checks.** Each table has a declared grain and a key, no list columns remain, and the naming rule protects the join between ratings and movies.

The next step connects the tables: the join from ratings to movies through `movie_links`, the exclusions for C11 and C12, and the `imdb_conflict` flag (C17).
