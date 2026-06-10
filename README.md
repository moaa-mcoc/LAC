# Legislative Action Center — Version 1.2

## Files

- `index.html` — Legislative Action Center, v1.2.
- `lac-config.json` — Campaign configuration: bills, targets, letter templates.
- `lac-legislators.json` — Legislator database: all 110 MI House members, 37 MI Senate members (district 35 currently vacant), and 2 U.S. Senators.

## What changed in Version 1.2

### 1. Legislator database (`lac-legislators.json`)

A standalone legislator database replaces the inline contact lists that were previously embedded in `lac-config.json`. Each record follows this schema:

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

U.S. Senate records use `"district": null` (statewide). The chamber naming convention is state-prefixed (`MI House`, `MI Senate`) to support future reuse by councils in other states.

The database is loaded at startup alongside `lac-config.json`. If the file is missing, the app falls back to any inline legislator data in `lac-config.json` (v1.1 behavior), then to built-in defaults.

### 2. District-based bill targeting

Bill entries in `lac-config.json` now use a `districts` array instead of inline legislator objects for committee targets. The app resolves district numbers against the database at runtime:

```json
{
  "target": "committee",
  "districts": ["71", "52", "83", "102", "14"],
  "committeeLabel": "House Committee on Government Operations — send to each member"
}
```

The optional `committeeLabel` field controls the recipient header shown to the user in Step 3. If omitted, a generic label is used.

**Target modes (unchanged from v1.1):**

| `target` | Behavior |
|---|---|
| `"committee"` | Contacts the legislators listed in `districts`, resolved from the database |
| `"district"` | ZIP → Google Civic API lookup → matched against the database by district number |
| `"delegation"` | MI U.S. Senators (from database) + member's U.S. House rep (Civic API) |

### 3. Parallel file loading

`loadExternalData()` replaces `loadExternalConfig()`. Both files are fetched simultaneously using `Promise.allSettled()`. A missing or invalid file degrades gracefully without blocking the other.

The `config-status` line visible to administrators now reports which files loaded successfully.

### 4. Database-backed district lookup

When a bill uses `target: "district"`, the app calls the Google Civic API to determine the user's state House and Senate district numbers, then cross-references those numbers against `lac-legislators.json` to retrieve verified email addresses, phone numbers, and contact form URLs. If no database match is found for a given district, the app falls back to whatever contact details the Civic API returned directly.

The same pattern applies to federal `target: "delegation"` bills — the U.S. House district number from the Civic API is matched against the database.

### 5. `state_committee` and `mi_senators` removed from `lac-config.json`

These blocks are no longer needed. All legislator data is sourced from `lac-legislators.json`. The app still honors these fields if present in the config (for backward compatibility with any cached or forked versions), but they should not be included in new configurations.

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

**Statewide floor-vote campaign:** Add a new bill entry with `"target": "district"` and no `districts` array. The Civic API and database handle all 110 House and 38 Senate members automatically based on the user's address.

---

## Deployment steps

1. Commit or upload all three files to the repo root: `index.html`, `lac-config.json`, `lac-legislators.json`.
2. Replace `YOUR_API_KEY_HERE` in `index.html` with your Google Civic Information API key.
3. Change the default admin password in `index.html` before posting publicly:
   ```js
   const LAC_ADMIN_PASSWORD = 'ChangeMe2026!';
   ```
4. Test:
   - State bill selection and committee email flow
   - District lookup (requires a valid Google Civic API key)
   - Gmail / Outlook / Yahoo / AOL fallback links
   - Copy message
   - Contact form links
   - Federal tab (shows "Coming Soon" until a federal bill is added to `lac-config.json`)
   - Metrics dashboard via `#metrics` or `Ctrl+Alt+M`
   - Metrics CSV export

---

## Maintaining the legislator database

`lac-legislators.json` should be reviewed at the start of each legislative session (January) and updated whenever a seat changes hands due to resignation, special election, or appointment.

- **MI House emails:** `FirstnameLastname@house.mi.gov` — verify at [house.mi.gov/AllRepresentatives](https://www.house.mi.gov/AllRepresentatives)
- **MI Senate emails:** `Sen[FI][Lastname]@senate.michigan.gov` — verify at [senate.michigan.gov/senators/all-senators](https://senate.michigan.gov/senators/all-senators/)
- **MI Senate district 35** is currently vacant. Add the record when a replacement is seated.
- Phone numbers should be verified against official directories; some currently reflect general switchboard numbers.

---

## Important limitation

Because this is a static website using mailto and webmail links, it cannot verify that an email was actually sent. Metrics track visits, lookups, email attempts, copy-and-send actions, contact form clicks, ZIP codes, chapters, and bill selections stored locally in the user's browser, plus GA4 event hooks. Centralized reporting requires GA4 or a future server-backed version.

---

## Recommended next improvements

- Verify and update all phone numbers in `lac-legislators.json` against official directories.
- Add individual contact form URLs for MI House members (currently all point to the general `house.mi.gov` directory).
- Add federal campaigns to `lac-config.json` when ready (GUARD VA Benefits Act, CHOICE Act, etc.).
- Add U.S. House member records to `lac-legislators.json` as campaigns require them.
- Build a server-backed dashboard for centralized cross-user campaign reporting.
