import asyncio
import json
import re
import time
from collections import defaultdict
from typing import Optional
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from py_scraper_models import ScrapeResponse

SCRAPER_VERSION = "1.0.0"
MIN_REQUEST_INTERVAL = 5.0  # seconds between requests to the same domain

# Module-level rate limit state (per-process, single worker)
_last_request_times: dict[str, float] = defaultdict(float)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
}


# ─── Fetch ────────────────────────────────────────────────────────────────────

def _get_domain(url: str) -> str:
    return urlparse(url).netloc


def _rate_limit(url: str) -> None:
    domain = _get_domain(url)
    elapsed = time.time() - _last_request_times[domain]
    if elapsed < MIN_REQUEST_INTERVAL:
        time.sleep(MIN_REQUEST_INTERVAL - elapsed)
    _last_request_times[domain] = time.time()


def fetch_html_static(url: str) -> str:
    _rate_limit(url)
    with httpx.Client(timeout=30, follow_redirects=True, headers=HEADERS) as client:
        resp = client.get(url)
        resp.raise_for_status()
        return resp.text


def fetch_html_browser(url: str) -> str:
    """Playwright-based fetch for JS-rendered pages. Called via asyncio.run()."""
    _rate_limit(url)

    async def _fetch() -> str:
        from playwright.async_api import async_playwright
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            try:
                page = await browser.new_page(extra_http_headers=HEADERS)
                await page.goto(url, wait_until="networkidle", timeout=30000)
                return await page.content()
            finally:
                await browser.close()

    return asyncio.run(_fetch())


# ─── Tier 1: JSON-LD ──────────────────────────────────────────────────────────

def extract_json_ld(html: str) -> dict:
    soup = BeautifulSoup(html, "lxml")
    result: dict = {}

    for tag in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(tag.string or "")
        except (json.JSONDecodeError, AttributeError):
            continue

        # Normalise: handle plain object, list, and @graph array
        items = data if isinstance(data, list) else [data]
        if isinstance(data, dict) and "@graph" in data:
            items = data["@graph"]

        for item in items:
            if not isinstance(item, dict):
                continue
            if item.get("@type") not in ("Product", "product"):
                continue

            result["product_name"] = item.get("name")

            offers = item.get("offers", {})
            if isinstance(offers, list):
                offers = offers[0] if offers else {}

            price_raw = offers.get("price")
            if price_raw is not None:
                try:
                    result["price"] = float(str(price_raw).replace(",", ""))
                except ValueError:
                    pass

            result["availability"] = _map_availability(offers.get("availability", ""))

            if result.get("price") is not None:
                result["extraction_method"] = "json_ld"
                result["extraction_tier"] = 1
                return result

    return result


# ─── Tier 2: Meta / Open Graph ────────────────────────────────────────────────

def extract_meta_tags(html: str) -> dict:
    soup = BeautifulSoup(html, "lxml")
    result: dict = {}

    # Price — try multiple patterns in priority order
    price_candidates = [
        soup.find("meta", attrs={"property": "product:price:amount"}),
        soup.find("meta", attrs={"name": "twitter:data1"}),
        soup.find("meta", attrs={"itemprop": "price"}),
        soup.find("span", attrs={"itemprop": "price"}),
        soup.find("div", attrs={"itemprop": "price"}),
    ]
    for candidate in price_candidates:
        if not candidate:
            continue
        raw = (
            candidate.get("content")
            or candidate.get("data-price")
            or candidate.get_text(strip=True)
        )
        if raw:
            digits = re.sub(r"[^\d.]", "", str(raw))
            try:
                result["price"] = float(digits)
                break
            except ValueError:
                continue

    # Product name — og:title is the most reliable cross-platform source
    og_title = soup.find("meta", attrs={"property": "og:title"})
    if og_title:
        result["product_name"] = og_title.get("content")

    # Availability
    avail_meta = soup.find("meta", attrs={"property": "product:availability"})
    if avail_meta:
        result["availability"] = _map_availability(avail_meta.get("content", ""))

    if result.get("price") is not None:
        result["extraction_method"] = "meta_tags"
        result["extraction_tier"] = 2

    return result


# ─── Tier 3: Supplement Facts Table ───────────────────────────────────────────

def extract_supplement_facts(html: str, vitamin_hint: Optional[str] = None) -> dict:
    """
    Parses the FDA-mandated Supplement Facts panel to extract:
    - servings_per_container (integer, required for cost-per-serving normalization)
    - serving_size_raw (e.g. "1 Softgel")
    - serving_size_value + serving_size_unit (active vitamin dose, if vitamin_hint provided)
    """
    soup = BeautifulSoup(html, "lxml")
    result: dict = {}

    # Supplement Facts can appear in a <table>, <div>, or <section>
    for element in soup.find_all(["table", "div", "section"]):
        text = element.get_text(" ", strip=True)
        if not re.search(r"supplement\s+facts", text, re.IGNORECASE):
            continue

        # Servings per container
        m = re.search(r"servings?\s+per\s+container[:\s]+(\d+)", text, re.IGNORECASE)
        if m:
            result["servings_per_container"] = int(m.group(1))

        # Serving size line (physical capsule size, e.g. "1 Softgel")
        m = re.search(r"serving\s+size[:\s]+([^\n|]{3,60})", text, re.IGNORECASE)
        if m:
            result["serving_size_raw"] = m.group(1).strip()

        # Active ingredient dose (only when vitamin_hint is provided)
        if vitamin_hint and result.get("servings_per_container"):
            pattern = re.escape(vitamin_hint) + r"[^0-9]*([0-9,]+\.?\d*)\s*(IU|mcg|µg|mg)"
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                try:
                    result["serving_size_value"] = float(m.group(1).replace(",", ""))
                    unit = m.group(2).lower()
                    result["serving_size_unit"] = "mcg" if unit in ("mcg", "µg") else unit
                except ValueError:
                    pass

        if result.get("servings_per_container"):
            result["extraction_method"] = "table_parse"
            break  # Stop after the first valid Supplement Facts block

    return result


