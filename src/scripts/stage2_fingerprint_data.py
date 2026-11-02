
import hashlib
from config.paths import RAW_DATA_DIR


def calculate_sha256(file_path):
    sha256_hash = hashlib.sha256()

    with open(file_path, "rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            sha256_hash.update(chunk)

    return sha256_hash.hexdigest()


def fingerprint_raw_data():
    raw_files = [
        "credits.csv",
        "keywords.csv",
        "links.csv",
        "movies_metadata.csv",
        "ratings.csv",
    ]

    fingerprints = {}

    for filename in raw_files:
        file_path = RAW_DATA_DIR / filename

        if not file_path.exists():
            raise FileNotFoundError(
                f"Raw data file not found: {file_path}"
            )

        fingerprint = calculate_sha256(file_path)
        fingerprints[filename] = fingerprint

        print(f"{filename}: {fingerprint}")

    return fingerprints
