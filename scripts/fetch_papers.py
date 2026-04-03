#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import json
import re
import subprocess
import sys
import urllib.parse
import urllib.request
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
BUILD_QUERY_CONFIG = SCRIPT_DIR / 'build_query_config.py'

SOURCE_PRIORITY = {
    'dblp': 0,
    'openalex': 1,
    'crossref': 2,
    'semantic_scholar': 3,
    'unavailable': 99,
}

USER_AGENT = 'system-paper-skill/2.0 (paper metadata fetcher)'
STOPWORDS = {
    'the', 'a', 'an', 'and', 'or', 'for', 'of', 'to', 'in', 'on', 'with', 'by', 'from',
    'system', 'systems', 'paper', 'papers', 'study', 'towards', 'using', 'based', 'via',
    'user', 'users', 'method', 'approach', 'toward', 'survey', 'review',
    '我', '想', '查', '相关', '论文', '方向', '帮我', '整理', '一份', '主要', '关心', '只给我', '推荐'
}

VENUE_ALIASES = {
    'osdi': ['osdi', 'operating systems design and implementation'],
    'sosp': ['sosp', 'operating systems principles'],
    'asplos': ['asplos', 'architectural support for programming languages and operating systems'],
    'nsdi': ['nsdi', 'networked systems design and implementation', 'network system design and implementation'],
    'eurosys': ['eurosys', 'european conference on computer systems'],
    'fast': ['fast', 'file and storage technologies'],
    'socc': ['socc', 'symposium on cloud computing'],
    'middleware': ['middleware', 'international middleware conference'],
    'sigcomm': ['sigcomm', 'computer communication'],
    'conext': ['conext', 'emerging networking experiments and technologies'],
    'imc': ['imc', 'internet measurement conference'],
    'ton': ['ton', 'transactions on networking'],
    'tpds': ['tpds', 'transactions on parallel and distributed systems'],
    'tocs': ['tocs', 'transactions on computer systems'],
    'toplas': ['toplas', 'transactions on programming languages and systems'],
    'pldi': ['pldi', 'programming language design and implementation'],
    'popl': ['popl', 'principles of programming languages'],
    'cgo': ['cgo', 'code generation and optimization'],
    'pact': ['pact', 'parallel architectures and compilation techniques'],
    'isca': ['isca', 'computer architecture'],
    'micro': ['micro', 'microarchitecture'],
    'hpca': ['hpca', 'high performance computer architecture'],
    'atc': ['atc', 'usenix annual technical conference', 'sigops annual technical conference'],
}

SEMANTIC_EQUIV = {
    'ai': ['machine learning', 'ml', 'llm'],
    'serving': ['inference', 'online serving', 'serving'],
    'inference': ['serving', 'online serving', 'model inference'],
    'observability': ['monitoring', 'tracing', 'telemetry', 'logging'],
    'cloud': ['cloud native', 'kubernetes', 'container'],
    'container': ['kubernetes', 'virtualization', 'cloud native'],
    'reliability': ['fault tolerance', 'availability', 'resilience'],
    'latency': ['tail latency', 'response time'],
    'training': ['distributed training', 'parameter server'],
    '推理': ['serving', 'inference'],
    '可观测性': ['monitoring', 'tracing', 'telemetry'],
    '训练': ['distributed training', 'parameter server'],
}


def run_py(script_path, args):
    cmd = [sys.executable, str(script_path)] + args
    out = subprocess.check_output(cmd, text=True)
    return json.loads(out)


