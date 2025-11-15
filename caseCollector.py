#!/usr/bin/env python3
"""
Wikipedia SCOTUS Case Collector
-----------------------------

This script collects:
  - All Wikipedia pages using SCOTUS-related infobox templates
  - Each page’s U.S. Reports citation and docket number (if present)
  - Monthly pageview metrics (all-time, 1-year, 6-month, 1-month)
  - Outputs:
        wiki_infobox_cases.csv

NOTE:
    You MUST provide your own Wikimedia OAuth credentials.

    Create a `.env` file (or export environment variables) containing:

        WIKI_OAUTH_CONSUMER_KEY="YOUR_KEY_HERE"
        WIKI_OAUTH_CONSUMER_SECRET="YOUR_SECRET_HERE"
        WIKI_OAUTH_ACCESS_TOKEN="YOUR_ACCESS_TOKEN"
        WIKI_OAUTH_ACCESS_SECRET="YOUR_ACCESS_SECRET"

"""

import os
import re
import csv
import time
import datetime
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from requests.adapters import HTTPAdapter, Retry
from requests_oauthlib import OAuth1
from tqdm import tqdm
from threading import Lock


# ============================================================
# 🔐 OAuth Credentials — MUST BE SUPPLIED BY USER
# ============================================================

CONSUMER_KEY = os.getenv("WIKI_OAUTH_CONSUMER_KEY")
CONSUMER_SECRET = os.getenv("WIKI_OAUTH_CONSUMER_SECRET")
ACCESS_TOKEN = os.getenv("WIKI_OAUTH_ACCESS_TOKEN")
ACCESS_SECRET = os.getenv("WIKI_OAUTH_ACCESS_SECRET")

if not all([CONSUMER_KEY, CONSUMER_SECRET, ACCESS_TOKEN, ACCESS_SECRET]):
    raise RuntimeError(
        "Missing OAuth credentials. "
        "Set environment variables or create a .env file."
    )

# ============================================================
# API & Headers
# ============================================================

API_URL = "https://en.wikipedia.org/w/api.php"

HEADERS = {
    "User-Agent": (
        "SCOTUS-Infobox-Scraper/1.0 "
        "(contact: YOUR_EMAIL_HERE) "
        "Python/3.x"
    )
}

auth = OAuth1(
    CONSUMER_KEY,
    CONSUMER_SECRET,
    ACCESS_TOKEN,
    ACCESS_SECRET,
    signature_type="auth_header",
)

# ============================================================
# Regex patterns for infobox extraction
# ============================================================

INFOBOX_START = re.compile(
    r"\{\{\s*(?:"
    r"Infobox\s+US\s+Supreme\s+Court\s+case"
    r"|Infobox\s+SCOTUS\s+case"
    r"|SCOTUSCase"
    r")",
    re.I,
)

US_CITE_RE = re.compile(r"\b\d+\s*U\.?\s*S\.?\s*\d+\b", re.I)

DOCKET_TOKEN_RE = re.compile(
    r"""
    \b
    (?:No\.?\s*)?
    (
        \d{1,3}[-–—]\d{1,5}     # e.g. 14-10078, 24-699
        |
        \d{1,3}[A-Z]\d{1,4}     # e.g. 22O141
    )
    \b
    """,
    re.VERBOSE | re.IGNORECASE,
)

# ============================================================
# Rate limiting
# ============================================================

rate_lock = Lock()
delay = 0.03

def throttle():
    with rate_lock:
        time.sleep(delay)

def adjust_rate(error=False):
    global delay
    with rate_lock:
        if error:
            delay = min(delay * 2, 1.0)
        else:
            delay = max(delay * 0.95, 0.02)

# ============================================================
# HTTP session with retries
# ============================================================

session = requests.Session()
session.auth = auth

retries = Retry(
    total=5,
    backoff_factor=0.2,
    status_forcelist=[429, 500, 502, 503, 504],
)
session.mount("https://", HTTPAdapter(max_retries=retries))


def safe_get(params):
    throttle()
    r = session.get(API_URL, params=params, headers=HEADERS, timeout=25)
    if r.status_code == 429:
        adjust_rate(error=True)
        time.sleep(delay)
        return safe_get(params)
    adjust_rate(error=False)
    r.raise_for_status()
    return r.json()


# ============================================================
# Retrieve pages that use SCOTUS infobox templates
# ============================================================

def get_pages_with_infobox():
    pages = set()
    templates = [
        "Template:Infobox_US_Supreme_Court_case",
    ]

    for title in templates:
        params = {
            "action": "query",
            "list": "embeddedin",
            "eititle": title,
            "einamespace": 0,
            "eilimit": "max",
            "format": "json",
        }

        while True:
            data = safe_get(params)
            for p in data.get("query", {}).get("embeddedin", []):
                pages.add(p["title"])

            if "continue" not in data:
                break
            params.update(data["continue"])

    return sorted(pages)


# ============================================================
# Wikitext retrieval & parsing
# ============================================================

def get_wikitext_batch(titles):
    throttle()
    params = {
        "action": "query",
        "prop": "revisions",
        "rvprop": "content",
        "titles": "|".join(titles),
        "format": "json",
        "formatversion": "2",
    }
    data = safe_get(params)
    out = {}

    for p in data["query"]["pages"]:
        out[p["title"]] = p.get("revisions", [{}])[0].get("content", "")

    return out


