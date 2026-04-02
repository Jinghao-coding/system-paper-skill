#!/usr/bin/env python3
import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
BUILD_CFG = BASE / 'scripts' / 'build_query_config.py'
BUILD_URLS = BASE / 'scripts' / 'build_query_urls.py'
FETCH_PAPERS = BASE / 'scripts' / 'fetch_papers.py'
FORMAT_CITATION = BASE / 'scripts' / 'format_citation.py'
GET_BIBTEX = BASE / 'scripts' / 'get_bibtex.py'


def run_py(script, args):
    cmd = [sys.executable, str(script)] + args
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or f'failed: {cmd}')
    return json.loads(proc.stdout)


def main():
    parser = argparse.ArgumentParser(description='Search paper helper for system-paper-skill')
    parser.add_argument('--topic', required=True)
    parser.add_argument('--top-k', type=int, default=12)
    parser.add_argument('--per-venue-limit', type=int, default=2)
    parser.add_argument('--citation-style', choices=['ieee', 'apa', 'plain'], default='ieee')
    parser.add_argument('--output', choices=['json', 'markdown'], default='json')
    args = parser.parse_args()

    cfg = run_py(BUILD_CFG, ['--topic', args.topic, '--top-k', str(args.top_k), '--format', 'json'])

    with tempfile.NamedTemporaryFile('w', suffix='.json', delete=False, encoding='utf-8') as tf:
        json.dump(cfg['venues'], tf, ensure_ascii=False, indent=2)
        temp_path = tf.name

    urls = run_py(BUILD_URLS, ['--topic', args.topic, '--venues-json', temp_path, '--limit', str(args.top_k), '--format', 'json'])
    papers_obj = run_py(FETCH_PAPERS, ['--topic', args.topic, '--top-k', str(args.top_k), '--per-venue-limit', str(args.per_venue_limit), '--format', 'json'])

    with tempfile.NamedTemporaryFile('w', suffix='.json', delete=False, encoding='utf-8') as tf2:
        json.dump(papers_obj['papers'], tf2, ensure_ascii=False, indent=2)
        papers_path = tf2.name

    cited = run_py(FORMAT_CITATION, ['--input', papers_path, '--style', args.citation_style])
    with tempfile.NamedTemporaryFile('w', suffix='.json', delete=False, encoding='utf-8') as tf3:
        json.dump(cited, tf3, ensure_ascii=False, indent=2)
        cited_path = tf3.name

    enriched = run_py(GET_BIBTEX, ['--input', cited_path])

    merged = {
        'topic': args.topic,
        'selected_areas': cfg['selected_areas'],
        'search_phrases': cfg['search_phrases'],
        'venues': cfg['venues'],
        'query_urls': urls['global_queries'],
        'per_venue_queries': urls['per_venue_queries'],
        'papers': enriched,
        'workflow': [
            '1. 先查看 selected_areas 和 venues，确定优先 venue',
            '2. 优先打开 per_venue_queries 中与 venues 对齐的 venue_link 或 dblp_search_url',
            '3. 抓取候选论文的 title/authors/year/venue/url',
            '4. 输出 citation 和 bibtex；若结果不足，再用 semantic_scholar_url 和 openalex_url 扩展',
            '5. 对候选论文按 relevance、年份、引用和系统相关性筛选'
        ]
    }

    if args.output == 'json':
        print(json.dumps(merged, ensure_ascii=False, indent=2))
    else:
        print(f'# Paper search helper for {args.topic}\n')
        print('## Selected areas')
        for a in merged['selected_areas']:
            print(f'- {a}')
        print('\n## Search phrases')
        for p in merged['search_phrases']:
            print(f'- {p}')
        print('\n## Papers')
        print('| year | target_venue | title | authors | citation |')
        print('|---:|---|---|---|---|')
        for p in merged['papers']:
            authors = ', '.join(p.get('authors', []))
            citation = (p.get('citation') or '').replace('|', '\\|')
            title = (p.get('title') or '').replace('|', '\\|')
            print(f"| {p.get('year','')} | {p.get('target_venue','')} | {title} | {authors} | {citation} |")
        print('\n## Workflow')
        for step in merged['workflow']:
            print(f'- {step}')


if __name__ == '__main__':
    main()