def http_get_json(url, headers=None, timeout=20):
    req = urllib.request.Request(url, headers=headers or {'User-Agent': USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode('utf-8', errors='replace'))


def safe_get(url, headers=None, timeout=20):
    try:
        return http_get_json(url, headers=headers, timeout=timeout), None
    except Exception as e:
        return None, str(e)


def normalize_text(text):
    if not text:
        return ''
    text = str(text).lower().strip()
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'[_\-/]+', ' ', text)
    text = re.sub(r'[^\w\s\u4e00-\u9fff]+', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()


def normalize_title(title):
    return normalize_text(title)


def normalize_doi(doi):
    if not doi:
        return ''
    doi = doi.strip().lower()
    doi = doi.replace('https://doi.org/', '').replace('http://doi.org/', '')
    return doi


def tokenize(text):
    text = normalize_text(text)
    if not text:
        return []
    parts = []
    for token in text.split():
        if len(token) < 2:
            continue
        if token in STOPWORDS:
            continue
        parts.append(token)
        for expanded in SEMANTIC_EQUIV.get(token, []):
            parts.extend(expanded.split())
    return parts


def unique_key(paper):
    doi = normalize_doi(paper.get('doi'))
    if doi:
        return f'doi:{doi}'
    title = normalize_title(paper.get('title'))
    year = str(paper.get('year') or '')
    return f'title:{title}|year:{year}'


def better_source(new_source, old_source):
    return SOURCE_PRIORITY.get(new_source, 999) < SOURCE_PRIORITY.get(old_source, 999)


def dedupe_keep_priority(papers):
    kept = {}
    for p in papers:
        key = unique_key(p)
        if key not in kept:
            kept[key] = p
            continue
        current = kept[key]
        new_score = p.get('relevance', {}).get('score', 0)
        old_score = current.get('relevance', {}).get('score', 0)
        if new_score > old_score or (new_score == old_score and better_source(p.get('source'), current.get('source'))):
            kept[key] = p
    return list(kept.values())


def reconstruct_openalex_abstract(inv_idx):
    if not inv_idx:
        return ''
    positions = []
    for word, pos_list in inv_idx.items():
        for pos in pos_list:
            positions.append((pos, word))
    positions.sort(key=lambda x: x[0])
    return ' '.join(word for _, word in positions)


def canonicalize_venue_name(text):
    norm = normalize_text(text)
    for key, aliases in VENUE_ALIASES.items():
        if any(alias in norm for alias in aliases):
            return key
    return norm


def venue_match_score(candidate_venue, target_venue):
    candidate = canonicalize_venue_name(candidate_venue)
    target_short = canonicalize_venue_name(target_venue.get('short_name', ''))
    target_full = canonicalize_venue_name(target_venue.get('full_name', ''))
    if not candidate:
        return 0
    score = 0
    if candidate == target_short or candidate == target_full:
        score += 8
    if target_short and target_short in candidate:
        score += 4
    if target_full and (target_full in candidate or candidate in target_full):
        score += 4
    return score


def paper_text_value(value):
    if value is None:
        return ''
    if isinstance(value, str):
        return value
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, list):
        return ' '.join(paper_text_value(v) for v in value)
    if isinstance(value, dict):
        for key in ('name', 'title', 'display_name', 'text'):
            if key in value:
                return paper_text_value(value.get(key))
        return ' '.join(paper_text_value(v) for v in value.values())
    return str(value)


def topic_match_score(topic, paper):
    topic_tokens = set(tokenize(topic))
    text = ' '.join([
        paper_text_value(paper.get('title', '')),
        paper_text_value(paper.get('abstract', '')),
        paper_text_value(paper.get('venue', '')),
        paper_text_value(paper.get('authors', [])),
        paper_text_value(paper.get('target_venue', '')),
    ])
    paper_tokens = set(tokenize(text))
    overlap = sorted(topic_tokens & paper_tokens)
    return len(overlap), overlap


def source_quality_bonus(source):
    return {
        'dblp': 2,
        'openalex': 1,
        'crossref': 0,
        'semantic_scholar': 0,
    }.get(source, 0)


def recency_bonus(year):
    if not year:
        return 0
    if year >= 2023:
        return 2
    if year >= 2020:
        return 1
    return 0


def citation_bonus(citation_count):
    if citation_count is None:
        return 0
    if citation_count >= 100:
        return 2
    if citation_count > 0:
        return 1
    return 0


def annotate_relevance(topic, target_venue, paper):
    overlap_score, overlap_tokens = topic_match_score(topic, paper)
    venue_score = venue_match_score(paper.get('venue', ''), target_venue)
    total = overlap_score * 2 + venue_score + source_quality_bonus(paper.get('source')) + recency_bonus(paper.get('year') or 0) + citation_bonus(paper.get('citation_count'))
    item = dict(paper)
    item['relevance'] = {
        'score': total,
        'topic_overlap': overlap_tokens,
        'venue_score': venue_score,
        'source_bonus': source_quality_bonus(paper.get('source')),
        'recency_bonus': recency_bonus(paper.get('year') or 0),
        'citation_bonus': citation_bonus(paper.get('citation_count')),
    }
    return item


def is_relevant(topic, target_venue, paper, min_score=4):
    scored = annotate_relevance(topic, target_venue, paper)
    venue_score = scored['relevance']['venue_score']
    overlap = len(scored['relevance']['topic_overlap'])
    score = scored['relevance']['score']
    keep = score >= min_score and (venue_score >= 4 or overlap >= 2 or (venue_score >= 1 and overlap >= 1))
    return keep, scored


