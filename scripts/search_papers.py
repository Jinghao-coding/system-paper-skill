#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
BUILD_QUERY_CONFIG = SCRIPT_DIR / 'build_query_config.py'
BUILD_QUERY_URLS = SCRIPT_DIR / 'build_query_urls.py'
FETCH_PAPERS = SCRIPT_DIR / 'fetch_papers.py'
FORMAT_CITATION = SCRIPT_DIR / 'format_citation.py'
GET_BIBTEX = SCRIPT_DIR / 'get_bibtex.py'
VERIFY_BIBTEX = SCRIPT_DIR / 'verify_bibtex.py'


def run_py(script_path, args):
    cmd = [sys.executable, str(script_path)] + args
    out = subprocess.check_output(cmd, text=True)
    return json.loads(out)


def write_temp_json(data):
    tf = tempfile.NamedTemporaryFile('w', suffix='.json', delete=False, encoding='utf-8')
    with tf:
        json.dump(data, tf, ensure_ascii=False, indent=2)
    return tf.name


def merge_papers_with_citations_and_bibtex(papers, citations, bibtex_entries, verification_entries):
    merged = []
    for i, p in enumerate(papers):
        item = dict(p)
        if i < len(citations):
            item['citation'] = citations[i].get('citation', '')
        else:
            item['citation'] = ''
        if i < len(bibtex_entries):
            item['bibtex'] = bibtex_entries[i].get('bibtex', '')
            item['bibtex_source'] = bibtex_entries[i].get('bibtex_source', '')
        else:
            item['bibtex'] = ''
            item['bibtex_source'] = ''
        if i < len(verification_entries):
            item['verification'] = verification_entries[i].get('verification', {})
            if verification_entries[i].get('claimed_doi'):
                item['claimed_doi'] = verification_entries[i].get('claimed_doi', '')
        else:
            item['verification'] = {}
        merged.append(item)
    return merged


def to_markdown(payload):
    lines = []
    lines.append('# System Paper Search Results')
    lines.append('')
    lines.append(f"- **Topic**: {payload['topic']}")
    lines.append(f"- **Language**: {payload['language']}")
    lines.append(f"- **Selected areas**: {', '.join(payload.get('selected_areas', []))}")
    lines.append(f"- **Preferred type**: {payload.get('preferred_type', 'balanced')}")
    lines.append(f"- **Citation style**: {payload.get('citation_style', 'ieee')}")
    lines.append('')

    lines.append('## Recommended venues')
    lines.append('')
    lines.append('| short_name | type | ccf | area | full_name |')
    lines.append('|---|---|---|---|---|')
    for v in payload.get('venues', []):
        lines.append(f"| {v.get('short_name')} | {v.get('type')} | {v.get('ccf')} | {v.get('area')} | {v.get('full_name')} |")
    lines.append('')

    lines.append('## Query URLs')
    lines.append('')
    urls = payload.get('query_urls', {})
    if urls:
        lines.append(f"- DBLP: {urls.get('dblp', '')}")
        lines.append(f"- Google Scholar: {urls.get('google_scholar', '')}")
        lines.append(f"- Semantic Scholar: {urls.get('semantic_scholar', '')}")
        lines.append(f"- OpenAlex: {urls.get('openalex', '')}")
    lines.append('')

    lines.append(f"## Papers ({len(payload.get('papers', []))} results)")
    lines.append('')
    for i, p in enumerate(payload.get('papers', []), 1):
        title = p.get('title') or '(No results found)'
        lines.append(f"### {i}. {title}")
        lines.append('')
        lines.append(f"- **Target venue**: {p.get('target_venue', '')}")
        lines.append(f"- **Matched venue**: {p.get('venue', '')}")
        lines.append(f"- **Year**: {p.get('year', '')}")
        lines.append(f"- **Authors**: {', '.join(p.get('authors', []))}")
        lines.append(f"- **Source**: {p.get('source', '')}")
        if p.get('relevance'):
            lines.append(f"- **Relevance score**: {p.get('relevance', {}).get('score', '')}")
            overlap = ', '.join(p.get('relevance', {}).get('topic_overlap', []))
            if overlap:
                lines.append(f"- **Topic overlap**: {overlap}")
        if p.get('citation_count') is not None:
            lines.append(f"- **Citation count**: {p['citation_count']}")
        if p.get('doi'):
            lines.append(f"- **DOI**: {p.get('doi')}")
        if p.get('url'):
            lines.append(f"- **URL**: {p.get('url')}")
        if p.get('abstract'):
            lines.append(f"- **Abstract**: {p.get('abstract')}")
        lines.append('')
        if p.get('citation'):
            lines.append(f"**Citation ({payload.get('citation_style', 'ieee')})**:")
            lines.append('```')
            lines.append(p.get('citation'))
            lines.append('```')
            lines.append('')
        if p.get('bibtex'):
            lines.append(f"**BibTeX** ({p.get('bibtex_source', 'unknown')}):")
            lines.append('```bibtex')
            lines.append(p.get('bibtex'))
            lines.append('```')
            lines.append('')
        verification = p.get('verification') or {}
        if verification:
            lines.append('**Reference verification**:')
            lines.append(f"- Exists in external metadata index: {verification.get('exists', False)}")
            lines.append(f"- Verification method: {verification.get('method', '')}")
            lines.append(f"- Title match score: {verification.get('title_score', 0)}")
            lines.append(f"- DOI exact match: {verification.get('doi_match', False)}")
            lines.append(f"- Year match: {verification.get('year_match', False)}")
            record = verification.get('verified_record') or {}
            if record.get('title'):
                lines.append(f"- Verified title: {record.get('title')}")
            if record.get('venue'):
                lines.append(f"- Verified venue: {record.get('venue')}")
            if record.get('url'):
                lines.append(f"- Verified URL: {record.get('url')}")
            lines.append('')
    return '\n'.join(lines)


