```python
#!/usr/bin/env python3

"""
merge_scdb.py
-----------------

Merges the SCDB Legacy (~1791–1945) and Modern (~1946–present) case-centered citation datasets.

INSTRUCTIONS:

1. Download the SCDB Legacy and Modern "case centered, citation" CSVs from:
   http://scdb.wustl.edu/data.php?s=1

2. Place both CSV files in the same folder as this script.

3. Run:

       python3 merge_scdb.py

4. When prompted, enter the exact filenames, e.g.:

       SCDB_Legacy_07_caseCentered_Citation.csv
       SCDB_2025_01_caseCentered_Citation.csv

The script will produce:

    SCDB_merged.csv
"""

import pandas as pd

def main():
    legacy_file = input("Enter the Legacy SCDB CSV filename (e.g. SCDB_Legacy_07_caseCentered_Citation.csv): ").strip()
    modern_file = input("Enter the Modern SCDB CSV filename (e.g. SCDB_2025_01_caseCentered_Citation.csv): ").strip()

    if not legacy_file or not modern_file:
        raise SystemExit("Both filenames are required. Exiting.")

    print(f"Loading Legacy SCDB from: {legacy_file}")
    legacy = pd.read_csv(legacy_file, dtype=str)

    print(f"Loading Modern SCDB from: {modern_file}")
    modern = pd.read_csv(modern_file, dtype=str)

    print("Merging datasets...")
    merged = pd.concat([legacy, modern], ignore_index=True)

    output = "SCDB_merged.csv"
    print(f"Saving merged SCDB to: {output}")
    merged.to_csv(output, index=False)

    print("\nDone! SCDB_merged.csv is ready.")

if __name__ == "__main__":
    main()