def search_openalex(topic, venue, limit=8):
    query = topic
    if venue.get('short_name'):
        query += f" {venue['short_name']}"
    params = {'search': query, 'per-page': str(limit)}
    url = 'https://api.openalex.org/works?' + urllib.parse.urlencode(params)
    data, err = safe_get(url)
    if err:
        return [], err
    results = []
    for item in data.get('results', []):
        host = item.get('primary_location') or {}
        source = host.get('source') or {}
        venue_name = source.get('display_name') or venue.get('short_name', '')
        authors = []
        for a in item.get('authorships', []):
            author = a.get('author') or {}
            name = author.get('display_name')
            if name:
                authors.append(name)
        doi = normalize_doi(item.get('doi') or '')
        doi_url = f'https://doi.org/{doi}' if doi else ''
        results.append({
            'title': item.get('display_name', ''),
            'authors': authors,
            'year': item.get('publication_year'),
            'venue': venue_name,
            'url': (item.get('primary_location') or {}).get('landing_page_url') or item.get('id'),
            'doi': doi_url,
            'abstract': reconstruct_openalex_abstract(item.get('abstract_inverted_index')),
            'citation_count': item.get('cited_by_count'),
            'source': 'openalex',
            'target_venue': venue['short_name'],
            'target_venue_link': venue['link'],
        })
    return results, None


def search_dblp(topic, venue, limit=8):
    query = f"{topic} {venue['short_name']}"
    params = {'q': query, 'h': str(limit), 'format': 'json'}
    url = 'https://dblp.org/search/publ/api?' + urllib.parse.urlencode(params)
    data, err = safe_get(url)
    if err:
        return [], err
    hits = (((data.get('result') or {}).get('hits') or {}).get('hit')) or []
    if isinstance(hits, dict):
        hits = [hits]
    results = []
    for h in hits:
        info = h.get('info') or {}
        authors_raw = info.get('authors') or {}
        authors = authors_raw.get('author') or []
        if isinstance(authors, str):
            authors = [authors]
        elif isinstance(authors, dict):
            txt = authors.get('text')
            authors = [txt] if txt else []
        doi = info.get('doi') or ''
        doi_url = f'https://doi.org/{normalize_doi(doi)}' if doi else ''
        results.append({
            'title': info.get('title', ''),
            'authors': authors,
            'year': int(info.get('year')) if str(info.get('year', '')).isdigit() else info.get('year'),
            'venue': info.get('venue') or venue['short_name'],
            'url': info.get('url') or '',
            'doi': doi_url,
            'abstract': '',
            'citation_count': None,
            'source': 'dblp',
            'target_venue': venue['short_name'],
            'target_venue_link': venue['link'],
        })
    return results, None


def search_crossref(topic, venue, limit=8):
    query = f"{topic} {venue['short_name']}"
    params = {'query.title': query, 'rows': str(limit)}
    url = 'https://api.crossref.org/works?' + urllib.parse.urlencode(params)
    data, err = safe_get(url, headers={'User-Agent': USER_AGENT, 'Accept': 'application/json'})
    if err:
        return [], err
    items = ((data.get('message') or {}).get('items')) or []
    results = []
    for item in items:
        title_list = item.get('title') or []
        title = title_list[0] if title_list else ''
        authors = []
        for a in item.get('author', []):
            given = a.get('given', '').strip()
            family = a.get('family', '').strip()
            name = ' '.join(x for x in [given, family] if x)
            if name:
                authors.append(name)
        year = None
        published = item.get('published-print') or item.get('published-online') or item.get('issued') or {}
        date_parts = published.get('date-parts') or []
        if date_parts and date_parts[0]:
            year = date_parts[0][0]
        container = item.get('container-title') or []
        venue_name = container[0] if container else venue['short_name']
        doi = item.get('DOI') or ''
        doi_url = f'https://doi.org/{normalize_doi(doi)}' if doi else ''
        results.append({
            'title': title,
            'authors': authors,
            'year': year,
            'venue': venue_name,
            'url': item.get('URL') or doi_url,
            'doi': doi_url,
            'abstract': item.get('abstract', '') or '',
            'citation_count': item.get('is-referenced-by-count'),
            'source': 'crossref',
            'target_venue': venue['short_name'],
            'target_venue_link': venue['link'],
        })
    return results, None