def detect_language(text):
    return 'zh' if any('\u4e00' <= ch <= '\u9fff' for ch in text or '') else 'en'


def main():
    parser = argparse.ArgumentParser(description='Unified system paper search workflow with bilingual support and stronger reranking')
    parser.add_argument('--topic', required=True, help='research topic or query in English or Chinese')
    parser.add_argument('--top-k', type=int, default=12, help='number of venues to search')
    parser.add_argument('--per-venue-limit', type=int, default=2, help='max papers per venue')
    parser.add_argument('--type', choices=['balanced', 'conference', 'journal'], default=None, help='optional preferred venue type')
    parser.add_argument('--citation-style', choices=['ieee', 'apa', 'plain'], default='ieee')
    parser.add_argument('--output', choices=['json', 'markdown'], default='json')
    args = parser.parse_args()

    cfg_args = ['--topic', args.topic, '--top-k', str(args.top_k), '--format', 'json']
    if args.type:
        cfg_args.extend(['--type', args.type])
    cfg = run_py(BUILD_QUERY_CONFIG, cfg_args)

    selected_venues_path = write_temp_json(cfg['venues'])
    urls = run_py(BUILD_QUERY_URLS, [
        '--topic', args.topic,
        '--venues-json', selected_venues_path,
        '--limit', str(args.top_k),
        '--format', 'json'
    ])

    fetch_args = [
        '--topic', args.topic,
        '--top-k', str(args.top_k),
        '--per-venue-limit', str(args.per_venue_limit),
        '--format', 'json'
    ]
    if args.type:
        fetch_args.extend(['--type', args.type])
    fetch_result = run_py(FETCH_PAPERS, fetch_args)
    papers = fetch_result.get('papers', [])

    papers_path = write_temp_json(papers)
    citations = run_py(FORMAT_CITATION, [
        '--input', papers_path,
        '--style', args.citation_style
    ])
    bibtex_entries = run_py(GET_BIBTEX, [
        '--input', papers_path,
        '--output', 'json'
    ])

    verification_entries = run_py(VERIFY_BIBTEX, [
        '--input', papers_path,
        '--output', 'json'
    ])

    merged_papers = merge_papers_with_citations_and_bibtex(papers, citations, bibtex_entries, verification_entries)
    language = fetch_result.get('language') or detect_language(args.topic)

    payload = {
        'topic': args.topic,
        'language': language,
        'selected_areas': cfg.get('selected_areas', []),
        'preferred_type': cfg.get('preferred_type', 'balanced'),
        'search_phrases': cfg.get('search_phrases', []),
        'venues': cfg.get('venues', []),
        'grouped_venues': cfg.get('grouped_venues', {}),
        'query_urls': urls.get('global_queries', {}),
        'per_venue_queries': urls.get('per_venue_queries', []),
        'papers': merged_papers,
        'citation_style': args.citation_style,
        'workflow': [
            'build_query_config',
            'build_query_urls',
            'fetch_papers (DBLP > OpenAlex > Crossref > Semantic Scholar)',
            'format_citation',
            'get_bibtex',
            'verify_bibtex'
        ]
    }

    if args.output == 'json':
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(to_markdown(payload))


if __name__ == '__main__':
    main()
