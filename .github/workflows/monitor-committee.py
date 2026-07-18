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

# legislature.mi.gov's server only sends its leaf certificate and never the
# intermediate that issued it (confirmed via `openssl s_client -showcerts`:
# depth=0 only, verify error 21 "unable to verify the first certificate").
# certifi ships root CAs, not intermediates, so it can't bridge that gap on
# its own — we bundle the missing intermediate explicitly. Fetched from
# DigiCert's repo: https://cacerts.digicert.com/DigiCertGlobalG2TLSRSASHA2562020CA1-1.crt
# (issued by DigiCert Global Root G2, which is in certifi's bundle).
_DIGICERT_G2_TLS_RSA_SHA256_2020_CA1 = """-----BEGIN CERTIFICATE-----
MIIEyDCCA7CgAwIBAgIQDPW9BitWAvR6uFAsI8zwZjANBgkqhkiG9w0BAQsFADBh
MQswCQYDVQQGEwJVUzEVMBMGA1UEChMMRGlnaUNlcnQgSW5jMRkwFwYDVQQLExB3
d3cuZGlnaWNlcnQuY29tMSAwHgYDVQQDExdEaWdpQ2VydCBHbG9iYWwgUm9vdCBH
MjAeFw0yMTAzMzAwMDAwMDBaFw0zMTAzMjkyMzU5NTlaMFkxCzAJBgNVBAYTAlVT
MRUwEwYDVQQKEwxEaWdpQ2VydCBJbmMxMzAxBgNVBAMTKkRpZ2lDZXJ0IEdsb2Jh
bCBHMiBUTFMgUlNBIFNIQTI1NiAyMDIwIENBMTCCASIwDQYJKoZIhvcNAQEBBQAD
ggEPADCCAQoCggEBAMz3EGJPprtjb+2QUlbFbSd7ehJWivH0+dbn4Y+9lavyYEEV
cNsSAPonCrVXOFt9slGTcZUOakGUWzUb+nv6u8W+JDD+Vu/E832X4xT1FE3LpxDy
FuqrIvAxIhFhaZAmunjZlx/jfWardUSVc8is/+9dCopZQ+GssjoP80j812s3wWPc
3kbW20X+fSP9kOhRBx5Ro1/tSUZUfyyIxfQTnJcVPAPooTncaQwywa8WV0yUR0J8
osicfebUTVSvQpmowQTCd5zWSOTOEeAqgJnwQ3DPP3Zr0UxJqyRewg2C/Uaoq2yT
zGJSQnWS+Jr6Xl6ysGHlHx+5fwmY6D36g39HaaECAwEAAaOCAYIwggF+MBIGA1Ud
EwEB/wQIMAYBAf8CAQAwHQYDVR0OBBYEFHSFgMBmx9833s+9KTeqAx2+7c0XMB8G
A1UdIwQYMBaAFE4iVCAYlebjbuYP+vq5Eu0GF485MA4GA1UdDwEB/wQEAwIBhjAd
BgNVHSUEFjAUBggrBgEFBQcDAQYIKwYBBQUHAwIwdgYIKwYBBQUHAQEEajBoMCQG
CCsGAQUFBzABhhhodHRwOi8vb2NzcC5kaWdpY2VydC5jb20wQAYIKwYBBQUHMAKG
NGh0dHA6Ly9jYWNlcnRzLmRpZ2ljZXJ0LmNvbS9EaWdpQ2VydEdsb2JhbFJvb3RH
Mi5jcnQwQgYDVR0fBDswOTA3oDWgM4YxaHR0cDovL2NybDMuZGlnaWNlcnQuY29t
L0RpZ2lDZXJ0R2xvYmFsUm9vdEcyLmNybDA9BgNVHSAENjA0MAsGCWCGSAGG/WwC
ATAHBgVngQwBATAIBgZngQwBAgEwCAYGZ4EMAQICMAgGBmeBDAECAzANBgkqhkiG
9w0BAQsFAAOCAQEAkPFwyyiXaZd8dP3A+iZ7U6utzWX9upwGnIrXWkOH7U1MVl+t
wcW1BSAuWdH/SvWgKtiwla3JLko716f2b4gp/DA/JIS7w7d7kwcsr4drdjPtAFVS
slme5LnQ89/nD/7d+MS5EHKBCQRfz5eeLjJ1js+aWNJXMX43AYGyZm0pGrFmCW3R
bpD0ufovARTFXFZkAdl9h6g4U5+LXUZtXMYnhIHUfoyMo5tS58aI7Dd8KvvwVVo4
chDYABPPTHPbqjc1qCmBaZx2vN4Ye5DUys/vZwP9BFohFrH/6j/f3IL16/RZkiMN
JCqVJUzKoZHm1Lesh3Sz8W2jmdv51b2EQJ8HmA==
-----END CERTIFICATE-----
"""

_SSL_CTX = ssl.create_default_context(cafile=certifi.where())
_SSL_CTX.load_verify_locations(cadata=_DIGICERT_G2_TLS_RSA_SHA256_2020_CA1)


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
