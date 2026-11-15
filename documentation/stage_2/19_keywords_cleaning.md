# Stage 2 — Cleaning the Keywords Table (C03, C26)

## 1. Purpose

The `keywords` table has two problems, both already solved for `credits`:

1. **Duplicate ids.** 46,419 rows should be 45,432, so 987 rows are extra copies.
2. **Text instead of lists.** The `keywords` column is Python-style text, not a real list.

This step removes the duplicates and parses the column, using the shared helpers from the credits step.

The script is:

```text
src/scripts/stage2_modules/stage2_clean_keywords.py
```

## 2. What was wrong

From the Stage 1 investigation (decision C03):

- 985 ids appear more than once, and **all copies are identical**.
- Ids 141971 and 159849 appear three times, which is why 985 ids produce 987 extra rows.
- 14,795 rows (31.87%) have an empty keyword list on the raw file.

## 3. The rules

- **Duplicates (C03):** keep the first copy and drop the rest. Because the copies are identical, nothing is lost.
- **Parsing (C26):** parse the `keywords` column with `ast.literal_eval` and check that each result is a list.
- **Order:** remove duplicates first, so no time is spent parsing rows that are about to be deleted.

## 4. The code

```python
EXPECTED_KEYWORDS_DUPLICATES = 987   # 46,419 -> 45,432


def clean_keywords(keywords):
    """C03, C26: remove duplicate copies, then parse the keywords column."""
    keywords = keep_first_copy_per_id(
        keywords, "id", EXPECTED_KEYWORDS_DUPLICATES, "keywords"
    )

    keywords = keywords.copy()
    keywords["keywords"] = parse_literal_column(keywords["keywords"], list, "keywords")

    logger.info("clean_keywords: parsed keywords for %s rows.", len(keywords))
    return keywords
```

How it works:

- `keep_first_copy_per_id` and `parse_literal_column` come from `stage2_helpers.py` (see documents 17 and 18). This function has the same shape as `clean_credits`.
- The expected number of removed rows (987) comes from decision C03. The helper raises an error if a different number is removed, which protects against a changed file.
- `.copy()` means the table passed in is never modified.

## 5. Testing and verification

The check script is `tests/check_keywords.py`. Run from the project root:

```powershell
python -m tests.check_keywords
```

| Check | Expected | Result |
|---|---|---|
| Ids that appear more than once | 985 | 985 |
| Ids whose copies differ as text | 0 | 0 |
| Rows | 46,419 to 45,432 | 46,419 to 45,432 |
| Ids unique | yes | yes |
| Empty keyword lists | 14,795 on the raw file | 14,340 |

Toy Story's keywords came out as a real list: jealousy, toy, boy, friendship, friends, rivalry, boy next door, new toy, toy comes to life.

## 6. Result

**The keywords table is cleaned.** It has 45,432 rows with unique ids, and `keywords` is a real list. This is the number the Stage 1 summary predicted.
