# Twitch Live Channel Scraper

This script scrapes live German-speaking Twitch streamers using the Twitch API and Playwright. It collects profile links from each streamer's "About" page to detect external shop or imprint pages.

---

## 💡 Features

- Uses the official Twitch API to retrieve live streamers
- Filters for German-speaking (`language=de`) streamers
- Scrapes each streamer's `/about` page for external links
- Detects shop, merch, or imprint links (e.g. Spreadshop, Impressum)
- Skips already scanned users using timestamped logs
- Saves results as structured CSV

---

## 📦 Requirements

Install Python 3.9+ and the required libraries:

```bash
pip install -r requirements.txt
```

### Example `requirements.txt`:

```
playwright
requests
tldextract
lxml
tqdm
python-dotenv
```

Then install the browser engine for Playwright:

```bash
playwright install
```

---

## 🔐 Twitch API Setup

1. Go to [https://dev.twitch.tv/console/apps](https://dev.twitch.tv/console/apps) and register a new app.
2. Copy the **Client ID** and **Client Secret**.

Create a `.env` file in the project root:

```
TWITCH_APP_ID=your_client_id_here
TWITCH_APP_SECRET=your_client_secret_here
```

---

## 🚀 Running the Scraper

Run the main script:

```bash
python twitch_scraper.py
```

This will:

- Authenticate with the Twitch API
- Fetch up to 1000 live German-speaking channels
- Visit each `/about` page with Playwright
- Parse outbound links and detect specific patterns
- Save results in a CSV

---

## 📁 Output

- `twitch_output.csv`: Collected results including timestamp, username, category (e.g. spreadshop, imprint), and link
- `checked_channels.csv`: Tracks when each streamer was last scanned (to avoid duplicates)

---

## ⚙️ Customization

You can change:

- The number of channels (default: 1000)
- The time interval between re-checks (`CHECK_INTERVAL_DAYS = 7`)
- The blacklist domains to avoid fake or affiliate imprints

---

## 🧑‍💻 Author

Developed by herrtier

---

## 📌 Notes

- Only works for publicly available /about pages
- Requires login only if Twitch blocks automated access (rare)
- Be sure to respect Twitch’s [Terms of Service](https://www.twitch.tv/p/en/legal/terms-of-service/)

---

## 🛠️ License

MIT — use responsibly and only for legal, educational, or analytical purposes.