from typing import List, Dict
from urllib.parse import quote_plus
import os, random, time, re
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

def _sleep(a=0.6, b=1.4):
    time.sleep(random.uniform(a, b))

def run(args, cfg) -> List[Dict]:
    search = cfg.get("search") or {}
    term_list = search.get("term_list") or (getattr(args, "businesses", None) or ["dentist"])
    location = search.get("location") or getattr(args, "location", "") or "Fresno, CA"
    max_pages = int((cfg.get("paging") or {}).get("max_pages") or getattr(args, "max_pages", 1) or 1)
    headful = bool(getattr(args, "headful", False))

    ua = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 14_6) AppleWebKit/537.36 "
          "(KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36")
    profile_dir = os.path.join(os.getcwd(), "out", "chrome_profile")
    os.makedirs(profile_dir, exist_ok=True)

    rows: List[Dict] = []
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=profile_dir,
            headless=not headful,
            channel="chrome",
            viewport={"width": random.randint(1200, 1440), "height": random.randint(760, 900)},
            locale="en-US",
            timezone_id="America/Los_Angeles",
            user_agent=ua,
        )
        page = ctx.new_page()

        # minimal stealth
        ctx.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined});")
        ctx.add_init_script("window.chrome = { runtime: {} };")
        ctx.add_init_script("Object.defineProperty(navigator, 'languages', {get: () => ['en-US','en']});")
        ctx.add_init_script("Object.defineProperty(navigator, 'platform', {get: () => 'MacIntel'});")
        ctx.add_init_script("Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4,5]});")

        for term in term_list:
            page_num = 0
            while page_num < max_pages:
                url = f"https://www.yelp.com/search?find_desc={quote_plus(term)}&find_loc={quote_plus(location)}&start={page_num*10}"
                page.goto(url, timeout=60000)
                _sleep(0.8, 1.8)

                try:
                    page.get_by_role("button", name=re.compile("Accept|Agree|OK", re.I)).first.click(timeout=2500)
                    _sleep()
                except Exception:
                    pass

                try:
                    page.mouse.wheel(0, random.randint(800, 1600))
                    _sleep()
                except Exception:
                    pass

                try:
                    page.wait_for_selector("h3 a[href^='/biz/']", timeout=10000)
                except PlaywrightTimeoutError:
                    break

                links = page.locator("h3 a[href^='/biz/']")
                n = min(links.count(), 10)
                if n == 0:
                    break

                for i in range(n):
                    a = links.nth(i)
                    name = (a.inner_text() or "").strip()
                    href = a.get_attribute("href") or ""
                    if not name or not href:
                        continue
                    rows.append({
                        "term": term,
                        "name": name,
                        "url": "https://www.yelp.com" + href,
                        "location": location,
                        "page": page_num + 1,
                    })
                    _sleep(0.3, 0.9)

                page_num += 1
                _sleep(1.0, 2.2)

        ctx.close()

    if not rows:
        rows = [
            {"term": "demo", "name": "Sample Business A", "url": "https://example.com/a", "location": location, "page": 1},
            {"term": "demo", "name": "Sample Business B", "url": "https://example.com/b", "location": location, "page": 1},
        ]
    return rows
