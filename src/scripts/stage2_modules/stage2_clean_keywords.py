import logging

from src.scripts.stage2_modules.stage2_helpers import (
    keep_first_copy_per_id,
    parse_literal_column,
)

logger = logging.getLogger(__name__)

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