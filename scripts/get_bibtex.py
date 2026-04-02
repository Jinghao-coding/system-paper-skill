#!/usr/bin/env python3
import argparse
import json
import re


def slug(text):
    text = (text or 'paper').lower()
    text = re.sub(r'[^a-z0-9]+', '_', text)
    return text.strip('_') or 'paper'


def make_bibtex(p):
    authors = ' and '.join(p.get('authors', []))
    title = p.get('title') or 'Unknown Title'
    year = str(p.get('year') or '0000')
    venue = p.get('venue') or p.get('target_venue') or 'Unknown Venue'
    url = p.get('url') or ''
    doi = p.get('doi') or ''
    key_author = slug((p.get('authors') or ['anon'])[0].split()[-1] if p.get('authors') else 'anon')
    key_title = slug(title.split()[0] if title else 'paper')
    key = f'{key_author}{year}{key_title}'
    entry_type = 'inproceedings'
    if p.get('target_venue') and not any(x in venue.lower() for x in ['conference', 'symposium', 'workshop']):
        entry_type = 'article'
    fields = [
        f'  title={{ {title} }}',
        f'  author={{ {authors} }}',
        f'  year={{ {year} }}',
        f'  booktitle={{ {venue} }}' if entry_type == 'inproceedings' else f'  journal={{ {venue} }}'
    ]
    if doi:
        fields.append(f'  doi={{ {doi} }}')
    if url:
        fields.append(f'  url={{ {url} }}')
    bib = f'@{entry_type}{{{key},\n' + ',\n'.join(fields) + '\n}}'
    return bib


def main():
    parser = argparse.ArgumentParser(description='Generate BibTeX for papers')
    parser.add_argument('--input', required=True, help='json file containing papers list or search result object')
    args = parser.parse_args()

    with open(args.input, 'r', encoding='utf-8') as f:
        data = json.load(f)

    papers = data['papers'] if isinstance(data, dict) and 'papers' in data else data
    out = []
    for p in papers:
        item = dict(p)
        item['bibtex'] = make_bibtex(p)
        out.append(item)

    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
