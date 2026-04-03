#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

USER_AGENT = 'system-paper-skill/2.1 (bibtex verifier)'


def normalize_text(text):
    if text is None:
        return ''
    text = str(text).lower().strip()
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'[_\-/]+', ' ', text)
    text = re.sub(r'[^\w\s\u4e00-\u9fff]+', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()


def tokenize(text):
    return [t for t in normalize_text(text).split() if len(t) >= 2]


def fetch_json(url, headers=None, timeout=20):
    req = urllib.request.Request(url, headers=headers or {'User-Agent': USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode('utf-8', errors='replace'))


def safe_fetch_json(url, headers=None, timeout=20):
    try:
        return fetch_json(url, headers=headers, timeout=timeout), None
    except Exception as e:
        return None, str(e)


def normalize_doi(value):
    if not value:
        return ''
    value = str(value).strip().lower()
    value = value.replace('https://doi.org/', '').replace('http://doi.org/', '')
    value = value.replace('doi:', '')
    return value.strip()


def parse_bibtex_fields(bibtex):
    fields = {}
    if not bibtex:
        return fields
    for key in ['title', 'author', 'journal', 'booktitle', 'year', 'doi', 'url']:
        match = re.search(rf'{key}\s*=\s*[{{\"](.*?)[}}\"]\s*(,|\n)', bibtex, flags=re.IGNORECASE | re.DOTALL)
        if match:
            fields[key] = match.group(1).strip()
    return fields


def load_input(path):
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    if isinstance(data, dict) and 'papers' in data:
        return data['papers']
    if isinstance(data, list):
        return data
    raise ValueError('input json must be a paper list or an object with papers field')


def important_tokens(text):
    tokens = []
    for t in tokenize(text):
        if len(t) >= 4:
            tokens.append(t)
    return tokens


def overlap_score(expected, observed):
    exp = set(tokenize(expected))
    obs = set(tokenize(observed))
    if not exp or not obs:
        return 0.0, []
    overlap = sorted(exp & obs)
    return len(overlap) / max(1, min(len(exp), len(obs))), overlap


def strong_title_match(expected, observed):
    expected_norm = normalize_text(expected)
    observed_norm = normalize_text(observed)
    if not expected_norm or not observed_norm:
        return False, 0.0, [], []
    score, overlap = overlap_score(expected_norm, observed_norm)
    exp_important = set(important_tokens(expected_norm))
    obs_important = set(important_tokens(observed_norm))
    important_overlap = sorted(exp_important & obs_important)
    exact = expected_norm == observed_norm
    expected_tokens = expected_norm.split()
    observed_tokens = observed_norm.split()
    long_substring = (
        len(expected_tokens) >= 4 and len(observed_tokens) >= 4 and
        (expected_norm in observed_norm or observed_norm in expected_norm)
    )
    strong = exact or long_substring or (len(important_overlap) >= 3 and score >= 0.6)
    return strong, score, overlap, important_overlap


def verify_via_doi(doi):
    doi = normalize_doi(doi)
    if not doi:
        return None
    url = f'https://api.crossref.org/works/{urllib.parse.quote(doi)}'
    data, err = safe_fetch_json(url, headers={'User-Agent': USER_AGENT})
    if err or not data:
        return None
    message = data.get('message') or {}
    title = ''
    if isinstance(message.get('title'), list) and message.get('title'):
        title = message['title'][0]
    elif isinstance(message.get('title'), str):
        title = message['title']
    authors = []
    for a in message.get('author', []) or []:
        given = (a.get('given') or '').strip()
        family = (a.get('family') or '').strip()
        full = ' '.join(x for x in [given, family] if x)
        if full:
            authors.append(full)
    venue = ''
    for key in ['container-title', 'short-container-title']:
        value = message.get(key)
        if isinstance(value, list) and value:
            venue = value[0]
            break
    year = None
    issued = (((message.get('issued') or {}).get('date-parts') or [[]])[0] or [])
    if issued:
        year = issued[0]
    return {
        'source': 'crossref-doi',
        'doi': normalize_doi(message.get('DOI') or doi),
        'title': title,
        'authors': authors,
        'venue': venue,
        'year': year,
        'url': (message.get('URL') or '').strip(),
    }


def verify_via_title(title, year=None):
    query = (title or '').strip()
    if not query:
        return None
    params = {'query.title': query, 'rows': '5'}
    if year:
        params['filter'] = f'from-pub-date:{year},until-pub-date:{year}'
    url = 'https://api.crossref.org/works?' + urllib.parse.urlencode(params)
    data, err = safe_fetch_json(url, headers={'User-Agent': USER_AGENT})
    if err or not data:
        return None
    items = ((data.get('message') or {}).get('items') or [])
    if not items:
        return None
    best = None
    best_score = -1.0
    for item in items:
        cand_title = ''
        raw_title = item.get('title') or []
        if isinstance(raw_title, list) and raw_title:
            cand_title = raw_title[0]
        elif isinstance(raw_title, str):
            cand_title = raw_title
        score, overlap = overlap_score(title, cand_title)
        strong, _, _, important_overlap = strong_title_match(title, cand_title)
        if not strong:
            continue
        item_year = None
        issued = (((item.get('issued') or {}).get('date-parts') or [[]])[0] or [])
        if issued:
            item_year = issued[0]
        if year and item_year and str(item_year) == str(year):
            score += 0.2
        score += min(0.2, 0.05 * len(important_overlap))
        if score > best_score:
            authors = []
            for a in item.get('author', []) or []:
                given = (a.get('given') or '').strip()
                family = (a.get('family') or '').strip()
                full = ' '.join(x for x in [given, family] if x)
                if full:
                    authors.append(full)
            venue = ''
            for key in ['container-title', 'short-container-title']:
                value = item.get(key)
                if isinstance(value, list) and value:
                    venue = value[0]
                    break
            best = {
                'source': 'crossref-title',
                'doi': normalize_doi(item.get('DOI') or ''),
                'title': cand_title,
                'authors': authors,
                'venue': venue,
                'year': item_year,
                'url': (item.get('URL') or '').strip(),
            }
            best_score = score
    if best_score < 0.45:
        return None
    best['match_score'] = round(best_score, 4)
    return best


def verify_entry(paper):
    bib_fields = parse_bibtex_fields(paper.get('bibtex', ''))
    claimed_title = paper.get('title') or bib_fields.get('title') or ''
    claimed_year = paper.get('year') or bib_fields.get('year') or None
    claimed_doi = normalize_doi(paper.get('doi') or bib_fields.get('doi') or '')
    claimed_venue = paper.get('venue') or paper.get('target_venue') or bib_fields.get('journal') or bib_fields.get('booktitle') or ''

    verified = None
    method = None
    if claimed_doi:
        verified = verify_via_doi(claimed_doi)
        method = 'doi'
    if not verified:
        verified = verify_via_title(claimed_title, claimed_year)
        method = 'title'

    title_strong, title_score, title_overlap, important_overlap = strong_title_match(claimed_title, (verified or {}).get('title', ''))
    venue_score, venue_overlap = overlap_score(claimed_venue, (verified or {}).get('venue', ''))
    year_match = bool(verified and claimed_year and verified.get('year') and str(claimed_year) == str(verified.get('year')))
    doi_match = bool(verified and claimed_doi and normalize_doi(verified.get('doi')) == claimed_doi)
    exists = bool(verified and (doi_match or title_strong or (title_score >= 0.9 and year_match and len(important_overlap) >= 3)))

    return {
        'title': claimed_title,
        'claimed_year': claimed_year,
        'claimed_doi': claimed_doi,
        'claimed_venue': claimed_venue,
        'verification': {
            'exists': exists,
            'method': method if verified else 'unverified',
            'title_score': round(title_score, 4),
            'title_overlap': title_overlap,
            'important_title_overlap': important_overlap,
            'venue_score': round(venue_score, 4),
            'venue_overlap': venue_overlap,
            'year_match': year_match,
            'doi_match': doi_match,
            'verified_record': verified,
        }
    }


def main():
    parser = argparse.ArgumentParser(description='Verify BibTeX/citation entries against real papers via DOI and Crossref title search')
    parser.add_argument('--input', required=True, help='input json file containing papers or {papers: [...]}')
    parser.add_argument('--output', choices=['json', 'markdown'], default='json')
    args = parser.parse_args()

    papers = load_input(args.input)
    verified = []
    for p in papers:
        item = dict(p)
        item.update(verify_entry(p))
        verified.append(item)

    if args.output == 'json':
        print(json.dumps(verified, ensure_ascii=False, indent=2))
    else:
        lines = []
        for i, p in enumerate(verified, 1):
            v = p.get('verification', {})
            status = 'verified' if v.get('exists') else 'unverified'
            lines.append(f'## {i}. {p.get("title", "") or "(untitled)"}')
            lines.append(f'- status: {status}')
            lines.append(f'- method: {v.get("method", "")}')
            lines.append(f'- title_score: {v.get("title_score", 0)}')
            lines.append(f'- doi_match: {v.get("doi_match", False)}')
            lines.append(f'- year_match: {v.get("year_match", False)}')
            record = v.get('verified_record') or {}
            if record:
                lines.append(f'- verified_title: {record.get("title", "")}')
                lines.append(f'- verified_venue: {record.get("venue", "")}')
                lines.append(f'- verified_year: {record.get("year", "")}')
                lines.append(f'- verified_url: {record.get("url", "")}')
            lines.append('')
        print('\n'.join(lines))


if __name__ == '__main__':
    main()
