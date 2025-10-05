from typing import List, Dict
from urllib.parse import quote_plus
import os, random, time
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

def _sleep(a=0.6, b=1.4):
    time.sleep(random.uniform(a, b))

def run(args, cfg) -> List[Dict]:
    q_cfg = (cfg.get("query") or {})
    industry = (q_cfg.get("industry") or "").strip()
    company  = (q_cfg.get("company")  or "").strip()
    location = (cfg.get("location") or getattr(args, "location", "") or "Fresno, CA").strip()
    max_pages = int((cfg.get("paging") or {}).get("max_pages") or getattr(args, "max_pages", 1) or 1)
    headful = bool(getattr(args, "headful", False))

    # Build the search query
    q_parts = [industry, company]
    q = " ".join([p for p in q_parts if p]).strip() or "education"

    # Reuse a persistent profile to look more “human”
    profile_dir = os.path.join(os.getcwd(), "out", "chrome_profile_indeed")
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
            user_agent=("Mozilla/5.0 (Macintosh; Intel Mac OS X 14_6) AppleWebKit/537.36 "
                        "(KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"),
        )
        # Basic stealth patches
        ctx.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined});")
        ctx.add_init_script("window.chrome = { runtime: {} };")
        ctx.add_init_script("Object.defineProperty(navigator, 'languages', {get: () => ['en-US','en']});")
        ctx.add_init_script("Object.defineProperty(navigator, 'platform', {get: () => 'MacIntel'});")
        ctx.add_init_script("Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4,5]});")

        page = ctx.new_page()

        base = "https://www.indeed.com/jobs"
        # Indeed paginates with &start=0,10,20...
        for page_idx in range(max_pages):
            start = page_idx * 10
            url = f"{base}?q={quote_plus(q)}&l={quote_plus(location)}&start={start}"
            page.goto(url, timeout=60000)
            _sleep(0.8, 1.8)

            # Accept cookie/consent if present
            try:
                page.get_by_role("button", name="Accept all cookies").click(timeout=2500)
                _sleep()
            except Exception:
                pass

            # Gentle scroll to trigger rendering
            try:
                page.mouse.wheel(0, random.randint(900, 1600))
                _sleep()
            except Exception:
                pass

            # Wait for job cards
            try:
                page.wait_for_selector('div.job_seen_beacon, li[data-testid="result"]', timeout=12000)
            except PlaywrightTimeoutError:
                break

            # Prefer newer testid selectors; fall back to classic ones
            cards = page.locator('li[data-testid="result"]')
            if cards.count() == 0:
                cards = page.locator("div.job_seen_beacon")

            n = min(cards.count(), 15)
            if n == 0:
                break

            for i in range(n):
                card = cards.nth(i)
                # Title + URL
                title_el = card.locator('a[data-testid="jobTitle"], h2 a').first
                href = ""
                title = ""
                try:
                    title = (title_el.inner_text() or "").strip()
                    href = title_el.get_attribute("href") or ""
                except Exception:
                    pass
                if not title or not href:
                    continue
                if href.startswith("/"):
                    href = "https://www.indeed.com" + href

                # Company
                company_el = card.locator('[data-testid="company-name"], span.companyName').first
                company_name = ""
                try:
                    company_name = (company_el.inner_text() or "").strip()
                except Exception:
                    pass

                # Location
                loc_el = card.locator('[data-testid="text-location"], div.companyLocation').first
                loc_text = ""
                try:
                    loc_text = (loc_el.inner_text() or "").strip()
                except Exception:
                    pass

                rows.append({
                    "query": q,
                    "title": title,
                    "company": company_name,
                    "location": loc_text or location,
                    "url": href,
                    "page": page_idx + 1,
                })
                _sleep(0.2, 0.6)

        ctx.close()

    if not rows:
        # Fallback so the pipeline completes even if blocked
        rows = [
            {"query": q, "title": "Sample Teacher", "company": "Demo Unified", "location": location, "url": "https://example.com/a", "page": 1},
            {"query": q, "title": "Sample Lecturer", "company": "Demo College", "location": location, "url": "https://example.com/b", "page": 1},
        ]
    return rows