# ─── Tier 4: Claude Haiku Fallback ────────────────────────────────────────────

def extract_haiku_fallback(html: str, anthropic_api_key: str) -> dict:
    """
    Last-resort price extraction via Claude Haiku.
    Only called when tiers 1-3 all failed to produce a price AND
    allow_llm_fallback=true (onboarding workflow only).
    """
    import anthropic

    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()
    page_text = soup.get_text(" ", strip=True)[:4000]

    client = anthropic.Anthropic(api_key=anthropic_api_key)
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=256,
        messages=[{
            "role": "user",
            "content": (
                "Extract the current product price from this supplement product page text.\n"
                "Return ONLY valid JSON with this exact structure:\n"
                '{"price": <number or null>, "product_name": <string or null>, '
                '"availability": "in_stock"|"out_of_stock"|"limited"|"unknown"}\n\n'
                f"Page text:\n{page_text}"
            ),
        }],
    )

    try:
        raw = message.content[0].text.strip()
        raw = re.sub(r"^```json?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
        data = json.loads(raw)
        if data.get("price") is not None:
            data["extraction_method"] = "haiku_fallback"
            data["extraction_tier"] = 4
        return data
    except (json.JSONDecodeError, IndexError, KeyError):
        return {}


# ─── Cascade Orchestrator ─────────────────────────────────────────────────────

def run_cascade(
    url: str,
    product_id: Optional[str] = None,
    requires_browser: bool = False,
    allow_llm_fallback: bool = False,
    vitamin_hint: Optional[str] = None,
    anthropic_api_key: Optional[str] = None,
) -> ScrapeResponse:
    def _error_response(err: str) -> ScrapeResponse:
        return ScrapeResponse(
            product_id=product_id,
            url=url,
            availability="unknown",
            extraction_method="none",
            extraction_tier=0,
            confidence="low",
            error=err,
            scraper_version=SCRAPER_VERSION,
        )

    # Fetch HTML
    try:
        html = fetch_html_browser(url) if requires_browser else fetch_html_static(url)
    except httpx.HTTPStatusError as e:
        code = e.response.status_code
        if code in (403, 429):
            return _error_response("bot_protection_detected")
        return _error_response(f"http_error_{code}")
    except httpx.TimeoutException:
        return _error_response("timeout")
    except Exception as e:
        return _error_response(str(e))

    # Tier 1: JSON-LD
    price_data = extract_json_ld(html)

    # Tier 2: Meta tags (if tier 1 didn't yield a price)
    if price_data.get("price") is None:
        meta = extract_meta_tags(html)
        # Merge only non-null values; don't overwrite good data with None
        for k, v in meta.items():
            if v is not None and price_data.get(k) is None:
                price_data[k] = v

    # Tier 3: Supplement Facts (always run — servings aren't in JSON-LD)
    supp = extract_supplement_facts(html, vitamin_hint=vitamin_hint)

    # Tier 4: Haiku fallback (gated)
    if price_data.get("price") is None and allow_llm_fallback and anthropic_api_key:
        haiku = extract_haiku_fallback(html, anthropic_api_key)
        for k, v in haiku.items():
            if v is not None and price_data.get(k) is None:
                price_data[k] = v

    # Merge price_data and supp results
    merged = {**price_data, **supp}

    # Determine winning extraction_tier
    tier = merged.get("extraction_tier", 0)
    if supp.get("servings_per_container"):
        tier = max(tier, 3)

    # Determine extraction_method (most informative tier that ran)
    method_rank = {"haiku_fallback": 4, "table_parse": 3, "meta_tags": 2, "json_ld": 1}
    methods = [
        price_data.get("extraction_method"),
        supp.get("extraction_method"),
    ]
    methods = [m for m in methods if m]
    extraction_method = max(methods, key=lambda m: method_rank.get(m, 0)) if methods else "none"

    has_price = merged.get("price") is not None
    has_servings = merged.get("servings_per_container") is not None
    confidence = "high" if (has_price and has_servings) else "low"

    return ScrapeResponse(
        product_id=product_id,
        url=url,
        price=merged.get("price"),
        servings_per_container=merged.get("servings_per_container"),
        serving_size_raw=merged.get("serving_size_raw"),
        serving_size_value=merged.get("serving_size_value"),
        serving_size_unit=merged.get("serving_size_unit"),
        product_name=merged.get("product_name"),
        availability=merged.get("availability", "unknown"),
        form=None,
        extraction_method=extraction_method,
        extraction_tier=tier,
        confidence=confidence,
        error=None,
        scraper_version=SCRAPER_VERSION,
    )


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _map_availability(value: str) -> str:
    v = value.lower()
    if any(x in v for x in ("instock", "in_stock", "in stock")):
        return "in_stock"
    if any(x in v for x in ("outofstock", "out_of_stock", "out of stock")):
        return "out_of_stock"
    if "limited" in v:
        return "limited"
    return "unknown"
