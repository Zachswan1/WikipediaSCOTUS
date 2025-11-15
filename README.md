# WikipediaSCOTUS

This repository generates a unified dataset of U.S. Supreme Court cases using:

- Wikipedia infobox metadata  
- U.S. Reports citations  
- Docket numbers  
- Monthly Wikipedia pageviews (2008–present)  
- Supreme Court Database (SCDB) variables  

The workflow uses three scripts:

- `caseCollector.py` — Scrapes Wikipedia SCOTUS infobox pages + pageviews  
- `merge_scdb.py` — Merges SCDB Legacy + Modern datasets  
- `extract.py` — Merges SCDB with Wikipedia data  

Because SCDB cannot be redistributed, you must download the official CSVs directly from the SCDB website.

---

## 📦 Installation

### 1. Install required Python packages

Run:

```bash
pip3 install -r requirements.txt
```

`requirements.txt` contains:

- `python-dotenv` — loads your `.env` file containing Wikimedia OAuth credentials  
- `requests` — MediaWiki HTTP API  
- `requests_oauthlib` — OAuth1 authentication  
- `tqdm` — progress bars  
- `pandas` — SCDB dataset processing  

---

## 🔐 Step 2 — Provide Wikimedia OAuth Credentials

Create a `.env` file in the same folder as the scripts:

```
WIKI_OAUTH_CONSUMER_KEY="YOUR_KEY"
WIKI_OAUTH_CONSUMER_SECRET="YOUR_SECRET"
WIKI_OAUTH_ACCESS_TOKEN="YOUR_ACCESS_TOKEN"
WIKI_OAUTH_ACCESS_SECRET="YOUR_ACCESS_SECRET"
```

These must come from your own Wikimedia OAuth consumer/app.

`caseCollector.py` will load them automatically using `python-dotenv`.

---

## 📥 Required External Data: Supreme Court Database (SCDB)

Download two datasets from:

http://scdb.wustl.edu/data.php?s=1

You need the **Case Centered — Cases Organized by Supreme Court Citation** version for both Modern and Legacy.

### 1. Modern SCDB (1946–present)

Example filename (yours may differ):

```
SCDB_2025_01_caseCentered_Citation.csv
```

### 2. Legacy SCDB (1791–1945)

Example filename:

```
SCDB_Legacy_07_caseCentered_Citation.csv
```

Unzip both files so the `.csv` versions are in your project folder.

---

## Step 3 — Merge SCDB Modern + Legacy

Run:

```bash
python3 merge_scdb.py
```

You will be prompted for:

- The Legacy SCDB CSV  
- The Modern SCDB CSV  

Output produced:

```
SCDB_merged.csv
```

This file contains all cases from both datasets.

---

## Step 4 — Run the Wikipedia Case Collector

This script:

- Finds all Wikipedia pages using SCOTUS infobox templates  
- Extracts U.S. Reports citations  
- Extracts docket numbers  
- Downloads monthly pageviews (2008 → present)  
- Produces:

```
wiki_infobox_cases.csv
```

Run:

```bash
python3 caseCollector.py
```

---

## Step 5 — Merge Wikipedia + SCDB Data

This script merges:

- `wiki_infobox_cases.csv`  
- `SCDB_merged.csv`  

It outputs:

```
SCDB_with_infobox_views.csv
unmatched_wiki_cases.csv
```

Run:

```bash
python3 extract.py
```

---

## Output Summary

- `SCDB_merged.csv` — Combined SCDB Legacy + Modern  
- `wiki_infobox_cases.csv` — All Wikipedia SCOTUS infobox pages with citations, dockets, and pageviews  
- `SCDB_with_infobox_views.csv` — Final merged dataset (SCDB + Wikipedia metadata + pageviews)  
- `unmatched_wiki_cases.csv` — Wikipedia cases that could not be matched to SCDB  

---

## Final Result

You obtain a unified dataset containing:

- SCDB variables from 1791 → present  
- Wikipedia attention metrics (monthly) from 2008 → present  
- Accurate matching via U.S. Reports citations + docket numbers  

This supports constructing a Wikipedia-based salience measure for U.S. Supreme Court cases.
