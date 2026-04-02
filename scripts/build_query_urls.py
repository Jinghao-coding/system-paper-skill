#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from urllib.parse import quote_plus

BASE = Path(__file__).resolve().parent.parent
DEFAULT_VENUES_PATH = BASE / 'data' / 'venues.json'


def load_payload(path):
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    if isinstance(data, dict) and 'venues' in data:
        return data['venues']
    if isinstance(data, list):
        return data
    raise ValueError('venues json must be either a list or an object with a venues field')


def build_urls(topic, venues, limit=10):
    topic_q = quote_plus(topic)
    rows = []
    for v in venues[:limit]:
        venue_name = v['short_name']
        venue_q = quote_plus(f'{topic} {venue_name}')
        full_venue_q = quote_plus(f'{topic} {v["full_name"]}')
        rows.append({
            'short_name': v['short_name'],
            'full_name': v['full_name'],
            'type': v['type'],
            'ccf': v['ccf'],
            'area': v['area'],
            'venue_link': v['link'],
            'dblp_search_url': f'https://dblp.org/search?q={venue_q}',
            'google_scholar_query': f'{topic} {venue_name}',
            'google_scholar_url': f'https://scholar.google.com/scholar?q={venue_q}',
            'semantic_scholar_url': f'https://www.semanticscholar.org/search?q={full_venue_q}',
            'openalex_url': f'https://openalex.org/works?search={full_venue_q}'
        })
    return {
        'topic': topic,
        'global_queries': {
            'dblp': f'https://dblp.org/search?q={topic_q}',
            'google_scholar': f'https://scholar.google.com/scholar?q={topic_q}',
            'semantic_scholar': f'https://www.semanticscholar.org/search?q={topic_q}',
            'openalex': f'https://openalex.org/works?search={topic_q}'
        },
        'per_venue_queries': rows
    }


def main():
    parser = argparse.ArgumentParser(description='Build query URLs for paper search')
    parser.add_argument('--topic', required=True)
    parser.add_argument('--venues-json', default=str(DEFAULT_VENUES_PATH))
    parser.add_argument('--limit', type=int, default=10)
    parser.add_argument('--format', choices=['json', 'markdown'], default='json')
    args = parser.parse_args()

    venues = load_payload(args.venues_json)
    result = build_urls(args.topic, venues, args.limit)

    if args.format == 'json':
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f'# Query URLs for {args.topic}\n')
        print('## Global queries')
        for k, v in result['global_queries'].items():
            print(f'- {k}: {v}')
        print('\n## Per venue queries')
        print('| short_name | type | ccf | area | venue_link | dblp_search_url | semantic_scholar_url | openalex_url |')
        print('|---|---|---|---|---|---|---|---|')
        for row in result['per_venue_queries']:
            print(f"| {row['short_name']} | {row['type']} | {row['ccf']} | {row['area']} | {row['venue_link']} | {row['dblp_search_url']} | {row['semantic_scholar_url']} | {row['openalex_url']} |")


if __name__ == '__main__':
    main()
