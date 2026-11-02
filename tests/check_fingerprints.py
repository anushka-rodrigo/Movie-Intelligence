from src.scripts.stage2_fingerprint_data import fingerprint_raw_data

fingerprints = fingerprint_raw_data()

print("\nFingerprinting completed successfully!")

print(f"\nTotal files fingerprinted: {len(fingerprints)}")