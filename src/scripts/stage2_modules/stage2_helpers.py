import ast
import logging

import pandas as pd

logger = logging.getLogger(__name__)


def parse_literal_column(series, expected_type, column_name):
    """Turn Python-style text into real lists/dicts, and check each result's type."""

    def parse_cell(value):
        if pd.isna(value):
            return None                      # genuinely missing stays missing

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