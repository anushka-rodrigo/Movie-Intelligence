# Stage 2 — Cleaning the Credits Table (C04, C05, C26)

## 1. Purpose

The `credits` table has the same two problems already solved in `movies_metadata`:

1. **Duplicate ids.** 45,476 rows should be 45,432, so 44 rows are extra copies.
2. **Text instead of lists.** `cast` and `crew` are Python-style text, not real lists.

This step removes the duplicates and parses both columns.

The scripts are:

```text
src/scripts/stage2_modules/stage2_helpers.py
src/scripts/stage2_modules/stage2_clean_credits.py
```

## 2. What was wrong

From the Stage 1 investigation:

- 43 ids appear more than once.
- 36 of them have identical copies (C04).
- 7 of them (4912, 69234, 99080, 110428, 132641, 159849, 298721) look different because their `crew` text differs. Parsing and comparing them showed that both copies hold exactly the same crew members, just in a different order (C05).

## 3. The rules

- **Duplicates (C04, C05):** keep the **first copy** and drop the rest. For the 7 conflicting ids the two copies carry the same information, so nothing is lost. The 7 ids are logged.
- **Parsing (C26):** parse `cast` and `crew` with `ast.literal_eval` and check that each result is a list.
- **Order:** duplicates are removed first, so no time is spent parsing rows that are about to be deleted.

## 4. Shared helpers

Both the credits and keywords tables need the same two tools, so they live in one shared file instead of being copied into each cleaning script:

- `parse_literal_column()`: turns Python-style text into real lists, and checks each result's type (see document 17).
- `keep_first_copy_per_id()`: removes duplicate ids and checks the result.

```python
def keep_first_copy_per_id(table, id_column, expected_removed, table_name):
    """Keep the first row for each id, and stop if the number removed is unexpected."""
    rows_before = len(table)

    repeated = table[table[id_column].duplicated(keep=False)]
    logger.info(
        "%s: ids that appear more than once: %s",
        table_name, repeated[id_column].nunique(),
    )

    # Copies that are not exact text matches (C05: same people, different order)
    distinct_copies = repeated.drop_duplicates()
    differing_ids = distinct_copies.loc[
        distinct_copies[id_column].duplicated(keep=False), id_column
    ].unique()
    logger.info(
        "%s: ids whose copies differ as text: %s -> %s",
        table_name, len(differing_ids), sorted(int(i) for i in differing_ids),
    )

    cleaned = table.drop_duplicates(subset=id_column, keep="first").reset_index(drop=True)

    removed = rows_before - len(cleaned)
    if removed != expected_removed:
        raise ValueError(
            f"{table_name}: expected to remove {expected_removed} copies, removed {removed}"
        )
    if cleaned[id_column].duplicated().any():
        raise ValueError(f"{table_name}: duplicate ids remain.")

    logger.info("%s: %s rows -> %s rows.", table_name, rows_before, len(cleaned))
    return cleaned
```

How it works:

- `duplicated(keep=False)` marks every copy of a repeated id, including the first.
- `drop_duplicates()` with no arguments removes only rows that are 100% identical. If an id still appears twice after that, its copies differ as text. This is how the 7 conflicting ids are found and logged.
- `drop_duplicates(subset=id_column, keep="first")` keeps the first row for each id, which is the C04 and C05 rule.
- The final checks stop the pipeline if the number of removed rows is not the expected one, or if any id is still repeated.

## 5. The credits step

```python
EXPECTED_CREDITS_DUPLICATES = 44   # 45,476 -> 45,432


def clean_credits(credits):
    """C04, C05, C26: remove duplicate copies, then parse cast and crew."""
    credits = keep_first_copy_per_id(
        credits, "id", EXPECTED_CREDITS_DUPLICATES, "credits"
    )

    credits = credits.copy()
    credits["cast"] = parse_literal_column(credits["cast"], list, "cast")
    credits["crew"] = parse_literal_column(credits["crew"], list, "crew")

    logger.info("clean_credits: parsed cast and crew for %s rows.", len(credits))
    return credits
```

The parse takes about 30 seconds, much longer than the metadata columns, because the cast and crew texts are very large.

## 6. Testing and verification

The check script is `tests/check_credits.py`. Run from the project root:

```powershell
python -m tests.check_credits
```

| Check | Expected | Result |
|---|---|---|
| Ids that appear more than once | 43 | 43 |
| Ids whose copies differ as text | the 7 ids above | the same 7 ids |
| Rows | 45,476 to 45,432 | 45,476 to 45,432 |
| Ids unique | yes | yes |
| Empty `crew` lists | 771 | 771 |
| Empty `cast` lists | 2,418 on the raw file | 2,414 |
| Toy Story, first cast member | Tom Hanks | Tom Hanks |

The 4 fewer empty `cast` lists come from duplicate copies that were removed. Toy Story has 13 cast members and 106 crew members.

## 7. Result

**The credits table is cleaned.** It has 45,432 rows with unique ids, and `cast` and `crew` are real lists.

It is not yet connected to the main pipeline. That happens after the keywords table is cleaned, so both tables are added together.
