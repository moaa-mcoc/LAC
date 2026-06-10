# Legislative Action Center — Version 1.2

## Repository files

| File | Purpose |
|---|---|
| `index.html` | Application — LAC v1.2 |
| `lac-config.json` | Campaign configuration: bills, targets, letter templates, alerts |
| `lac-legislators.json` | Legislator database: 162 records (110 MI House, 37 MI Senate, 13 US House, 2 US Senate) |
| `.github/workflows/monitor-committee.yml` | Daily GitHub Actions workflow — monitors committee schedule |
| `.github/workflows/monitor-committee.py` | Python script — RSS fetch and agenda parsing logic |
| `README.md` | This file |

---

## What changed in Version 1.2

### 1. Legislator database (`lac-legislators.json`)

A standalone legislator database replaces the inline contact lists previously embedded in `lac-config.json`. Each record follows this schema:

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

**Chamber values:** `"MI House"`, `"MI Senate"`, `"US House"`, `"US Senate"`

U.S. Senate records use `"district": null` (statewide). U.S. House members use `contact_url` only — no direct email address is published. The chamber naming convention is state-prefixed to support future reuse by councils in other states.

The database is loaded at startup alongside `lac-config.json` using `Promise.allSettled()`. A missing file degrades gracefully without blocking the other.

### 2. District-based bill targeting

Bill entries in `lac-config.json` now use a `districts` array instead of inline legislator objects for committee targets. The app resolves district numbers against the database at runtime:

```json
{
  "target": "committee",
  "districts": ["71", "52", "83", "102", "14"],
  "committeeLabel": "House Committee on Government Operations — send to each member"
}
```

**Target modes:**

| `target` | Behavior |
|---|---|
| `"committee"` | Contacts legislators in `districts`, resolved from the database |
| `"district"` | ZIP → Google Civic API → matched against database by district number |
| `"delegation"` | MI U.S. Senators (from database) + member's U.S. House rep (Civic API) |

### 3. Action alert banner

`lac-config.json` supports an `alerts` array. Active alerts display as a prominent red banner above the issue banner on the relevant tab. Alerts expire automatically based on the `expires` field — no manual cleanup needed.

```json
{
  "alerts": [
    {
      "tab": "state",
      "headline": "HB 5280 scheduled for committee hearing",
      "desc": "The House Committee on Government Operations has scheduled HB 5280 for a hearing on 6/15/2026 09:00 AM. Now is the time to contact committee members.",
      "bill_code": "HB 5280",
      "info_url": "https://legislature.mi.gov/Committees/Meeting?meetingID=XXXX",
      "info_label": "View hearing notice ↗",
      "expires": "2026-06-16"
    }
  ]
}
```

`tab` accepts `"state"`, `"federal"`, or `"both"`. Set `expires` to the day after the hearing. The alert clears automatically at midnight on that date.

### 4. Automated committee monitoring

A GitHub Actions workflow runs every morning at 7:00 AM Eastern. It checks the Michigan Legislature RSS feed for House Government Operations Committee meetings and fetches each agenda looking for HB 5262, 5278, 5279, or 5280. If a match is found, it creates a GitHub Issue in the repo — GitHub automatically emails the repo owner. The issue contains the exact JSON block to paste into `lac-config.json`, with only the `expires` date to fill in.

The workflow can also be triggered manually from the Actions tab at any time.

### 5. `state_committee` and `mi_senators` removed from `lac-config.json`

All legislator data is now sourced from `lac-legislators.json`. The app still honors these fields if present in the config for backward compatibility, but they should not be included in new configurations.

---

## Bill configuration reference

```json
{
  "id": 1,
  "code": "HB 5280",
  "priority": true,
  "target": "committee",
  "districts": ["71", "52", "83", "102", "14"],
  "committeeLabel": "House Committee on Government Operations — send to each member",
  "short": "Short title shown on the bill card",
  "desc": "One or two sentence description shown on the bill card.",
  "url": "https://legislature.mi.gov/...",
  "relatedFederal": null,
  "subject": "Email subject line",
  "body": "Dear Representative [LAST_NAME],\n\n...\n\nRespectfully,\n[FULL_NAME]\n[CITY], Michigan\nMember, [CHAPTER]"
}
```

