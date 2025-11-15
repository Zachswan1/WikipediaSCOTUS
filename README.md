# 📘 WikipediaSCOTUS

A Python-based data collection tool for building a **Wikipedia-based salience measure** for U.S. Supreme Court cases.

This project automatically:

- Finds **all Wikipedia articles** that use SCOTUS-related infobox templates  
- Extracts each page’s **U.S. Reports citation** (if present)  
- Extracts each page’s **docket number**  
- Downloads **monthly pageview metrics** (July 2015–present)  
- Produces a unified dataset:  
  **wiki_infobox_cases.csv**

This enables a transparent, replicable measure of public attention toward Supreme Court cases using Wikipedia traffic patterns.

---

## 📂 Repository Structure

WikipediaSCOTUS/  
│  
├── caseCollector.py      ← main script (collects all data)  
├── extract.py            ← optional helper script  
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

Run the collector:

python3 caseCollector.py

The script will:

1. Identify Wikipedia pages with SCOTUS infobox templates  
2. Extract:  
   - U.S. Reports citation  
   - Docket number  
3. Fetch monthly pageviews (July 2015–present)  
4. Save the final dataset as **wiki_infobox_cases.csv**

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

Although the script requests data starting in 2008, the API only returns valid monthly traffic metrics from mid-2015 onward.  
Pageviews prior to July 2015 are incomplete and should not be treated as comparable or reliable measures.

---