def extract_infobox(text):
    m = INFOBOX_START.search(text)
    if not m:
        return ""
    start = m.start()
    depth = 0
    i = start

    while i < len(text):
        if text[i:i+2] == "{{":
            depth += 1
            i += 2
        elif text[i:i+2] == "}}":
            depth -= 1
            i += 2
            if depth <= 0:
                return text[start:i]
        else:
            i += 1

    return ""


def clean_markup(t):
    t = re.sub(r"\[https?://[^\]\s]*(?:\s+[^\]]+)?\]", "", t)
    t = re.sub(r"\[\[([^\]|]+\|)?([^\]]+)\]\]", r"\2", t)
    t = re.sub(r"<.*?>", "", t)
    return t


def extract_us_cite_and_docket(box):
    us = ""
    docket = ""

    box_clean = clean_markup(box)

    # Citations field
    cit = re.search(
        r"\|\s*[Cc]itations\s*=\s*((?:.|\n)*?)(?=\n\|\s*\w+\s*=|\n\}\}|$)",
        box_clean,
    )

    if cit:
        field = cit.group(1)
        m_us = US_CITE_RE.search(field)
        if m_us:
            us = m_us.group(0)

        m_dk = DOCKET_TOKEN_RE.search(field)
        if m_dk and not docket:
            docket = m_dk.group(1)

    # USVol + USPage
    if not us:
        v = re.search(r"\|\s*[Uu][Ss][Vv]ol\s*=\s*([0-9]+)", box_clean)
        p = re.search(r"\|\s*[Uu][Ss][Pp]age\s*=\s*([0-9]+)", box_clean)
        if v and p:
            us = f"{v.group(1)} U.S. {p.group(1)}"

    # Docket field
    if not docket:
        m_line = re.search(r"\|\s*[Dd]ocket\s*=\s*([^\n]+)", box_clean)
        if m_line:
            rhs = m_line.group(1)
            m_dk = DOCKET_TOKEN_RE.search(rhs)
            if m_dk:
                docket = m_dk.group(1)

    docket = docket.replace("–", "-").replace("—", "-")
    return us.strip(), docket.strip()


# ============================================================
# Pageview retrieval
# ============================================================

def get_pageviews(title):
    throttle()
    base = (
        "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/"
        "en.wikipedia/all-access/user"
    )

    t = title.replace(" ", "_")
    start = "20080101"
    end = datetime.date.today().strftime("%Y%m%d")

    url = f"{base}/{t}/monthly/{start}/{end}"

    try:
        r = session.get(url, headers=HEADERS, timeout=20)
        if r.status_code == 429:
            adjust_rate(error=True)
            time.sleep(delay)
            return (0, 0, 0, 0)

        adjust_rate(error=False)

        if r.status_code != 200:
            return (0, 0, 0, 0)

        items = r.json().get("items", [])
        if not items:
            return (0, 0, 0, 0)

        views = [x["views"] for x in items]

        all_time = sum(views)
        last_12 = sum(views[-12:]) if len(views) >= 12 else sum(views)
        last_6 = sum(views[-6:]) if len(views) >= 6 else sum(views)
        last_1 = views[-1] if views else 0

        return (all_time, last_12, last_6, last_1)

    except Exception:
        return (0, 0, 0, 0)


# ============================================================
# Batch processing
# ============================================================

def process_batch(titles):
    data = get_wikitext_batch(titles)
    rows = []

    for t in titles:
        txt = data.get(t, "") or ""
        box = extract_infobox(txt)

        if box:
            us, dock = extract_us_cite_and_docket(box)
        else:
            us, dock = "", ""

        rows.append((t, us, dock))

    return rows


# ============================================================
# Main workflow
# ============================================================

def main():
    print("Fetching list of pages with SCOTUS infobox...")
    pages = get_pages_with_infobox()
    print(f"Found {len(pages)} pages.\n")

    batches = [pages[i:i+50] for i in range(0, len(pages), 50)]

    all_rows = []

    print("Fetching wikitext and extracting cites/dockets...")
    with ThreadPoolExecutor(max_workers=10) as pool, tqdm(
        total=len(batches), desc="Wikitext"
    ) as bar:
        futures = [pool.submit(process_batch, b) for b in batches]
        for fut in as_completed(futures):
            rows = fut.result()
            all_rows.extend(rows)
            bar.update(1)

    print(f"\nTotal rows collected: {len(all_rows)}\n")

    print("Fetching pageviews...")
    final_rows = []
    with ThreadPoolExecutor(max_workers=20) as pool, tqdm(
        total=len(all_rows), desc="Pageviews"
    ) as bar:
        future_map = {
            pool.submit(get_pageviews, t): (t, us, dock)
            for (t, us, dock) in all_rows
        }

        for fut in as_completed(future_map):
            t, us, dock = future_map[fut]
            v_all, v_yr, v_6, v_1 = fut.result()
            final_rows.append([
                t, us, dock,
                v_all, v_yr, v_6, v_1
            ])
            bar.update(1)

    with open("wiki_infobox_cases.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow([
            "title",
            "usCite",
            "docket",
            "views_all_time",
            "views_1yr",
            "views_6mo",
            "views_1mo",
        ])
        w.writerows(final_rows)

    print("\n=== DONE ===")
    print("wiki_infobox_cases.csv rows:", len(final_rows))


if __name__ == "__main__":
    main()
