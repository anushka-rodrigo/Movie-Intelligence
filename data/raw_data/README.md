# Raw Data

This folder holds the original, **unmodified** Kaggle files. They are not stored in the repository because of their size (`ratings.csv` alone is roughly 700 MB).

## How to get the data

1. Download from Kaggle: https://www.kaggle.com/datasets/rounakbanik/the-movies-dataset
2. Unzip and place the CSV files in this folder (`data/raw_data/`).
3. Never edit these files. All cleaning happens in the ETL pipeline, and cleaned output goes to `data/processed/`.

## Files

| File | Approx. size | Description |
|---|---|---|
| `movies_metadata.csv` | ~34 MB | Main table of about 45k movies: budget, revenue, genres, release date, runtime, language, production companies and countries, overview, popularity, vote average and count |
| `credits.csv` | ~190 MB | Cast and crew for each movie, stored as stringified lists of dictionaries |
| `keywords.csv` | ~6 MB | Plot keywords for each movie, stored as stringified lists of dictionaries |
| `links.csv` | ~2 MB | Maps MovieLens IDs to IMDb and TMDB IDs |
| `links_small.csv` | <1 MB | Links for the movies covered by `ratings_small.csv` |
| `ratings.csv` | ~700 MB | About 26 million ratings from 270,000+ users |
| `ratings_small.csv` | ~2 MB | A 100k-rating subset, used for fast development and testing |

*Sizes are approximate. Check your local copies.*

## Columns

**movies_metadata.csv:** `adult`, `belongs_to_collection`, `budget`, `genres`, `homepage`, `id`, `imdb_id`, `original_language`, `original_title`, `overview`, `popularity`, `poster_path`, `production_companies`, `production_countries`, `release_date`, `revenue`, `runtime`, `spoken_languages`, `status`, `tagline`, `title`, `video`, `vote_average`, `vote_count`

**credits.csv:** `cast`, `crew`, `id`

**keywords.csv:** `id`, `keywords`

**links.csv / links_small.csv:** `movieId`, `imdbId`, `tmdbId`

**ratings.csv / ratings_small.csv:** `userId`, `movieId`, `rating`, `timestamp`

## How the files relate

```
movies_metadata.id  ──  credits.id
                    ──  keywords.id
                    ──  links.tmdbId ── links.movieId ── ratings.movieId
```

- `movies_metadata`, `credits` and `keywords` share the **TMDB ID** (`id`).
- `ratings` uses the **MovieLens ID** (`movieId`). To connect ratings to movie metadata, go through `links` (`movieId` → `tmdbId` → `id`).
- Movies to ratings is one-to-many, and so is movies to cast and crew.

## Known issues (to confirm in Stage 1)

- `budget` and `revenue` often contain `0`, which usually means missing, not a true zero.
- A few rows in `movies_metadata.csv` are malformed (shifted columns or invalid IDs).
- Duplicate movie IDs may exist.
- `genres`, `cast`, `crew`, `keywords` and similar columns are stringified JSON-like lists that need parsing.
- Some columns have mixed types (for example `budget` stored as text).
- Some `links.tmdbId` values are missing, so those ratings cannot be joined to movie metadata.