def search_semantic_scholar(topic, venue, limit=8):
    query = f"{topic} {venue['short_name']}"
    params = {
        'query': query,
        'limit': str(limit),
        'fields': 'title,authors,year,venue,url,abstract,citationCount,externalIds'
    }
    url = 'https://api.semanticscholar.org/graph/v1/paper/search?' + urllib.parse.urlencode(params)
    data, err = safe_get(url, headers={'User-Agent': USER_AGENT, 'Accept': 'application/json'})
    if err:
        return [], err
    results = []
    for item in data.get('data', []):
        external_ids = item.get('externalIds') or {}
        doi = external_ids.get('DOI') or ''
        doi_url = f'https://doi.org/{normalize_doi(doi)}' if doi else ''
        authors = [(a or {}).get('name') for a in item.get('authors', []) if (a or {}).get('name')]
        results.append({
            'title': item.get('title', ''),
            'authors': authors,
            'year': item.get('year'),
            'venue': item.get('venue') or venue['short_name'],
            'url': item.get('url') or doi_url,
            'doi': doi_url,
            'abstract': item.get('abstract') or '',
            'citation_count': item.get('citationCount'),
            'source': 'semantic_scholar',
            'target_venue': venue['short_name'],
            'target_venue_link': venue['link'],
        })
    return results, None


def search_with_priority(topic, venue, limit=3):
    attempts = []
    funcs = [
        ('dblp', search_dblp),
        ('openalex', search_openalex),
        ('crossref', search_crossref),
        ('semantic_scholar', search_semantic_scholar),
    ]
    all_scored = []
    for source_name, func in funcs:
        results, err = func(topic, venue, limit=max(limit * 3, 8))
        filtered = []
        for p in results:
            ok, scored = is_relevant(topic, venue, p)
            all_scored.append(scored)
            if ok:
                filtered.append(scored)
        attempts.append({'source': source_name, 'error': err, 'count': len(results), 'kept': len(filtered)})
        if filtered:
            filtered = sorted(filtered, key=lambda x: (x['relevance']['score'], x.get('citation_count') or 0, x.get('year') or 0), reverse=True)
            return filtered[:limit], attempts
    fallback = sorted(all_scored, key=lambda x: (x['relevance']['score'], x.get('citation_count') or 0, x.get('year') or 0), reverse=True)
    return fallback[:limit], attempts


def detect_language(text):
    return 'zh' if re.search(r'[\u4e00-\u9fff]', text or '') else 'en'


def main():
    parser = argparse.ArgumentParser(description='Fetch papers from multiple sources with venue canonicalization and reranking')
    parser.add_argument('--topic', required=True)
    parser.add_argument('--top-k', type=int, default=10)
    parser.add_argument('--per-venue-limit', type=int, default=2)
    parser.add_argument('--type', choices=['balanced', 'conference', 'journal'], default=None)
    parser.add_argument('--format', choices=['json', 'markdown'], default='json')
    args = parser.parse_args()

    cfg_args = ['--topic', args.topic, '--top-k', str(args.top_k), '--format', 'json']
    if args.type:
        cfg_args.extend(['--type', args.type])
    cfg = run_py(BUILD_QUERY_CONFIG, cfg_args)
    venues = cfg['venues']

    papers = []
    debug = []
    for venue in venues:
        venue_papers, attempts = search_with_priority(args.topic, venue, limit=args.per_venue_limit)
        papers.extend(venue_papers)
        debug.append({'venue': venue['short_name'], 'attempts': attempts})

    papers = dedupe_keep_priority(papers)
    papers = sorted(papers, key=lambda x: (x.get('relevance', {}).get('score', 0), x.get('citation_count') or 0, x.get('year') or 0), reverse=True)

    output = {
        'topic': args.topic,
        'language': detect_language(args.topic),
        'preferred_type': cfg.get('preferred_type', 'balanced'),
        'selected_areas': cfg['selected_areas'],
        'search_phrases': cfg['search_phrases'],
        'venues': venues,
        'papers': papers,
        'debug': debug,
    }

    if args.format == 'json':
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        print(f'# Fetched papers for {args.topic}\n')
        print('| score | year | source | target_venue | title | authors | venue |')
        print('|---:|---:|---|---|---|---|---|')
        for p in papers:
            authors = ', '.join(p.get('authors', []))
            score = p.get('relevance', {}).get('score', '')
            title = (p.get('title') or '').replace('|', '\\|')
            venue = (p.get('venue') or '').replace('|', '\\|')
            print(f"| {score} | {p.get('year','')} | {p.get('source','')} | {p.get('target_venue','')} | {title} | {authors} | {venue} |")


if __name__ == '__main__':
    main()
