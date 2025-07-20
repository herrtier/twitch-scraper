import csv
import os
import re
import time
from datetime import datetime, timedelta
import requests
import tldextract
from lxml import html as lxml_html
from tqdm import tqdm
from playwright.sync_api import sync_playwright
from dotenv import dotenv_values


CONFIG = dotenv_values('.env')
TWITCH_CLIENT_ID = CONFIG['TWITCH_APP_ID']
TWITCH_CLIENT_SECRET = CONFIG['TWITCH_APP_SECRET']
CHECK_INTERVAL_DAYS = 7


def get_oauth_token():
    url = "https://id.twitch.tv/oauth2/token"
    params = {
        "client_id": TWITCH_CLIENT_ID,
        "client_secret": TWITCH_CLIENT_SECRET,
        "grant_type": "client_credentials"
    }
    response = requests.post(url, params=params)
    response.raise_for_status()
    return response.json()["access_token"]


def get_all_live_channels(token, max_total=1000):
    headers = {
        "Client-ID": TWITCH_CLIENT_ID,
        "Authorization": f"Bearer {token}"
    }
    url = "https://api.twitch.tv/helix/streams"
    live_channels = []
    cursor = None

    while len(live_channels) < max_total:
        params = {"first": 100, "language": "de"}
        if cursor:
            params["after"] = cursor

        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()

        for stream in data["data"]:
            live_channels.append(stream["user_login"])

        cursor = data.get("pagination", {}).get("cursor")
        if not cursor:
            break

        time.sleep(1)
    return live_channels


def scrape_twitch_about_page(channel_name: str, user_login=None):
    url = f"https://www.twitch.tv/{channel_name}/about"
    d = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        page.goto(url, wait_until="load")
        page.wait_for_timeout(5000)
        html_content = page.content()
        browser.close()

    site = lxml_html.fromstring(html_content)
    for element, attribute, link, pos in site.iterlinks():
        if not link:
            continue
        link = link.lower()

        if 'spreadshop' in link:
            d['spreadshop'] = link
        if 'spreadshirt' in link:
            d['spreadshirt'] = link
        if 'shirtee' in link:
            d['shirtee'] = link

        if 'impressum' in link:
            check = sum(
                [1 if exc in link else 0 for exc in [
                    'ins.gg', 'tworeach.com', 'reachout.agency', 'pure4u.de',
                    'streamfluence.de', '2ndwave.rocks', 'new-base.de', 'digitalninjas.de',
                    'onlinetitans.org', '2rea.ch', 'pingup.de', 'peoplessquare.de',
                    'beyondmgmt.de', 'lyaison.com', 'snoops-1.mozello.shop',
                    'nextlevelnation.de', 'powmedia.de', 'peoplessquare.link',
                    '1up.management'
                ]]
            )
            if check == 0:
                d['imprint'] = link

        split_domain = tldextract.extract(link)
        domain = f"{split_domain.domain}.{split_domain.suffix}"
        if split_domain.subdomain:
            domain = f"{split_domain.subdomain}.{domain}"

        if user_login:
            if re.sub(r"[^A-Za-z0-9]", "", user_login.lower()) in re.sub(r"[^A-Za-z0-9]", "", domain.lower()):
                d['website'] = link

    return d


def load_checked_channels(filepath="checked_channels.csv"):
    checked = {}
    if os.path.exists(filepath):
        with open(filepath, newline='', encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                checked[row['username'].lower()] = row['last_checked']
    return checked


def save_checked_channel(username, filepath="checked_channels.csv"):
    now = datetime.utcnow().isoformat()
    exists = os.path.exists(filepath)
    with open(filepath, "a", newline='', encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["username", "last_checked"])
        if not exists:
            writer.writeheader()
        writer.writerow({"username": username, "last_checked": now})


def write_output(username, result_dict, status="ok", filepath="twitch_output.csv"):
    now = datetime.utcnow().isoformat()
    exists = os.path.exists(filepath)
    with open(filepath, "a", newline='', encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["timestamp", "username", "category", "link", "status"])
        if not exists:
            writer.writeheader()

        if not result_dict:
            writer.writerow({
                "timestamp": now,
                "username": username,
                "category": "none",
                "link": "",
                "status": status
            })
        else:
            for key, val in result_dict.items():
                writer.writerow({
                    "timestamp": now,
                    "username": username,
                    "category": key,
                    "link": val,
                    "status": status
                })


def main():
    token = get_oauth_token()
    print("[✓] Zugriffstoken geholt")

    checked_channels = load_checked_channels()
    print(f"[✓] Geladene Prüf-Historie: {len(checked_channels)} Kanäle")

    channels = get_all_live_channels(token, max_total=500)
    print(f"[✓] Gefundene deutschsprachige Live-Kanäle: {len(channels)}")

    cutoff = datetime.utcnow() - timedelta(days=CHECK_INTERVAL_DAYS)

    for username in tqdm(channels, desc="Analysiere Kanäle"):
        uname = username.lower()
        last_checked = checked_channels.get(uname)
        if last_checked:
            try:
                dt = datetime.fromisoformat(last_checked)
                if dt > cutoff:
                    continue
            except:
                pass

        try:
            result = scrape_twitch_about_page(username, user_login=username)
            status = "ok" if result else "no_links"
            write_output(username, result, status=status)
        except Exception as e:
            write_output(username, {}, status=f"error: {e}")
        save_checked_channel(uname)
        time.sleep(1.5)


if __name__ == "__main__":
    main()
