import logging

from src.scripts.stage2_modules.stage2_helpers import (
    keep_first_copy_per_id,
    parse_literal_column,
)

logger = logging.getLogger(__name__)

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