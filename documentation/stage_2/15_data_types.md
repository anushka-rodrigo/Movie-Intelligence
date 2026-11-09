# Stage 2 — Fixing Data Types (C27)

## 1. Purpose

After the repair, almost every metadata column holds text. A budget stored as `"30000000"` cannot be averaged, and a date stored as `"1995-10-30"` cannot be grouped by decade. This step gives each column its proper type.

Function: `fix_data_types()` in `stage2_clean_metadata.py`.

## 2. Target types

| Columns | Type | Meaning |
|---|---|---|
| `popularity`, `budget`, `revenue`, `runtime`, `vote_average` | `float64` | Decimal numbers that can hold "missing" |
| `id`, `vote_count` | `Int64` | Whole numbers that are allowed to have gaps |
| `adult`, `video` | `bool` | Strictly true or false |
| `status`, `original_language` | `category` | A small fixed set of labels |
| `release_date` | `datetime64` | A real date |

`runtime` and `vote_average` are not named in decision C27, but the next step needs them as numbers.

`Int64` (capital I) is pandas' nullable integer. Plain `int64` cannot hold a missing value. `budget` first came out as plain `int64`, so it was forced to `float64` so that blanking out placeholders in the next step does not change its type.

Columns such as `title`, `overview` and `genres` stay as text for now. The list-like columns are parsed in a later step.

## 3. The safety rule

A conversion can quietly turn a bad value into "missing". To avoid that, every conversion is checked:

1. Count the missing values before.
2. Convert, with unparseable values turned into missing (`errors="coerce"`).
3. Count the missing values after.
4. If the count went up, stop and show the values that could not be converted.

## 4. The code

```python
def _convert_checked(series, converter, column_name):
    """Convert a column, and stop if any real value turned into 'missing'."""
    missing_before = series.isna().sum()
    converted = converter(series)
    newly_missing = converted.isna().sum() - missing_before

    if newly_missing != 0:
        culprits = series[converted.isna() & series.notna()].unique()[:5]
        raise ValueError(
            f"{column_name}: {newly_missing} values could not be converted, "
            f"for example {list(culprits)}"
        )
    return converted


def _to_bool(series, column_name):
    """Convert 'True'/'False' text to real booleans, and stop on anything else."""
    mapping = {"True": True, "False": False, True: True, False: False}
    converted = series.map(mapping)

    if converted.isna().any():
        culprits = series[converted.isna()].unique()[:5]
        raise ValueError(f"{column_name}: unexpected values {list(culprits)}")
    return converted.astype(bool)


def fix_data_types(meta):
    meta = meta.copy()

    for column in ["popularity", "budget", "revenue", "runtime", "vote_average"]:
        numbers = _convert_checked(
            meta[column], lambda s: pd.to_numeric(s, errors="coerce"), column
        )
        meta[column] = numbers.astype("float64")

    for column in ["id", "vote_count"]:
        numbers = _convert_checked(
            meta[column], lambda s: pd.to_numeric(s, errors="coerce"), column
        )
        meta[column] = numbers.astype("Int64")

    for column in ["adult", "video"]:
        meta[column] = _to_bool(meta[column], column)

    for column in ["status", "original_language"]:
        meta[column] = meta[column].astype("category")

    meta["release_date"] = _convert_checked(
        meta["release_date"],
        lambda s: pd.to_datetime(s, format="%Y-%m-%d", errors="coerce"),
        "release_date",
    )

    return meta
```

How it works:

- A `lambda` is a tiny unnamed function. It hands `_convert_checked` the conversion recipe, so one checking function serves both numbers and dates.
- `format="%Y-%m-%d"` is a strict year-month-day shape. Anything else becomes missing, and the check catches it.
- `_to_bool` accepts only `True` and `False` and stops on anything else.

## 5. Testing and verification

Check script: `tests/check_types.py`.

The data types came out as designed: `id` and `vote_count` as `Int64`, `adult` and `video` as `bool`, `status` and `original_language` as `category`, and `release_date` as `datetime64`.

The counts reconcile with Stage 1, which counted on the raw file before the repair:

| Check | Stage 1 (raw) | Now | Reason |
|---|---:|---:|---|
| `adult` True | 9 | 9 | Unchanged |
| `video` True | 93 | 93 | Unchanged |
| `release_date` missing | 87 | 84 | The 3 stub rows got their dates back |
| `runtime` missing | 263 | 257 | 6 values restored by the repair |
| `status` missing | 87 | 81 | The same 6 |

Release dates run from 1874 to 2020. The 1874 date is a real early film. The 2020 dates are movies marked as planned or rumoured, because the dataset was collected around 2017. They are kept, and `status` can be used to filter them in time-based analyses.

## 6. Result

**Every metadata column has a proper type, and no value was lost in the conversion.** The row count is still 45,433.
