# WikipediaSCOTUS

This repository provides a complete workflow for generating a unified dataset of U.S. Supreme Court cases with:

- Wikipedia metadata  
- U.S. Reports citations  
- Docket numbers  
- Monthly Wikipedia pageviews (2008–present)  
- Supreme Court Database (SCDB) variables  

The workflow uses three scripts:

- caseCollector.py — Scrapes Wikipedia SCOTUS infobox pages + pageviews  
- merge_scdb.py — Merges SCDB Legacy + Modern into one unified file  
- extract.py — Merges SCDB with Wikipedia data  

Because SCDB cannot be redistributed here, you must download the official CSVs directly from SCDB.

---

## Required External Data: Supreme Court Database (SCDB)

Download two datasets from:

http://scdb.wustl.edu/data.php?s=1

You need the “Case Centered — Cases Organized by Supreme Court Citation” version for both Modern and Legacy.

### 1. Modern Database (1946 → present)

From the MODERN Database section, download the latest release.

Example filename (yours may differ):

SCDB_2025_01_caseCentered_Citation.csv.zip

Unzip it so you have the CSV:

SCDB_2025_01_caseCentered_Citation.csv

### 2. Legacy Database (1791 → 1945)

From the LEGACY Database section, download:

SCDB_Legacy_07_caseCentered_Citation.csv.zip

Unzip it so you have:

SCDB_Legacy_07_caseCentered_Citation.csv

Place both CSVs in the same folder as the scripts.

---

## Step 1 — Merge SCDB Modern + Legacy

Run:

python3 merge_scdb.py

You will be prompted for:

- Legacy SCDB filename (e.g. SCDB_Legacy_07_caseCentered_Citation.csv)  
- Modern SCDB filename (e.g. SCDB_2025_01_caseCentered_Citation.csv)

Output created:

SCDB_merged.csv

This file contains all rows from both Legacy and Modern SCDB case-centered citation datasets.

---

## Step 2 — Prepare Repository Structure

Your folder should now contain:

caseCollector.py  
extract.py  
merge_scdb.py  
SCDB_Legacy_07_caseCentered_Citation.csv (or your legacy filename)  
SCDB_2025_01_caseCentered_Citation.csv (or your modern filename)  
SCDB_merged.csv  
.env

---

## Step 3 — Provide Wikimedia OAuth Credentials

Create a .env file containing:

WIKI_OAUTH_CONSUMER_KEY="YOUR_KEY"  
WIKI_OAUTH_CONSUMER_SECRET="YOUR_SECRET"  
WIKI_OAUTH_ACCESS_TOKEN="YOUR_TOKEN"  
WIKI_OAUTH_ACCESS_SECRET="YOUR_ACCESS_SECRET"

These must come from your own Wikimedia OAuth consumer/app.

---

## Step 4 — Run caseCollector.py

This script:

- Finds all Wikipedia pages using SCOTUS infobox templates  
- Extracts U.S. Reports citations  
- Extracts docket numbers  
- Downloads monthly pageview metrics from July 2015 to present via the official REST API (pre-2015 data may be incomplete/legacy)
- Produces:

wiki_infobox_cases.csv

Run:

python3 caseCollector.py

---

## Step 5 — Run extract.py

This script merges:

- wiki_infobox_cases.csv  
- SCDB_merged.csv  

It outputs:

SCDB_with_infobox_views.csv  
unmatched_wiki_cases.csv

Run:

python3 extract.py

---

## Output Summary

SCDB_merged.csv — Combined SCDB Legacy + Modern (citation-organized, case-centered)  
wiki_infobox_cases.csv — All Wikipedia SCOTUS infobox pages with citations, dockets, and pageviews  
SCDB_with_infobox_views.csv — Final merged dataset (SCDB + Wikipedia metadata + pageviews)  
unmatched_wiki_cases.csv — Wikipedia cases that could not be matched to SCDB

---

## Final Result

You get a unified dataset containing:

- SCDB variables from 1791 → present  
- Wikipedia attention metrics (monthly) from 2008 → present  
- Accurate case matching via U.S. Reports citations and docket numbers  

This supports constructing a Wikipedia-based salience measure for U.S. Supreme Court cases.
