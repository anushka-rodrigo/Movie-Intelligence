from src.scripts.stage2_extract_data import extract_data

tables = extract_data()

print("\nExtraction completed successfully!")

print("\nAvailable datasets:")

for name, df in tables.items():
    print(f"{name}: {df.shape}")
    
# run following code at root to test
# python -m tests.check_extraction