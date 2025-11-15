# 📘 WikipediaSCOTUS

A Python-based data collection tool for building a **Wikipedia-based salience measure** for U.S. Supreme Court cases.

This project:

- Identifies **all Wikipedia articles** containing SCOTUS-related infobox templates  
- Extracts each page’s **U.S. Reports citation** (if present)  
- Extracts each page’s **docket number**  
- Downloads **monthly pageview metrics** (July 2015–present)  
- Produces a unified dataset of Wikipedia-based salience values  
- Integrates this dataset with **Supreme Court Database (SCDB)** case information

---

## 📂 Repository Structure

WikipediaSCOTUS/  
│  
├── caseCollector.py      ← Scrapes Wikipedia infoboxes + pageviews  
├── extract.py            ← Merges Wikipedia data with SCDB case data  
└── README.md  

---

## 🛠️ Requirements

Install dependencies:

pip install -r requirements.txt

Suggested requirements.txt:

requests  
requests-oauthlib  
tqdm  
python-dotenv  

---

## 🔐 Authentication (Required)

This script uses the Wikimedia API via **OAuth 1.0a**.

Create your OAuth consumer here:

https://meta.wikimedia.org/wiki/Special:OAuthConsumerRegistration/propose

Then create a `.env` file containing:

WIKI_OAUTH_CONSUMER_KEY=your_key  
WIKI_OAUTH_CONSUMER_SECRET=your_secret  
WIKI_OAUTH_ACCESS_TOKEN=your_token  
WIKI_OAUTH_ACCESS_SECRET=your_token_secret  

⚠️ Never commit your `.env` file.

---

## ▶️ Usage

### Step 1 — Collect Wikipedia case data

Run:

python3 caseCollector.py

This produces:

**wiki_infobox_cases.csv**

containing:
- page title  
- U.S. Reports citation  
- docket number  
- pageview metrics  

### Step 2 — Merge with SCDB data

Place your SCDB file (e.g., `SCDB_2024_01_caseCentered_Citation.csv`) in the same directory.

Then run:

python3 extract.py

This produces:

**scdb_with_wikipedia_salience.csv**

which merges SCDB case metadata with Wikipedia pageview-based salience.

---

## 📊 Output Columns (wiki_infobox_cases.csv)

title — Wikipedia page title  
usCite — U.S. Reports citation (if present)  
docket — Docket number  
views_all_time — Total views since July 2015  
views_1yr — Views in the last 12 months  
views_6mo — Views in the last 6 months  
views_1mo — Views in the last month  

---

## 📝 Notes on Pageview Data

The Wikimedia REST API provides reliable pageview data beginning **July 2015**.

Although the script requests data starting in 2008, the API only returns valid monthly traffic from mid-2015 onward.  
Pageviews from before July 2015 are incomplete and should not be treated as comparable measures.

---
