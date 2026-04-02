#!/usr/bin/env python3
import argparse
import json


def fmt_authors(authors):
    if not authors:
        return ''
    if len(authors) == 1:
        return authors[0]
    if len(authors) == 2:
        return f'{authors[0]} and {authors[1]}'
    return ', '.join(authors[:-1]) + f', and {authors[-1]}'


def ieee(p):
    authors = ', '.join(p.get('authors', []))
    title = p.get('title') or ''
    venue = p.get('venue') or p.get('target_venue') or ''
    year = p.get('year') or ''
    url = p.get('url') or ''
    parts = []
    if authors:
        parts.append(f'{authors},')
    if title:
        parts.append(f'"{title},"')
    if venue:
        parts.append(venue + ',')
    if year:
        parts.append(str(year) + '.')
    if url:
        parts.append(url)
    return ' '.join(parts).strip()


def apa(p):
    authors = fmt_authors(p.get('authors', []))
    title = p.get('title') or ''
    venue = p.get('venue') or p.get('target_venue') or ''
    year = p.get('year') or 'n.d.'
    url = p.get('url') or ''
    text = ''
    if authors:
        text += f'{authors} '
    text += f'({year}). {title}. '
    if venue:
        text += f'{venue}. '
    if url:
        text += url
    return text.strip()


def plain(p):
    title = p.get('title') or ''
    authors = ', '.join(p.get('authors', []))
    venue = p.get('venue') or p.get('target_venue') or ''
    year = p.get('year') or ''
    return f'{title} | {authors} | {venue} | {year}'.strip(' |')


def main():
    parser = argparse.ArgumentParser(description='Format citations for fetched papers')
    parser.add_argument('--input', required=True, help='json file containing papers list or search result object')
    parser.add_argument('--style', choices=['ieee', 'apa', 'plain'], default='ieee')
    args = parser.parse_args()

    with open(args.input, 'r', encoding='utf-8') as f:
        data = json.load(f)

    papers = data['papers'] if isinstance(data, dict) and 'papers' in data else data
    out = []
    for p in papers:
        if args.style == 'ieee':
            citation = ieee(p)
        elif args.style == 'apa':
            citation = apa(p)
        else:
            citation = plain(p)
        item = dict(p)
        item['citation'] = citation
        out.append(item)

    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
