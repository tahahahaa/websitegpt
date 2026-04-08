import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urlunparse
from langchain_core.documents import Document

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

SKIP_URL_PATTERNS = [
    '/cdn-cgi/', '/wp-json/', '/feed/', '/rss/', '/xmlrpc',
    '/wp-admin/', '/wp-login',
    '.jpg', '.png', '.gif', '.pdf', '.zip', '.css', '.js',
    'mailto:', 'tel:', 'javascript:',
    '-squad', '-squad/', 'wp-content',
]

PRIORITY_KEYWORDS = [
    'schedule', 'standing', 'point', 'table', 'watch', 'result',
    'about', 'faq', 'contact', 'ticket', 'venue', 'price',
    'match-report', 'media-release', 'hbl-psl', '2026', '2025',
    'service', 'product', 'team', 'player', 'feature',
]


def normalize_url(url: str) -> str:
    parsed = urlparse(url)
    path = parsed.path.rstrip('/')
    return urlunparse((parsed.scheme, parsed.netloc, path, '', parsed.query, ''))


def should_skip_url(url: str) -> bool:
    return any(p in url.lower() for p in SKIP_URL_PATTERNS)


def fetch_with_requests(url: str) -> str:
    resp = requests.get(url, headers=HEADERS, timeout=10)
    resp.raise_for_status()
    return resp.text


def fetch_with_playwright(url: str) -> str:
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=HEADERS['User-Agent'],
            viewport={'width': 1280, 'height': 900}
        )
        page = context.new_page()

        try:
            page.goto(url, wait_until='networkidle', timeout=15000)
        except Exception:
            try:
                page.goto(url, wait_until='domcontentloaded', timeout=10000)
                time.sleep(3)
            except Exception as e:
                browser.close()
                raise e

        try:
            page_height = page.evaluate("document.body.scrollHeight") or 3000
            steps = min(10, max(5, page_height // 400))
            for i in range(steps):
                page.evaluate(f"window.scrollTo(0, {int((page_height/steps)*i)})")
                time.sleep(0.3)
            page.evaluate("window.scrollTo(0, 0)")
            time.sleep(1.5)
        except Exception:
            pass

        for sel in ['.loading', '.spinner', '[class*="loader"]', '[class*="skeleton"]']:
            try:
                page.wait_for_selector(sel, state='hidden', timeout=2000)
            except Exception:
                pass

        try:
            page.evaluate("document.querySelectorAll('details').forEach(el => el.setAttribute('open', ''))")
        except Exception:
            pass

        for sel in ['[aria-expanded="false"]', '.accordion-button.collapsed',
                    '.faq-question', 'button[data-toggle="collapse"]',
                    '.show-more', '[data-expand]', '.collapsible']:
            try:
                for el in page.query_selector_all(sel)[:15]:
                    try:
                        el.click(timeout=300)
                    except Exception:
                        pass
            except Exception:
                pass

        time.sleep(1)
        html = page.content()
        browser.close()
        return html


def fetch_page(url: str) -> str:
    requests_html = None
    playwright_html = None

    try:
        requests_html = fetch_with_requests(url)
        print(f'  [requests] {len(requests_html):,} chars')
    except Exception as e:
        print(f'  [requests failed] {e}')

    try:
        playwright_html = fetch_with_playwright(url)
        print(f'  [playwright] {len(playwright_html):,} chars')
    except Exception as e:
        print(f'  [playwright failed] {e}')

    if playwright_html and requests_html:
        winner = playwright_html if len(playwright_html) >= len(requests_html) else requests_html
        method = 'playwright' if len(playwright_html) >= len(requests_html) else 'requests'
        print(f'  → using {method}')
        return winner
    elif playwright_html:
        return playwright_html
    elif requests_html:
        return requests_html
    else:
        raise Exception(f'Both fetch methods failed for {url}')


def extract_clean_text(html: str) -> str:
    soup = BeautifulSoup(html, 'lxml')

    # NOTE: iframe intentionally NOT in this list — we scrape iframe URLs separately
    for tag in soup(['script', 'style', 'nav', 'footer', 'header',
                     'aside', 'form', 'noscript', 'svg', 'meta', 'link']):
        tag.decompose()

    # Extract tables as structured rows
    tables_text = []
    for table in soup.find_all('table'):
        rows = []
        for row in table.find_all('tr'):
            cells = [td.get_text(strip=True) for td in row.find_all(['td', 'th'])]
            cells = [c for c in cells if c.strip()]
            if cells:
                rows.append(' | '.join(cells))
        if rows:
            tables_text.append('\n'.join(rows))
        table.decompose()

    text = soup.get_text(separator='\n', strip=True)
    lines = [l.strip() for l in text.splitlines() if l.strip()]

    deduped = []
    prev = None
    for line in lines:
        if line != prev:
            deduped.append(line)
        prev = line

    result = '\n'.join(deduped)
    if tables_text:
        result += '\n\n=== TABLE DATA ===\n' + '\n\n'.join(tables_text)

    return result


def scrape_url(url: str, max_pages: int = 5) -> list[Document]:
    visited = set()
    to_visit = [normalize_url(url)]
    documents = []
    base_domain = urlparse(url).netloc

    while to_visit and len(visited) < max_pages:
        current_url = to_visit.pop(0)

        if current_url in visited:
            continue

        if should_skip_url(current_url):
            print(f'  → Skipping (noise): {current_url}')
            continue

        print(f'\nScraping [{len(visited)+1}/{max_pages}]: {current_url}')

        try:
            html = fetch_page(current_url)
        except Exception as e:
            print(f'  ✗ Skip: {e}')
            visited.add(current_url)
            continue

        visited.add(current_url)
        clean_text = extract_clean_text(html)

        if len(clean_text) > 50:
            documents.append(Document(
                page_content=clean_text,
                metadata={'source': current_url, 'domain': base_domain}
            ))
            print(f'  ✓ Saved {len(clean_text):,} chars')
        else:
            print(f'  ✗ Empty page, skipping')

        soup = BeautifulSoup(html, 'lxml')
        found_links = []

        # Extract iframe src URLs — priority, go there immediately
        for iframe in soup.find_all('iframe', src=True):
            iframe_url = normalize_url(urljoin(current_url, iframe['src']))
            parsed = urlparse(iframe_url)
            if (
                parsed.netloc == base_domain
                and iframe_url not in visited
                and iframe_url not in to_visit
                and parsed.scheme in ['http', 'https']
            ):
                print(f'  → Found iframe: {iframe_url}')
                found_links.insert(0, iframe_url)

        # Extract regular anchor links
        for a in soup.find_all('a', href=True):
            href = normalize_url(urljoin(current_url, a['href']))
            parsed = urlparse(href)
            if (
                parsed.netloc == base_domain
                and href not in visited
                and href not in to_visit
                and href not in found_links
                and parsed.scheme in ['http', 'https']
                and not should_skip_url(href)
            ):
                found_links.append(href)

        priority = [l for l in found_links
                    if any(k in l.lower() for k in PRIORITY_KEYWORDS)]
        others = [l for l in found_links if l not in priority]

        # iframes already at front of found_links, priority pages next, rest after
        to_visit = priority + to_visit + others

    print(f'\n✅ Done — {len(documents)} pages scraped')
    return documents