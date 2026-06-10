# Legislative Action Center — Version 1.1

## Files

- `index-v1.1.html` — updated static Legislative Action Center.
- `lac-config.sample.json` — sample external campaign configuration.

## What changed in Version 1.1

1. **External campaign configuration support**
   - The app tries to load `lac-config.json` from the same folder as the HTML file.
   - If no external file is found, it falls back to the built-in campaign data.
   - To use this feature, copy `lac-config.sample.json` to `lac-config.json` and edit the bills/contacts there.

2. **Password-protected metrics dashboard**
   - The Metrics link is hidden from normal public users.
   - Administrators can open the dashboard by going to the page URL with `#metrics` or `#admin` at the end, or by pressing `Ctrl + Alt + M`.
   - Default password: `ChangeMe2026!`
   - Change the password in the HTML before posting publicly:
     ```js
     const LAC_ADMIN_PASSWORD = 'ChangeMe2026!';
     ```
   - This is light protection for a static website. Anyone with technical skill can view the password in the page source. Use server-side authentication for stronger protection.

3. **Recommended campaign metrics**
   - Page visits
   - Legislator lookup attempts
   - Email attempts
   - Copy-and-send uses
   - Contact form clicks
   - ZIP codes represented
   - Chapters represented
   - Bill selections
   - Recent activity log
   - CSV export

4. **GA4 event preservation**
   - Existing GA4 `lacEvent()` calls still fire.
   - The same events are also stored locally for export/testing.

5. **Contact-form support**
   - Legislator records may include `contact_url`.
   - If present, the tool displays a Contact Form / Open Contact Form option.

## Important limitation

Because this is a static website using mailto/webmail links, it cannot verify that an email was actually sent. It can only track that the user clicked an email option, copied a message, opened a contact form, or completed lookup/navigation steps. Centralized reporting should be done in GA4 or a future server-backed version.

## Deployment steps

1. Upload `index-v1.1.html` to Weebly or your hosting location.
2. Rename it as appropriate, such as `index.html`.
3. If you want external campaign data, upload a file named `lac-config.json` in the same folder.
4. Replace `YOUR_API_KEY_HERE` with your Google Civic Information API key if using address-based lookup.
5. Change the default admin password before posting publicly.
6. Test:
   - State bill selection
   - Email app link
   - Gmail/Outlook/Yahoo fallback links
   - Copy message
   - Contact form links
   - Metrics unlock using `#metrics`
   - Metrics CSV export

## Recommended next improvements

- Move all built-in state bills into `lac-config.json`.
- Add actual federal campaigns, such as GUARD and CHOICE.
- Add official contact form URLs for each legislator.
- Build a server-backed dashboard if you need centralized campaign reporting.
# LAC