**Merge fields available in `body`:** `[FULL_NAME]`, `[LAST_NAME]`, `[SALUTATION]`, `[CITY]`, `[ZIP]`, `[ADDRESS]`, `[EMAIL]`, `[CHAPTER]`

**Statewide floor-vote campaign:** Add a bill entry with `"target": "district"` and no `districts` array. The Civic API and database handle all 110 House and 38 Senate members automatically based on the user's address.

---

## When a committee alert is triggered

The GitHub Actions workflow will create an Issue in this repo and email you. The issue contains a pre-filled alert JSON block. Steps to activate the alert:

1. Open `lac-config.json` in the repo
2. Add the JSON block from the issue into the `alerts` array
3. Set `expires` to the day after the hearing date (`YYYY-MM-DD`)
4. Commit — the alert banner goes live on the LAC immediately
5. Close the GitHub Issue once the alert is live

To clear the alert after the hearing: set `expires` to a past date and commit, or delete the entry from the `alerts` array.

---

## Deployment steps (new council)

1. Commit all files to the repo root: `index.html`, `lac-config.json`, `lac-legislators.json`
2. Commit `.github/workflows/monitor-committee.yml` and `.github/workflows/monitor-committee.py`
3. Replace `YOUR_API_KEY_HERE` in `index.html` with a Google Civic Information API key
4. Change the default admin password in `index.html`:
   ```js
   const LAC_ADMIN_PASSWORD = 'ChangeMe2026!';
   ```
5. Create the `committee-alert` label in the repo (Issues → Labels → New label)
6. Test:
   - State bill selection and committee email flow
   - District lookup (requires a valid Google Civic API key)
   - Gmail / Outlook / Yahoo / AOL fallback links
   - Copy message and contact form links
   - Federal tab (shows "Coming Soon" until a federal bill is added)
   - Metrics dashboard via `#metrics` or `Ctrl+Alt+M`
   - Metrics CSV export
   - GitHub Actions workflow via manual trigger (Actions tab → Run workflow)

---

## Maintaining the legislator database

`lac-legislators.json` should be reviewed each January ahead of the new legislative session and updated whenever a seat changes hands.

- **MI House emails:** `FirstnameLastname@house.mi.gov` — verify at [house.mi.gov/AllRepresentatives](https://www.house.mi.gov/AllRepresentatives)
- **MI Senate emails:** `Sen[FI][Lastname]@senate.michigan.gov` — verify at [senate.michigan.gov/senators/all-senators](https://senate.michigan.gov/senators/all-senators/)
- **MI Senate district 35** is currently vacant — add the record when a replacement is seated
- **US House members** use `contact_url` only; `email` is intentionally blank
- Phone numbers should be verified against official directories; some currently reflect general switchboard numbers

---

## Monitoring workflow maintenance

The workflow uses `actions/checkout@v5` and `actions/github-script@v8`, compatible with Node.js 24 (required after September 16, 2026).

To update the list of bills being monitored, edit `WATCH_BILLS` in `.github/workflows/monitor-committee.py`:

```python
WATCH_BILLS = ['HB 5262', 'HB 5278', 'HB 5279', 'HB 5280']
```

Add or remove bill codes as campaigns change. No other changes are needed.

---

## Important limitation

Because this is a static website using mailto and webmail links, it cannot verify that an email was actually sent. Metrics track visits, lookups, email attempts, copy-and-send actions, contact form clicks, ZIP codes, chapters, and bill selections — stored locally in the user's browser and reported via GA4. Centralized reporting across all users requires GA4 or a future server-backed version.

---

## Recommended next improvements

- Verify and update all phone numbers in `lac-legislators.json` against official directories.
- Add individual contact form URLs for MI House members (currently all point to the general `house.mi.gov` directory).
- Add federal campaigns to `lac-config.json` when ready (GUARD VA Benefits Act, CHOICE Act, etc.).
- Build a server-backed dashboard for centralized cross-user campaign reporting.
- **Per-state bill files (v1.3 candidate):** When a second state council adopts the LAC, refactor campaign bills into a `/legislation/` folder with one file per state (e.g., `michigan.json`, `ohio.json`) plus a shared `federal.json` for bill descriptions that apply across states. The right trigger for this refactor is managing bills for two states simultaneously — `lac-config.json` works well for a single-state deployment and this complexity is not yet warranted.
