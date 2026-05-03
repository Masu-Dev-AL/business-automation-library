import os
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

from fastapi import FastAPI

from py_scraper_cascade import SCRAPER_VERSION, run_cascade
from py_scraper_models import (
    HealthResponse,
    RobotsRequest,
    RobotsResponse,
    ScrapeRequest,
    ScrapeResponse,
)

app = FastAPI(
    title="Vitamin Price Scraper API",
    version=SCRAPER_VERSION,
    description=(
        "Sidecar service for the competitor-price-monitor-n8n project. "
        "Handles all HTTP scraping and price extraction so n8n stays clean."
    ),
)

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Check once at startup whether Playwright is installed
_playwright_available = False
try:
    from playwright.async_api import async_playwright  # noqa: F401
    _playwright_available = True
except ImportError:
    pass


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        version=SCRAPER_VERSION,
        playwright_available=_playwright_available,
    )


@app.post("/scrape", response_model=ScrapeResponse)
def scrape(req: ScrapeRequest) -> ScrapeResponse:
    return run_cascade(
        url=req.url,
        product_id=req.product_id,
        requires_browser=req.requires_browser,
        allow_llm_fallback=req.allow_llm_fallback,
        vitamin_hint=req.vitamin_hint,
        anthropic_api_key=ANTHROPIC_API_KEY,
    )


@app.post("/robots", response_model=RobotsResponse)
def check_robots(req: RobotsRequest) -> RobotsResponse:
    parsed = urlparse(req.url)
    domain = parsed.netloc
    robots_url = f"{parsed.scheme}://{domain}/robots.txt"

    rp = RobotFileParser()
    rp.set_url(robots_url)
    try:
        rp.read()
    except Exception as e:
        return RobotsResponse(
            url=req.url,
            domain=domain,
            scrape_allowed="unknown",
            note=f"Could not fetch robots.txt: {e}",
        )

    can_fetch = rp.can_fetch(req.user_agent, req.url)
    return RobotsResponse(
        url=req.url,
        domain=domain,
        scrape_allowed="yes" if can_fetch else "no",
    )
