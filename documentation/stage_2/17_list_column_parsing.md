# Stage 2 — Parsing the List-Like Text Columns (C26)

## 1. Purpose

A column such as `genres` looks like a list but is really one long piece of text:

```text
"[{'id': 16, 'name': 'Animation'}, {'id': 35, 'name': 'Comedy'}]"
```

Text cannot be counted, grouped or searched by genre. This step turns it into real Python lists and dictionaries.

Functions: `parse_literal_column()` and `parse_list_columns()` in `stage2_clean_metadata.py`.

## 2. Which columns

| Column | Becomes | Empty or missing means |
|---|---|---|
| `genres` | list of dictionaries | `[]` = unknown (C24) |
| `production_companies` | list of dictionaries | `[]` = unknown |
| `production_countries` | list of dictionaries | `[]` = unknown |
| `spoken_languages` | list of dictionaries | `[]` = unknown, never filled in as English |
| `belongs_to_collection` | one dictionary | missing = the movie is not in a collection |

The other three Python-style columns, `cast`, `crew` and `keywords`, are in other tables and use the same function in Phase C.

## 3. Two rules from the cleaning decisions

- **Use `ast.literal_eval`, not `json.loads`.** The text uses Python-style single quotes, which the JSON reader rejects. `literal_eval` reads Python literals (lists, dictionaries, numbers, text) and nothing else, so it is safe, unlike `eval`.
- **A successful parse proves only the syntax.** The text `'5'` parses fine into a number. So after parsing, every result is checked to be a list (or a dictionary for the collection). In Stage 1, 3 cells parsed into the wrong type. They were in the broken records.

## 4. The code

```python
import ast

LIST_COLUMNS = ["genres", "production_companies", "production_countries", "spoken_languages"]
DICT_COLUMNS = ["belongs_to_collection"]


def parse_literal_column(series, expected_type, column_name):
    """Turn Python-style text into real lists/dicts, and check each result's type."""

    def parse_cell(value):
        if pd.isna(value):
            return None

        try:
            parsed = ast.literal_eval(value)
        except (ValueError, SyntaxError):
            raise ValueError(f"{column_name}: cannot parse {str(value)[:80]!r}")

        if not isinstance(parsed, expected_type):
            raise ValueError(
                f"{column_name}: expected {expected_type.__name__}, "
                f"got {type(parsed).__name__} for {str(value)[:80]!r}"
            )
        return parsed

    return series.apply(parse_cell)


def parse_list_columns(meta):
    meta = meta.copy()

    for column in LIST_COLUMNS:
        meta[column] = parse_literal_column(meta[column], list, column)

    for column in DICT_COLUMNS:
        meta[column] = parse_literal_column(meta[column], dict, column)

    return meta
```

How it works:

- `parse_cell` is a helper inside the function. `series.apply(parse_cell)` runs it on every cell.
- A genuinely missing cell stays missing, so the movies with no collection are "no collection", not an empty dictionary.
- Empty lists stay as empty lists. C24 says to keep them and treat them as unknown during analysis, not to delete them.
- Either failure raises an error showing the first 80 characters of the culprit, so the pipeline stops instead of continuing quietly.
- `parse_literal_column` is reusable for `cast`, `crew` and `keywords`.

## 5. The cleaning wrapper

All five metadata steps now run through one function, in order:

```python
def clean_movies_metadata(meta):
    meta = repair_split_records(meta)
    meta = remove_duplicate_movies(meta)
    meta = fix_data_types(meta)
    meta = clean_placeholders(meta)
    meta = parse_list_columns(meta)
    return meta
```

## 6. Testing and verification

Check script: `tests/check_parsing.py`. The parse ran with no errors, which also proves that the 3 wrong-type cells from Stage 1 are gone.

Empty lists compared with Stage 1 (small drops come from the removed duplicates):

| Column | Stage 1 (raw) | Now |
|---|---:|---:|
| `genres` | 2,442 | 2,442 |
| `production_companies` | 11,875 | 11,868 |
| `production_countries` | 6,282 | 6,279 |
| `spoken_languages` | 3,829 | 3,827 |

Other results:

- 4,488 movies belong to a collection.
- Toy Story's genres are Animation, Comedy and Family, and its collection is "Toy Story Collection".

## 7. Result

**The five list-like metadata columns are real lists and dictionaries.** The row count is still 45,433.

**Phase B is complete.** `movies_metadata` is fully cleaned in memory: repaired, de-duplicated, typed, placeholders handled and lists parsed. It is not saved yet. Saving is the Load step, after the other tables are cleaned.
