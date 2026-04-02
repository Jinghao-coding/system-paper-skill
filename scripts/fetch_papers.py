#!/usr/bin/env python3
import argparse
import json
import re
import urllib.request
import urllib.parse
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
BUILD_CFG = BASE / 'scripts' / 'build_query_config.py'


def load_json_from_cmd(topic, top_k):
    import subprocess, sys
    cmd = [sys.executable, str(BUILD_CFG), '--topic', topic, '--top-k', str(top_k), '--format', 'json']
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or 'build_query_config failed')
    return json.loads(proc.stdout)


def fetch_url(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return resp.read().decode('utf-8', errors='ignore')


def strip_tags(text):
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def parse_dblp_search(html, limit=10):
    items = []
    blocks = re.findall(r'<li class="entry[^"]*?">(.*?)</li>', html, flags=re.S)
    for block in blocks:
        title_m = re.search(r'class="title"[^>]*>(.*?)</span>', block, flags=re.S)
        if not title_m:
            continue
        title = strip_tags(title_m.group(1))

        authors = [strip_tags(x) for x in re.findall(r'<span itemprop="author"[^>]*><a [^>]*><span itemprop="name">(.*?)</span>', block, flags=re.S)]
        year_m = re.search(r'<span itemprop="datePublished">(\d{4})</span>', block)
        year = int(year_m.group(1)) if year_m else None
        venue_m = re.search(r'<span class="venue">(.*?)</span>', block, flags=re.S)
        venue = strip_tags(venue_m.group(1)) if venue_m else None
        url_m = re.search(r'<nav class="publ">.*?<a href="([^"]+)"', block, flags=re.S)
        url = url_m.group(1) if url_m else None
        doi_m = re.search(r'https?://doi\.org/([^"\s<>]+)', block)
        doi = doi_m.group(1) if doi_m else None

        items.append({
            'title': title,
            'authors': authors,
            'year': year,
            'venue': venue,
            'url': url,
            'doi': doi,
            'source': 'dblp-search'
        })
        if len(items) >= limit:
            break
    return items


def main():
    parser = argparse.ArgumentParser(description='Fetch paper metadata from DBLP search results')
    parser.add_argument('--topic', required=True)
    parser.add_argument('--top-k', type=int, default=8)
    parser.add_argument('--per-venue-limit', type=int, default=3)
    parser.add_argument('--format', choices=['json', 'markdown'], default='json')
    args = parser.parse_args()

    cfg = load_json_from_cmd(args.topic, args.top_k)
    papers = []
    seen = set()

    for venue in cfg['venues']:
        q = urllib.parse.quote_plus(f"{args.topic} {venue['short_name']}")
        search_url = f'https://dblp.org/search?q={q}'
        try:
            html = fetch_url(search_url)
            results = parse_dblp_search(html, limit=args.per_venue_limit)
        except Exception as e:
            results = [{
                'title': None,
                'authors': [],
                'year': None,
                'venue': venue['short_name'],
                'url': search_url,
                'doi': None,
                'source': 'dblp-search',
                'error': str(e)
            }]

        for r in results:
            key = (r.get('title'), r.get('year'), r.get('venue'))
            if key in seen:
                continue
            seen.add(key)
            r['target_venue'] = venue['short_name']
            r['target_venue_link'] = venue['link']
            papers.append(r)

    output = {
        'topic': args.topic,
        'selected_areas': cfg['selected_areas'],
        'venues': cfg['venues'],
        'papers': papers
    }

    if args.format == 'json':
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        print(f'# Papers for {args.topic}\n')
        print('| target_venue | year | title | authors | venue | url |')
        print('|---|---:|---|---|---|---|')
        for p in papers:
            authors = ', '.join(p.get('authors', []))
            print(f"| {p.get('target_venue','')} | {p.get('year','')} | {p.get('title','')} | {authors} | {p.get('venue','')} | {p.get('url','')} |")


if __name__ == '__main__':
    main()
