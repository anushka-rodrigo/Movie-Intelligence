from scripts.stage2_modules.stage2_fingerprint_data import (
    fingerprint_raw_data,
    save_or_verify_fingerprints,
)

fingerprints = fingerprint_raw_data()

save_or_verify_fingerprints(fingerprints)

print("\nFingerprinting and verification completed successfully!")
print(f"\nTotal files fingerprinted: {len(fingerprints)}")
