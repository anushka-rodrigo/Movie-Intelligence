import hashlib
import json

from config.paths import RAW_DATA_DIR, PROCESSED_DATA_DIR


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

def save_or_verify_fingerprints(fingerprints):
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

    manifest_path = PROCESSED_DATA_DIR / "raw_data_fingerprints.json"

    # First run: save the original fingerprints
    if not manifest_path.exists():
        with open(manifest_path, "w", encoding="utf-8") as file:
            json.dump(fingerprints, file, indent=4)

        print("\nFingerprint manifest created successfully!")
        return

    # Future runs: compare against the saved fingerprints
    with open(manifest_path, "r", encoding="utf-8") as file:
        saved_fingerprints = json.load(file)

    changed_files = []

    for filename, current_hash in fingerprints.items():
        saved_hash = saved_fingerprints.get(filename)

        if saved_hash != current_hash:
            changed_files.append(filename)

    if changed_files:
        print("\nWARNING: Raw data changes detected!")

        for filename in changed_files:
            print(f"Changed or missing from manifest: {filename}")

        raise ValueError("Raw data fingerprint verification failed.")

    print("\nAll raw data fingerprints verified successfully!")


if __name__ == "__main__":
    fingerprints = fingerprint_raw_data()
    save_or_verify_fingerprints(fingerprints)
