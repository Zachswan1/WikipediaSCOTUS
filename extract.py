import pandas as pd
import re

WIKI_FILE = "wiki_infobox_cases.csv"
SCDB_FILE = "SCDB_merged.csv"
OUTPUT_FILE = "SCDB_with_infobox_views.csv"
UNMATCHED_FILE = "unmatched_wiki_cases.csv"


def norm_us(s: str) -> str:
    """Normalize U.S. citations for matching."""
    if not isinstance(s, str):
        return ""
    s = s.strip()
    # Normalize U. S. vs U.S.
    s = s.replace("U. S.", "U.S.").replace("U. S", "U.S")
    s = s.replace("U. S", "U.S")
    # Normalize dashes
    s = s.replace("–", "-").replace("—", "-")
    # Collapse internal whitespace
    s = " ".join(s.split())
    return s


def norm_docket(s: str) -> str:
    """Normalize docket strings for matching."""
    if not isinstance(s, str):
        return ""
    s = s.strip()
    s = s.replace("–", "-").replace("—", "-")
    # Strip "No." prefixes but preserve letters and hyphens
    s = s.replace("No. ", "").replace("No.", "")
    return s


# Placeholder U.S. citations:
#   592 U.S. ___
#   596 U.S. —
#   586 U.S.
#   603 U.S.
PLACEHOLDER_US_RE = re.compile(
    r"""
    ^\s*
    \d+\s*U\.?S\.?
    (?:\s*[_\-–—]*)?   # underscores/dashes but NO trailing page digits
    \s*$
    """,
    re.VERBOSE | re.IGNORECASE,
)


def is_placeholder_us(us_norm: str) -> bool:
    """
    Return True if:
      - usCite is blank, or
      - usCite looks like a placeholder.

    For matching logic, blank and placeholder both mean "no usable usCite".
    """
    if not us_norm:
        return True
    return bool(PLACEHOLDER_US_RE.match(us_norm))


def get_wiki_year(row: pd.Series):
    """
    Get a decision year from wiki metadata, used only to disambiguate
    when a docket maps to multiple SCDB rows.

    Priority:
        1. Year in the title at the end: '... (2018)'
        2. Year in the raw usCite string: '524 U.S. 274 (1998)'
    """
    title = str(row.get("title", "") or "")
    m = re.search(r"\((\d{4})\)\s*$", title)
    if m:
        return int(m.group(1))

    us_raw = str(row.get("usCite", "") or "")
    m2 = re.search(r"(1[89]\d{2}|20\d{2})", us_raw)
    if m2:
        return int(m2.group(1))

    return None


def compute_decision_year(date_decision: str, term: str):
    """
    Compute a year for SCDB rows, preferring dateDecision, falling
    back to term if necessary.
    """
    dd = str(date_decision or "").strip()
    if dd:
        parts = dd.split("/")
        y = parts[-1]
        if len(y) == 4 and y.isdigit():
            return int(y)

    t = str(term or "").strip()
    if t.isdigit():
        return int(t)

    return None


def main():
    # Load wiki infobox data — includes ALL infobox pages, even with blank usCite/docket.
    wiki = pd.read_csv(WIKI_FILE, dtype=str).fillna("")
    scdb = pd.read_csv(SCDB_FILE, dtype=str).fillna("")

    # Normalize for matching
    wiki["usCite_norm"] = wiki["usCite"].apply(norm_us)
    wiki["docket_norm"] = wiki["docket"].apply(norm_docket)

    scdb["usCite_norm"] = scdb["usCite"].apply(norm_us)
    scdb["docket_norm"] = scdb["docket"].apply(norm_docket)

    # Precompute decision year for SCDB, for docket-based disambiguation
    scdb["decisionYear"] = scdb.apply(
        lambda r: compute_decision_year(
            r.get("dateDecision", ""), r.get("term", "")
        ),
        axis=1,
    )

    # Index SCDB by usCite_norm and docket_norm
    scdb_by_us = {}
    for k, grp in scdb.groupby("usCite_norm"):
        if k:
            scdb_by_us[k] = grp

    scdb_by_docket = {}
    for k, grp in scdb.groupby("docket_norm"):
        if k:
            scdb_by_docket[k] = grp

    matched_rows = []
    unmatched_rows = []

    for _, w_row in wiki.iterrows():
        w_title = w_row["title"]
        w_us_norm = w_row["usCite_norm"]
        w_docket_norm = w_row["docket_norm"]

        # Treat placeholders and blanks as "no usCite" for matching
        if is_placeholder_us(w_us_norm):
            w_us_effective = ""
        else:
            w_us_effective = w_us_norm

        chosen = None

        # --- 1) Try usCite first (if non-blank and non-placeholder) --------
        if w_us_effective and w_us_effective in scdb_by_us:
            cand = scdb_by_us[w_us_effective]
            if len(cand) == 1:
                chosen = cand.iloc[0]
            else:
                # In practice US reports cites are unique; if not,
                # take the first row deterministically.
                chosen = cand.iloc[0]

        # --- 2) If no usCite match, try docket -----------------------------
        if chosen is None and w_docket_norm:
            if w_docket_norm in scdb_by_docket:
                cand = scdb_by_docket[w_docket_norm]

                if len(cand) == 1:
                    chosen = cand.iloc[0]
                else:
                    # Only here do we invoke year-based disambiguation:
                    # a docket maps to multiple SCDB decisions.
                    wiki_year = get_wiki_year(w_row)
                    if wiki_year is not None:
                        cand_year = cand[cand["decisionYear"] == wiki_year]
                        if len(cand_year) == 1:
                            chosen = cand_year.iloc[0]
                        elif len(cand_year) > 1:
                            # Still ambiguous, but at least filtered by year
                            chosen = cand_year.iloc[0]
                        else:
                            # No exact year match; fall back to first
                            chosen = cand.iloc[0]
                    else:
                        # No wiki year info; fall back to first SCDB row
                        chosen = cand.iloc[0]

        # --- 3) Record matched vs unmatched -------------------------------
        if chosen is None:
            unmatched_rows.append(w_row.to_dict())
        else:
            merged = chosen.to_dict()
            # Attach wiki metadata + views
            merged.update(
                {
                    "wiki_title": w_title,
                    "wiki_usCite": w_row["usCite"],
                    "wiki_docket": w_row["docket"],
                    "views_all_time": w_row["views_all_time"],
                    "views_1yr": w_row["views_1yr"],
                    "views_6mo": w_row["views_6mo"],
                    "views_1mo": w_row["views_1mo"],
                }
            )
            matched_rows.append(merged)

    matched_df = pd.DataFrame(matched_rows)
    unmatched_df = pd.DataFrame(unmatched_rows)

    matched_df.to_csv(OUTPUT_FILE, index=False)
    unmatched_df.to_csv(UNMATCHED_FILE, index=False)

    print("=== SUMMARY ===")
    print(f"Total wiki rows:         {len(wiki)}")
    print(f"Matched SCDB cases:      {len(matched_df)}")
    print(f"Unmatched wiki cases:    {len(unmatched_df)}")
    print(f"Matched + unmatched sum: {len(matched_df) + len(unmatched_df)}")

    if len(wiki) != len(matched_df) + len(unmatched_df):
        print("⚠️ WARNING: counts do NOT add up! Check for logic errors.")
    else:
        print("✅ Sum check passed: matched + unmatched == total wiki rows.")

    print(f"\nMatched output:   {OUTPUT_FILE}")
    print(f"Unmatched output: {UNMATCHED_FILE}")


if __name__ == "__main__":
    main()

