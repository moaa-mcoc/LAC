# Legislative Action Center (LAC)
### Michigan Council of Chapters · Military Officers Association of America

**Live site:** [moaa-mcoc.github.io/LAC](https://moaa-mcoc.github.io/LAC)  
**Current version:** 1.3  
**Maintained by:** LCDR Rich Higgins, USN (Ret.), President, Michigan Council of Chapters, MOAA

---

## Overview

The LAC is a static web application hosted on GitHub Pages that enables MOAA members to contact their Michigan state legislators and U.S. congressional delegation on priority legislation. It requires no backend, no database server, and no CMS. All campaign content is driven by two JSON files in the repository root.

The application is structured as two pages: a discovery page where users read about current bills and select one to act on, and a dedicated action page where they enter their information and send a pre-written, personalized letter to the appropriate legislators.

---

## Repository Files

| File | Purpose |
|---|---|
| `index.html` | Discovery page — hero, bill showcase, resource documents, alerts |
| `action.html` | Action page — bill context, 2-step wizard, letter composer, send |
| `lac-config.json` | Campaign configuration — bills, letter templates, alerts |
| `lac-legislators.json` | Legislator database (162 records) |
| `monitor-status.json` | Written daily by GitHub Actions; displays last monitoring timestamp |
| `.github/workflows/monitor-committee.yml` | Daily GitHub Actions workflow definition |
| `.github/workflows/monitor-committee.py` | Python RSS/agenda monitoring script |
| `README.md` | This file |

---

## User Flow

**1. Discovery — `index.html`**

The user arrives at the discovery page and sees:
- A hero section explaining the issue and the tool
- Four bill showcase cards — HB 5280 as a full-width priority card, the other three in a 2-column grid
- Battle Card and One-Pager resource documents on the HB 5280 card
- An alert banner when committee action is imminent (conditional)
- A committee monitoring status line showing the last automated check

Clicking **"Take action on this bill →"** on any card navigates to `action.html?bill=HB%205280&tab=state` (or whichever bill was selected).

**2. Action — `action.html`**

The user arrives with their chosen bill pre-loaded from the URL. The page shows:
- A context banner confirming the selected bill with a "← Choose a different bill" escape hatch
- **Step 1:** Your information (name, address, ZIP, email, MOAA chapter)
- **Step 2:** Review & send — pre-written letter populated with their details, legislator buttons for each committee member, email delivery options (mailto, Gmail, Outlook web, Yahoo Mail, copy/paste, contact form)
- A phone script for members who prefer to call

---

## Architecture

### URL Scheme

```
index.html                              ← Discovery page
action.html?bill=HB%205280&tab=state    ← State bill, pre-selected
action.html?bill=S.1234&tab=federal     ← Federal bill (when added)
action.html                             ← Defaults to HB 5280 / state
```

### Data Loading

Both pages load `lac-config.json` independently at startup using `fetch()` with `Promise.allSettled()`. Each file also contains in-code fallback bill data so the application remains functional if the JSON fetch fails. `action.html` additionally loads `lac-legislators.json` to resolve committee members and district lookups.

### Bill Targeting Modes

| Mode | Behavior |
|---|---|
| `committee` | Contacts a fixed list of legislators by district number — resolved from `lac-legislators.json` |
| `district` | ZIP code → Google Civic API → database lookup → member's own state rep and senator |
| `delegation` | Michigan U.S. Senators + Civic API lookup for member's U.S. House rep (federal bills) |

### Legislator Database

`lac-legislators.json` contains 162 records covering Michigan House (110), Michigan Senate (37), U.S. House (13), and U.S. Senate (2). Legislators are resolved by district number at runtime — no contact data is stored in `lac-config.json`.

**Record schema:**
```json
{
  "state": "MI",
  "chamber": "MI House",
  "district": "71",
  "name": "Brian BeGole",
  "salutation": "Representative",
  "party": "R",
  "email": "bbeGole@house.mi.gov",
  "phone": "(517) 373-0853",
  "contact_url": "https://www.house.mi.gov/"
}
```

Chamber values: `"MI House"` `"MI Senate"` `"US House"` `"US Senate"`  
U.S. Senate: `"district": null` — U.S. House: `"email": ""` (contact form only)

---

## Configuration

All campaign content is managed in `lac-config.json`. The application reads this file at startup and overrides its in-code fallbacks.

**Top-level structure:**
```json
{
  "state_bills": [...],
  "federal_bills": [...],
  "alerts": [...]
}
```

### Bill Record Schema

```json
{
  "id": 1,
  "code": "HB 5280",
  "priority": true,
  "target": "committee",
  "districts": ["71", "52", "83", "102", "14"],
  "committeeLabel": "House Committee on Government Operations — send to each member",
  "short": "Income Tax Act — retirement pay equity",
  "desc": "Plain-English description shown on the bill card.",
  "url": "https://legislature.mi.gov/...",
  "relatedFederal": null,
  "subject": "Support for HB 5280",
  "body": "Dear Representative [LAST_NAME],\n\n...\n\nRespectfully,\n[FULL_NAME]\n[CITY], Michigan\nMember, [CHAPTER]"
}
```

**Merge fields available in `body`:**  
`[FULL_NAME]` `[LAST_NAME]` `[CITY]` `[ZIP]` `[ADDRESS]` `[EMAIL]` `[CHAPTER]` `[SALUTATION]`

### Alert Record Schema

```json
{
  "tab": "state",
  "headline": "HB 5280 scheduled for committee hearing",
  "desc": "The House Committee on Government Operations has scheduled HB 5280 for a hearing.",
  "bill_code": "HB 5280",
  "info_url": "https://...",
  "info_label": "View hearing notice ↗",
  "expires": "2026-06-30"
}
```

`tab` values: `"state"` `"federal"` `"both"`  
Alerts auto-expire based on the `expires` date. Set to `"2099-12-31"` for a standing alert.  
The "Contact legislators now" button on an alert links directly to `action.html?bill=HB%205280&tab=state`.

---

## Current State Bills

All four bills target the **House Committee on Government Operations** (districts 71, 52, 83, 102, 14).

| Bill | Title | Priority |
|---|---|---|
| HB 5280 | Income Tax Act — retirement pay equity | ★ Yes |
| HB 5262 | Uniformity of Service Dates Act | No |
| HB 5278 | State Personal Identification Card Act | No |
| HB 5279 | Michigan Vehicle Code | No |

The `federal_bills` array is currently empty. The Federal tab on `index.html` displays "Coming Soon." Infrastructure for `target: "delegation"` is fully in place.

---

## Adding a Federal Bill

Add an entry to the `federal_bills` array in `lac-config.json`:

```json
{
  "id": 1,
  "code": "H.R.1234",
  "priority": true,
  "target": "delegation",
  "short": "Short title of the bill",
  "desc": "One or two sentence plain-English description.",
  "url": "https://www.congress.gov/bill/...",
  "relatedState": "HB 5280",
  "subject": "Please support H.R.1234 — Short Title",
  "body": "Dear [SALUTATION] [LAST_NAME],\n\n...\n\nRespectfully,\n[FULL_NAME]\n[CITY], Michigan\nMember, [CHAPTER]"
}
```

The Federal tab badge changes from "Coming Soon" to the bill count automatically once at least one federal bill is present.

---

## Automated Committee Monitoring

A GitHub Actions workflow runs daily at **7:00 AM Eastern**.

**Behavior:**
1. Fetches the Michigan Legislature RSS feed
2. Checks House Government Operations Committee agendas for HB 5262, 5278, 5279, and 5280
3. If a match is found, creates a GitHub Issue (triggers email notification to the maintainer) with a pre-filled `lac-config.json` alert block ready to paste in
4. Writes `monitor-status.json` to the repo — `index.html` reads this at startup and displays the last-checked timestamp in the state tab

**Workflow files:**
- `.github/workflows/monitor-committee.yml`
- `.github/workflows/monitor-committee.py`

**Actions used:** `actions/checkout@v5` · `actions/github-script@v8` (Node.js 24 compatible)

---

## Analytics

Google Analytics 4 · Measurement ID: **G-J7VGNRJQ98**

Custom events fired:

| Event | Fired when |
|---|---|
| `page_visit` | Either page loads |
| `bill_selected` | User arrives at `action.html` with a bill parameter |
| `step_complete` | User advances past Step 1 on `action.html` |
| `zip_lookup` | Legislator lookup attempted (district or delegation targeting) |
| `email_choice` | User clicks a send method (mailto, Gmail, Outlook, Yahoo, copy, contact form) |
| `alert_displayed` | An action alert banner is rendered |
| `tab_switch` | User switches tabs on `index.html` |
| `config_loaded` | External JSON loaded successfully |

A password-protected **metrics dashboard** is accessible via `Ctrl+Alt+M` or `index.html#metrics`. It displays aggregate counts and a recent activity log from `localStorage`, exportable as CSV. Password is set in the `LAC_ADMIN_PASSWORD` constant in `index.html`.

---

## Key Constants

| Constant | Location | Value |
|---|---|---|
| GA4 Measurement ID | Both files | `G-J7VGNRJQ98` |
| Google Civic API key | `action.html` | `YOUR_API_KEY_HERE` |
| Admin password | `index.html` | `ChangeMe2026!` |
| MCOC logo URL | Both files | `https://www.moaamcoc.com/uploads/1/4/8/4/148483887/published/mcoc-logo.png?1740860645` |
| Config URL | Both files | `lac-config.json` |
| Legislators URL | `action.html` | `lac-legislators.json` |

---

## Outstanding Items

- [ ] Verify phone numbers and individual email addresses in `lac-legislators.json` against official directories
- [ ] Add individual contact form URLs for MI House members (currently all point to general `house.mi.gov`)
- [ ] MI Senate district 35 — populate when replacement is seated
- [ ] Federal campaigns (GUARD VA Benefits Act, CHOICE Act) — add to `federal_bills` when approved
- [ ] Per-state bill file structure (`/legislation/michigan.json`) — deferred to v1.4 when second council adopts the LAC
- [ ] Server-backed dashboard for centralized cross-user reporting — future version

---

## Enterprise Licensing

The LAC is available to MOAA councils nationwide as a turnkey advocacy tool.

- **Setup fee:** $1,000 (501(c)(3) contribution to SE Michigan Chapter MOAA Scholarship Fund)
- **Annual maintenance:** $400
- **Onboarding materials:** `LAC-Program-Brief.html` · `LAC-Onboarding-Checklist.md`
- **Forum presentation:** MOAA State Legislation Exchange, July 21, 2026

Contact: LCDR Rich Higgins, USN (Ret.) — [moaamcoc.com](https://www.moaamcoc.com)

---

*Last updated: June 2026 · Version 1.3*
