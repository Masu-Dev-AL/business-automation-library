from pydantic import BaseModel, field_validator
from typing import Optional


class ScrapeRequest(BaseModel):
    url: str
    requires_browser: bool = False

    @field_validator('requires_browser', mode='before')
    @classmethod
    def parse_requires_browser(cls, v):
        if isinstance(v, str):
            return v.strip().lower() in ('true', '1', 'yes')
        return bool(v)
    allow_llm_fallback: bool = False
    product_id: Optional[str] = None
    vitamin_hint: Optional[str] = None  # e.g. "Vitamin D3" — used to locate dose in Supplement Facts


class ScrapeResponse(BaseModel):
    product_id: Optional[str] = None
    url: str
    price: Optional[float] = None
    servings_per_container: Optional[int] = None
    serving_size_raw: Optional[str] = None
    serving_size_value: Optional[float] = None
    serving_size_unit: Optional[str] = None
    product_name: Optional[str] = None
    availability: str = "unknown"  # in_stock | out_of_stock | limited | unknown
    form: Optional[str] = None
    extraction_method: str = "none"  # json_ld | meta_tags | table_parse | haiku_fallback | none
    extraction_tier: int = 0          # 1-4, 0 = failed before any extraction
    confidence: str = "low"           # high (price + servings) | low (partial or failed)
    error: Optional[str] = None
    scraper_version: str = "1.0.0"


class HealthResponse(BaseModel):
    status: str
    version: str
    playwright_available: bool


class RobotsRequest(BaseModel):
    url: str
    user_agent: str = "Mozilla/5.0"


class RobotsResponse(BaseModel):
    url: str
    domain: str
    scrape_allowed: str  # yes | no | unknown
    matched_rule: Optional[str] = None
    note: Optional[str] = None
