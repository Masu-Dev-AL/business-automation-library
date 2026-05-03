#!/usr/bin/env python3
"""
robots_txt_checker.py

Standalone script: checks robots.txt crawl permission for a list of
(domain, path) pairs. Returns a JSON report to stdout.

Usage:
    python robots_txt_checker.py targets.json
    python robots_txt_checker.py --inline '[{"url": "https://nowfoods.com/products/supplements/vitamin-d3-1000-iu-softgels"}]'

targets.json format:
    [{"url": "https://competitor.com/product/path"}]

Output per target:
    {
        "url": "...",
        "domain": "...",
        "path": "...",
        "scrape_allowed": "yes" | "no" | "unknown",
        "matched_rule": "..." | null,
        "note": "..."
    }
"""

import sys
import json
import urllib.robotparser
import urllib.parse
import urllib.request
import argparse

USER_AGENT = 'Mozilla/5.0 (compatible; PriceMonitorBot/1.0)'
TIMEOUT = 10


def check_url(url: str) -> dict:
    parsed = urllib.parse.urlparse(url)
    domain = f"{parsed.scheme}://{parsed.netloc}"
    path = parsed.path or '/'
    robots_url = f"{domain}/robots.txt"

    rp = urllib.robotparser.RobotFileParser()
    rp.set_url(robots_url)

    try:
        req = urllib.request.Request(robots_url, headers={'User-Agent': USER_AGENT})
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            content = resp.read().decode('utf-8', errors='replace')
        rp.parse(content.splitlines())
        note = 'robots.txt fetched and parsed'
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return {
                'url': url, 'domain': domain, 'path': path,
                'scrape_allowed': 'yes',
                'matched_rule': None,
                'note': 'robots.txt returned 404 — no restrictions'
            }
        return {
            'url': url, 'domain': domain, 'path': path,
            'scrape_allowed': 'unknown',
            'matched_rule': None,
            'note': f'HTTP error fetching robots.txt: {e.code}'
        }
    except Exception as e:
        return {
            'url': url, 'domain': domain, 'path': path,
            'scrape_allowed': 'unknown',
            'matched_rule': None,
            'note': f'Error fetching robots.txt: {e}'
        }

    allowed = rp.can_fetch(USER_AGENT, url)
    return {
        'url': url,
        'domain': domain,
        'path': path,
        'scrape_allowed': 'yes' if allowed else 'no',
        'matched_rule': None,
        'note': note
    }


def main():
    parser = argparse.ArgumentParser(description='Check robots.txt for a list of URLs')
    parser.add_argument('file', nargs='?', help='JSON file with list of {"url": "..."} objects')
    parser.add_argument('--inline', help='Inline JSON string instead of file')
    args = parser.parse_args()

    if args.inline:
        targets = json.loads(args.inline)
    elif args.file:
        with open(args.file) as f:
            targets = json.load(f)
    else:
        # Default: check Phase 1 seed URLs
        targets = [
            {'url': 'https://www.nowfoods.com/products/supplements/vitamin-d3-1000-iu-softgels'},
            {'url': 'https://www.nowfoods.com/products/supplements/vitamin-d3-5000-iu-softgels'},
            {'url': 'https://www.lifeextension.com/vitamins-supplements/item01751/vitamin-d3'},
            {'url': 'https://www.lifeextension.com/vitamins-supplements/item01718/vitamin-d3'},
            {'url': 'https://www.thorne.com/products/dp/vitamin-d3'},
        ]

    results = [check_url(t['url']) for t in targets]
    print(json.dumps(results, indent=2))

    # Print summary
    allowed = sum(1 for r in results if r['scrape_allowed'] == 'yes')
    blocked = sum(1 for r in results if r['scrape_allowed'] == 'no')
    unknown = sum(1 for r in results if r['scrape_allowed'] == 'unknown')
    print(f"\nSummary: {allowed} allowed, {blocked} blocked, {unknown} unknown", file=sys.stderr)


if __name__ == '__main__':
    main()
