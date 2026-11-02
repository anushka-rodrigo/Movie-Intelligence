
from pathlib import Path

# Project root directory - move to parent path then its parent path
PROJECT_ROOT = Path(__file__).resolve().parent.parent 

# Main directories
DATA_DIR = PROJECT_ROOT / "data"

RAW_DATA_DIR = DATA_DIR / "raw_data"

PROCESSED_DATA_DIR = DATA_DIR / "processed"

LOG_DIR = PROJECT_ROOT / "logs"

TEST_DIR = PROJECT_ROOT / "tests"

SRC_DIR = PROJECT_ROOT / "src"

SCRIPTS_DIR = SRC_DIR / "scripts"
