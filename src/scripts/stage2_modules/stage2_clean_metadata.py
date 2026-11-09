import logging

import pandas as pd

logger = logging.getLogger(__name__)

# The tail row's values sit 9 columns to the left of where they belong
SHIFT = 9
EXPECTED_SPLIT_RECORDS = 3


def repair_split_records(meta):
    """C01: glue the 3 split metadata records back into single rows."""
    rows_before = len(meta)

    # Work on a copy, and let every column hold text and numbers for now
    meta = meta.copy().astype("object")
    columns = list(meta.columns)

    # Tail rows are the rows whose id is not a number
    id_as_number = pd.to_numeric(meta["id"], errors="coerce")
    tail_labels = list(meta.index[id_as_number.isna()])

    if len(tail_labels) != EXPECTED_SPLIT_RECORDS:
        raise ValueError(
            f"Expected {EXPECTED_SPLIT_RECORDS} split records, "
            f"found {len(tail_labels)}"
        )

    for tail_label in tail_labels:
        stub_label = tail_label - 1  # the stub is the row just before

        # The stub must be incomplete: it has no title
        if pd.notna(meta.at[stub_label, "title"]):
            raise ValueError(f"Row {stub_label} does not look like a stub")

        # Join the two halves of the overview with the original line break
        meta.at[stub_label, "overview"] = (
            meta.at[stub_label, "overview"]
            + "\n"
            + meta.at[tail_label, columns[0]]
        )

        # Move the tail's remaining values into columns 10 onward
        for j in range(1, 15):
            meta.at[stub_label, columns[j + SHIFT]] = meta.at[tail_label, columns[j]]

        logger.info("Repaired split record at rows %s and %s.", stub_label, tail_label)

    # Remove the leftover tail rows, then renumber 0, 1, 2... in file order
    meta = meta.drop(index=tail_labels).reset_index(drop=True)

    # Checks: the repair must have produced exactly what we expect
    if len(meta) != rows_before - EXPECTED_SPLIT_RECORDS:
        raise ValueError("Row count after repair is wrong.")
    if pd.to_numeric(meta["id"], errors="coerce").isna().any():
        raise ValueError("Some ids are still not numeric after repair.")

    logger.info("repair_split_records: %s rows -> %s rows.", rows_before, len(meta))
    return meta

EXPECTED_DUPLICATE_COPIES = 30

def remove_duplicate_movies(meta):
    """C06 + C07: keep one copy of each movie (highest vote_count, then first in file)."""
    rows_before = len(meta)
    meta = meta.copy()

    # Temporary helper columns, removed at the end
    meta["_id"] = pd.to_numeric(meta["id"])
    meta["_votes"] = pd.to_numeric(meta["vote_count"])
    meta["_position"] = range(len(meta))

    # Which ids appear more than once?
    repeated = meta[meta["_id"].duplicated(keep=False)]
    logger.info("Movie ids that appear more than once: %s", repeated["_id"].nunique())

    # Of those, which have copies that really differ? (C07)
    content_columns = [c for c in meta.columns if not c.startswith("_")]
    distinct_copies = repeated.drop_duplicates(subset=content_columns)
    conflict_ids = distinct_copies.loc[
        distinct_copies["_id"].duplicated(keep=False), "_id"
    ].unique()
    logger.info("Ids whose copies differ: %s -> %s", len(conflict_ids), sorted(conflict_ids))

    # Of those, which differ in vote_count?
    votes_per_id = repeated.groupby("_id")["_votes"].nunique()
    vote_conflict_ids = votes_per_id[votes_per_id > 1].index.tolist()
    logger.info("Ids whose vote_count differs: %s", vote_conflict_ids)

    # Best copy first: higher vote_count, then earlier position in the file
    ordered = meta.sort_values(
        ["_id", "_votes", "_position"],
        ascending=[True, False, True],
        na_position="last",
    )
    kept = ordered.drop_duplicates(subset="_id", keep="first")

    # Restore the original file order and remove the helper columns
    kept = (
        kept.sort_values("_position")
        .drop(columns=["_id", "_votes", "_position"])
        .reset_index(drop=True)
    )

    # Checks
    removed = rows_before - len(kept)
    if removed != EXPECTED_DUPLICATE_COPIES:
        raise ValueError(
            f"Expected to remove {EXPECTED_DUPLICATE_COPIES} copies, removed {removed}"
        )
    if pd.to_numeric(kept["id"]).duplicated().any():
        raise ValueError("Duplicate ids remain after de-duplication.")

    logger.info("remove_duplicate_movies: %s rows -> %s rows.", rows_before, len(kept))
    return kept

def clean_movies_metadata(meta):
    """Run every metadata cleaning step in order."""
    meta = repair_split_records(meta)
    meta = remove_duplicate_movies(meta)
    return meta
