"""
MOAA LAC — House Government Operations Committee monitor.
Called by .github/workflows/monitor-committee.yml
Checks the MI Legislature RSS feed for Government Operations meetings,
fetches each agenda, and flags any that include the MOAA priority bills.
"""
 
import urllib.request
import ssl
import certifi
import xml.etree.ElementTree as ET
import re
import json
import os
import sys
 
# ── Bills to watch ──────────────────────────────────────────────────────────
WATCH_BILLS = ['HB 5262', 'HB 5278', 'HB 5279', 'HB 5280']
BILL_PATTERNS = [
    re.compile(r'\b' + b.replace(' ', r'\s*') + r'\b', re.IGNORECASE)
    for b in WATCH_BILLS
]
 
RSS_URL = 'https://legislature.mi.gov/documents/publications/RssFeeds/comschedule.xml'
 
# Explicit, well-maintained CA bundle — legislature.mi.gov's server doesn't
# send its full certificate chain, which trips up urllib's bare OpenSSL
# verification on GitHub Actions runners (SSLCertVerificationError:
# unable to get local issuer certificate). certifi's bundle resolves it.
_SSL_CTX = ssl.create_default_context(cafile=certifi.where())
 
 
def fetch(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'MOAA-LAC-Monitor/1.0'})
    with urllib.request.urlopen(req, timeout=15, context=_SSL_CTX) as r:
        return r.read().decode('utf-8')
 
 
def set_output(key, value):
    with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
        f.write(f'{key}={value}\n')
 
 
# ── Step 1: Parse RSS, find Government Operations meetings ───────────────────
print("Fetching RSS feed...")
rss_text = fetch(RSS_URL)
root = ET.fromstring(rss_text)
 
gov_ops_meetings = []
for item in root.findall('.//item'):
    title = item.findtext('title') or ''
    link  = item.findtext('link')  or ''
    if 'Government Operations' in title and 'House' in title:
        gov_ops_meetings.append({'title': title, 'link': link})
        print(f"  Found: {title}")
 
if not gov_ops_meetings:
    print("No House Government Operations meetings in RSS feed. Done.")
    set_output('bills_found', 'false')
    sys.exit(0)
 
# ── Step 2: Check each meeting agenda for our bills ──────────────────────────
matches = []
for meeting in gov_ops_meetings:
    print(f"Checking agenda: {meeting['link']}")
    try:
        agenda_html = fetch(meeting['link'])
    except Exception as e:
        print(f"  Warning: could not fetch agenda — {e}")
        continue
 
    found_bills = []
    for i, pattern in enumerate(BILL_PATTERNS):
        if pattern.search(agenda_html):
            found_bills.append(WATCH_BILLS[i])
 
    if found_bills:
        date_match = re.search(
            r'(\d{1,2}/\d{1,2}/\d{4}\s+\d{1,2}:\d{2}\s*[AP]M)',
            meeting['title']
        )
        meeting_date = date_match.group(1) if date_match else 'see agenda'
        matches.append({
            'bills': found_bills,
            'date': meeting_date,
            'url': meeting['link'],
        })
        print(f"  *** MATCH: {found_bills} on agenda for {meeting_date} ***")
    else:
        print("  No MOAA bills on this agenda.")
 
# ── Step 3: Write results for the next workflow step ─────────────────────────
if matches:
    with open('matches.json', 'w') as f:
        json.dump(matches, f)
    all_bills = ', '.join(sorted(set(b for m in matches for b in m['bills'])))
    set_output('bills_found', 'true')
    set_output('bills_list', all_bills)
    print(f"\nTotal matches found: {len(matches)}")
else:
    print("\nNo MOAA bills scheduled in any upcoming Government Operations meeting.")
    set_output('bills_found', 'false')
    set_output('bills_list', '')
