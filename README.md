# Legislative Action Center (LAC)
### Michigan Council of Chapters · Military Officers Association of America

**Live site:** [moaa-mcoc.github.io/LAC](https://moaa-mcoc.github.io/LAC)
**Current version:** 1.5
**Maintained by:** LCDR Rich Higgins, USN (Ret.), President, Michigan Council of Chapters, MOAA

---

## Overview

The LAC is a static web application hosted on GitHub Pages that enables MOAA members to contact their Michigan state legislators and U.S. congressional delegation on priority legislation. It requires no backend, no database server, and no CMS. All campaign content is driven by JSON files in the repository root.

The application is structured as two pages: a discovery page where users read about current bills and select one to act on, and a dedicated action page where they enter their information and send a pre-written, personalized letter to the appropriate legislators.

---

## Repository Files

| File | Purpose |
|---|---|
| `index.html` | Discovery page — hero, state/federal tabs, bill list, alerts, bill tracker |
| `action.html` | Action page — bill context, 2-step wizard, letter composer, send |
| `lac-config.json` | Campaign configuration — bills, letter templates, alerts. Source of truth at runtime. |
| `lac-fallback-data.js` | Single shared copy of `STATE_BILLS`/`FEDERAL_BILLS` fallback data, loaded by both `index.html` and `action.html` before their own inline scripts. Used only if `lac-config.json` fails to fetch. **This is the only place fallback bill data should be edited** — see Data Loading below. |
| `lac-legislators.json` | Legislator database |
| `bills.json` | LegiScan bill-status data, read by `index.html`'s bill tracker and status badges. Updated automatically — see Automated Committee Monitoring & Bill Status. |
| `monitor-status.json` | Written by GitHub Actions on each committee-monitoring run; displays last-checked timestamp on the state tab |
| `Census-Geocoder-Worker.js` | Source for the Cloudflare Worker (`lac-csnsus-proxy`) that proxies the U.S. Census Bureau Geocoder and adds CORS headers. Deployed separately to Cloudflare — this file in the repo is the source copy, not something GitHub Pages serves or executes. |
| `scripts/fetch-bill-status.mjs` | Node script that queries LegiScan and writes `bills.json` |
| `.github/workflows/monitor-committee.yml` | Daily GitHub Actions workflow — RSS/agenda monitoring |
| `.github/workflows/*` (bill status) | Scheduled workflow that runs `fetch-bill-status.mjs` and commits the resulting `bills.json` |
| `README.md` | This file |

---

## User Flow

**1. Discovery — `index.html`**

The user arrives at the discovery page and sees:
- A hero section explaining the issue and the tool
- Two tabs: **State Legislation** and **Federal Legislation**, each badged with a live count
- On the State tab, bills are grouped into sections and rendered as list rows (not cards): an **"Ask Your Own State Legislators"** section for district-targeted bills, followed by one section per committee for committee-targeted bills (e.g., "House Committee on Government Operations," "Senate Committee on Health Policy")
- A "send one email for all House bills" row when more than one House bill shares a committee
- A live **Michigan Bill Tracker** table (from `bills.json`) showing LegiScan status badges when status data is available
- On the Federal tab, bills render as full cards with resource-document links
- An alert banner when committee action is imminent (conditional, per bill/tab)
- A committee monitoring status line showing the last automated RSS check

Clicking a bill's action button navigates to `action.html?bill=<code>&tab=state` or `&tab=federal`.

**2. Action — `action.html`**

The user arrives with their chosen bill pre-loaded from the URL. The page shows:
- A context banner confirming the selected bill, with a resource link (label configurable per bill — see `urlLabel` below) and a "← Choose a different bill" escape hatch
- **Step 1:** Your information (name, address, ZIP, email, MOAA chapter)
- **Step 2:** Review & send — pre-written letter populated with their details, legislator buttons resolved by target mode (see below), email delivery options (mailto, Gmail, Outlook web, Yahoo Mail, copy/paste, contact form)
- A phone script for members who prefer to call, generated per bill (see Phone Scripts below)

---

## Architecture

### URL Scheme

```
index.html                              ← Discovery page
action.html?bill=HB%205280&tab=state    ← Committee-targeted state bill
action.html?bill=Richard%20Star%20Act%20—%20MI%20State%20Resolution&tab=state   ← District-targeted state bill
action.html?bill=SEACR%20Act%20of%202026&tab=federal                            ← Delegation-targeted federal bill
action.html?bill=ALL&tab=state          ← Synthetic "send one email for all House bills" flow
action.html                             ← Defaults to HB 5280 / state
```

### Data Loading

Both pages load `lac-config.json` independently at startup using `fetch()` with `Promise.allSettled()`. If that fetch fails, both pages fall back to in-code bill data.

**That fallback data lives in exactly one place: `lac-fallback-data.js`.** It's loaded via a `<script src="lac-fallback-data.js">` tag in both `index.html` and `action.html`, placed immediately before each page's own inline `<script>` block, so `STATE_BILLS`/`FEDERAL_BILLS` are declared and populated before either page's code runs. `loadExternalData()` in both pages reassigns these same variables if the `lac-config.json` fetch succeeds.

This replaced an earlier design where each HTML file carried its own duplicate copy of the fallback arrays — those two copies drifted out of sync more than once (most notably, `action.html`'s fallback was missing an entire bill entry that `index.html`'s had). Do not reintroduce inline `STATE_BILLS`/`FEDERAL_BILLS` array literals in either HTML file — add new bills to `lac-fallback-data.js` instead, and keep `lac-config.json` in sync with it by hand (see Adding a Bill below).

`action.html` additionally loads `lac-legislators.json` to resolve legislators. `index.html` additionally loads `bills.json` (LegiScan status) and `monitor-status.json` (last RSS check).

### Bill Targeting Modes

All three modes below are implemented and in active use.

| Mode | Behavior | Legislator resolution |
|---|---|---|
| `committee` | Contacts a fixed list of legislators by district number | Districts listed in the bill's `districts` array, resolved against `lac-legislators.json` |
| `district` | Contacts the user's own Michigan state representative and state senator | User's address is geocoded (see below), resolved to MI House and MI Senate districts, matched against `lac-legislators.json` |
| `delegation` | Contacts Michigan's two U.S. Senators plus the user's own U.S. House representative | MI's two U.S. Senators are pulled directly from `lac-legislators.json`; the House rep is resolved the same way as `district` mode, but against the congressional district layer |

**Geocoding note:** Legislator lookups by address use the **U.S. Census Bureau Geocoder**, proxied through a Cloudflare Worker (source in `Census-Geocoder-Worker.js`, deployed as `lac-csnsus-proxy`) that adds CORS headers, since the Census API itself doesn't send them. This replaced the Google Civic Information API's "Representatives" endpoint, which Google retired on April 30, 2025. No API key is required for the Census Geocoder.

### Legislator Database

`lac-legislators.json` contains legislator records covering Michigan House, Michigan Senate, U.S. House, and U.S. Senate. Legislators are resolved by chamber + district number at runtime — no contact data is stored in `lac-config.json`.

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
  "chamber": "house",
  "code": "HB 5280",
  "code2": null,
  "priority": true,
  "target": "committee",
  "districts": ["71", "52", "83", "102", "14"],
  "committeeLabel": "House Committee on Government Operations — send to each member",
  "short": "Income Tax Act — retirement pay equity",
  "desc": "Plain-English description shown on the bill card/row.",
  "url": "https://legislature.mi.gov/...",
  "urlLabel": null,
  "url2": null,
  "battleCard": null,
  "onePager": null,
  "resources": null,
  "relatedFederal": null,
  "subject": "Support for HB 5280",
  "body": "Dear Representative [LAST_NAME],\n\n...\n\nRespectfully,\n[FULL_NAME]\n[CITY], Michigan\nMember, [CHAPTER]",
  "phoneScript": null
}
```

| Field | Required | Notes |
|---|---|---|
| `chamber` | State bills only | `"house"` or `"senate"` — determines which committee section a `committee`-target bill renders under. Not used for `district`-target bills, which render in their own section regardless of this field. |
| `code2` / `url2` | Optional | For tie-barred companion bill pairs (e.g., HB 5456/5457) |
| `committeeLabel` | Required for `target: "committee"` | Shown as the recommendation header on the action page |
| `urlLabel` | Optional | Overrides the link text next to `url` on both the bill row (`index.html`) and the context banner (`action.html`). Defaults to `"View bill ↗"` on the row and `"View full bill text ↗"` on the banner if omitted. Use this for anything that isn't actual bill text — e.g., a model resolution template — so the link doesn't misleadingly say "bill text." |
| `battleCard` / `onePager` | Optional, state bills | Resource PDF links shown on the bill row |
| `resources` | Optional, federal bills | Array of `{label, url}` PDF links shown on the federal card |
| `relatedFederal` / `relatedState` | Optional | Cross-reference text; not currently rendered in the UI, informational only |
| `phoneScript` | Optional | See Phone Scripts below |

**Merge fields available in `body`:**
`[FULL_NAME]` `[LAST_NAME]` `[CITY]` `[ZIP]` `[ADDRESS]` `[EMAIL]` `[CHAPTER]` `[SALUTATION]`

### Phone Scripts

Each bill can supply an optional `phoneScript` field. If omitted, a default template is used: *"...ask for your support in moving [CODE] forward in committee..."* — accurate for a bill actively in committee, but wrong framing for something like a resolution that hasn't been introduced yet, so those bills should supply their own `phoneScript`.

**Merge fields available in `phoneScript` are more limited than in `body`:** only `[FULL_NAME]`, `[CHAPTER]`, and `[CODE]`. This is because the phone script is generated once on the page, before any specific legislator has been looked up or chosen — `[LAST_NAME]` and `[SALUTATION]` aren't available at that point. Phone scripts for `district`/`delegation`-target bills should speak generically ("your representative or senator") rather than naming a specific legislator.

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
The "Contact legislators now" button on an alert links directly to `action.html?bill=<code>&tab=<tab>`.

---

## Current Bills

### State Tab

| Bill | Title | Target | Priority |
|---|---|---|---|
| HB 5280 | Income Tax Act — retirement pay equity | `committee` (House Gov't Ops) | ★ Yes |
| HB 5262 | Uniformity of Service Dates Act | `committee` (House Gov't Ops) | No |
| HB 5278 | State Personal Identification Card Act | `committee` (House Gov't Ops) | No |
| HB 5279 | Michigan Vehicle Code | `committee` (House Gov't Ops) | No |
| HB 5456 & HB 5457 | Hyperbaric Oxygen Therapy Pilot Program | `committee` (Senate Health Policy) | ★ Yes |
| Richard Star Act — MI State Resolution | Ask your legislator to introduce a resolution supporting the federal Major Richard Star Act (H.R. 2102 / S. 1032) | `district` | ★ Yes |

The Richard Star Act entry is architecturally distinct from the others: it's not asking users to support a pending Michigan bill, but to ask their own state rep or senator to *introduce* a resolution. Its `url` points to a model resolution template rather than bill text, so it uses `urlLabel: "View Resolution Template ↗"` to avoid the default "View bill" / "View full bill text" wording. Once Michigan actually introduces a resolution, this entry should be updated: switch `target` to `committee`, add the real bill number to `code`, drop or repurpose `urlLabel` once `url` points to actual bill text, and rewrite `body`/`phoneScript` from "will you introduce" framing to "please support" framing.

### Federal Tab

| Bill | Title | Target | Priority |
|---|---|---|---|
| SEACR Act of 2026 | Submarine Exposure and Combat Recognition Act | `delegation` | ★ Yes |

---

## Adding a Bill

**State bill**, add to `state_bills`:
- `target: "committee"` for a bill in front of a specific committee — set `chamber`, `districts`, and `committeeLabel`
- `target: "district"` for a "contact your own legislator" ask — no `districts`/`committeeLabel` needed
- Set `urlLabel` if `url` doesn't point to actual bill text (e.g., a resolution template, a one-pager, a toolkit)

**Federal bill**, add to `federal_bills` with `target: "delegation"`:
```json
{
  "id": 2,
  "code": "H.R.1234",
  "priority": true,
  "target": "delegation",
  "short": "Short title of the bill",
  "desc": "One or two sentence plain-English description.",
  "url": "https://www.congress.gov/bill/...",
  "resources": [ { "label": "One-Pager", "url": "https://..." } ],
  "relatedState": null,
  "subject": "Please support H.R.1234 — Short Title",
  "body": "Dear [SALUTATION] [LAST_NAME],\n\n...\n\nRespectfully,\n[FULL_NAME]\n[CITY], Michigan\nMember, [CHAPTER]"
}
```

**Two places to update, not three:** `lac-config.json` is the source of truth at runtime, and `lac-fallback-data.js` is the single shared fallback used by both pages if the config fetch fails. Add the same bill object (field-for-field identical) to both. Do **not** add bill data directly inside `index.html` or `action.html` — the shared fallback file exists specifically so there's only one fallback copy to maintain.

---

## Automated Committee Monitoring & Bill Status

Two independent pieces of automation keep the site's bill information current without manual editing.

**1. Committee agenda monitoring** — a GitHub Actions workflow (`.github/workflows/monitor-committee.yml`) runs daily at **7:00 AM Eastern**:
1. Fetches the Michigan Legislature RSS feed
2. Checks tracked committee agendas for tracked bill numbers
3. If a match is found, creates a GitHub Issue (triggers email notification to the maintainer) with a pre-filled `lac-config.json` alert block ready to paste in
4. Writes `monitor-status.json` to the repo — `index.html` reads this at startup and displays the last-checked timestamp in the state tab

**2. LegiScan bill status** — a scheduled workflow runs `scripts/fetch-bill-status.mjs`, which queries the LegiScan API and commits the result to `bills.json`. `index.html` reads `bills.json` at startup and renders a **Michigan Bill Tracker** table plus color-coded status badges (Introduced, In Committee, Engrossed, Passed, etc.) next to each bill row. This runs on its own schedule, independent of the RSS monitor above.

**Actions used:** `actions/checkout@v5` · `actions/github-script@v8` (Node.js 24 compatible)

---

## Analytics

Google Analytics 4 · Measurement ID: **G-J7VGNRJQ98**

Custom events fired:

| Event | Fired when |
|---|---|
| `page_visit` | Either page loads |
| `bill_selected` | User arrives at `action.html` with a bill parameter |
| `bill_card_rendered` | A bill row/card is rendered on `index.html` |
| `step_complete` | User advances past Step 1 on `action.html` |
| `zip_lookup` | Legislator lookup attempted (`district` or `delegation` targeting) |
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
| Census Geocoder proxy (Cloudflare Worker) | `action.html` | `https://lac-csnsus-proxy.team-86d.workers.dev` — no API key needed; source in `Census-Geocoder-Worker.js` |
| Admin password | Both files | `ChangeMe2026!` |
| MCOC logo URL | `index.html` | `https://www.moaamcoc.com/uploads/1/4/8/4/148483887/published/mcoc-logo.png?1740860645` |
| Config URL | Both files | `lac-config.json` |
| Fallback data script | Both files | `lac-fallback-data.js` |
| Legislators URL | Both files | `lac-legislators.json` |
| Bill status URL | `index.html` | `bills.json` |

---

## Outstanding Items

- [ ] Verify phone numbers and individual email addresses in `lac-legislators.json` against official directories
- [ ] Add individual contact form URLs for MI House members (currently many point to the general `house.mi.gov`)
- [ ] MI Senate district 35 — populate when replacement is seated
- [ ] Add Take Action gating logic to suppress the action button for bills that are dead or already enacted
- [ ] Update the Richard Star Act entry once Michigan actually introduces a state resolution — switch `target` from `district` to `committee`, add the real bill number, and rewrite the letter/phone-script framing
- [ ] Consider a lightweight CI check that flags (not blocks) a PR where `lac-config.json` and `lac-fallback-data.js` list different bill `code` values — `lac-fallback-data.js` removed the two-HTML-files drift risk, but the config file and the fallback file are still two hand-maintained copies of the same data
- [ ] Per-state bill file structure (`/legislation/michigan.json`) — deferred to a future version when a second council adopts the LAC
- [ ] Server-backed dashboard for centralized cross-user reporting — future version

---

*Last updated: August 2026 · Version 1.5*
