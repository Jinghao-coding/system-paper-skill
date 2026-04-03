#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import json
import re
import urllib.request
from pathlib import Path

USER_AGENT = 'system-paper-skill/1.0 (bibtex fetcher)'


def normalize_author(author):
    """标准化作者格式 - 支持字符串或字典"""
    if isinstance(author, str):
        return author
    if isinstance(author, dict):
        name = author.get('name', '') or author.get('display_name', '')
        if name:
            return name
        given = author.get('given', '').strip()
        family = author.get('family', '').strip()
        if given or family:
            return ' '.join(x for x in [given, family] if x)
    return str(author) if author else ''


def load_papers(path):
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    if isinstance(data, dict) and 'papers' in data:
        return data['papers']
    if isinstance(data, list):
        return data
    raise ValueError('input json must be a paper list or an object with papers field')


def slug(text):
    text = (text or '').lower()
    text = re.sub(r'[^a-z0-9]+', '', text)
    return text[:32] or 'paper'


def local_bibtex_key(p):
    authors = p.get('authors') or []
    # 标准化作者
    names = [normalize_author(a) for a in authors]
    names = [n for n in names if n]
    first_author = slug(names[0].split()[-1] if names else 'unknown')
    year = str(p.get('year') or 'nd')
    title_slug = slug(p.get('title') or 'paper')[:12]
    return f'{first_author}{year}{title_slug}'


def local_make_bibtex(p):
    """启发式生成 BibTeX - 作为最后的兜底"""
    entry_type = 'inproceedings'
    venue = (p.get('venue') or '').lower()
    target = (p.get('target_venue') or '').lower()
    merged = venue + ' ' + target
    if any(k in merged for k in ['journal', 'transactions', 'letters', 'magazine', 'tocs', 'tos', 'tpds', 'ton']):
        # 期刊
        if not any(k in merged for k in ['conference', 'symposium', 'workshop', 'proc']):
            entry_type = 'article'

    key = local_bibtex_key(p)
    
    # 标准化作者
    authors_list = [normalize_author(a) for a in (p.get('authors') or [])]
    authors_list = [n for n in authors_list if n]
    authors = ' and '.join(authors_list)
    
    title = p.get('title') or ''
    year = p.get('year') or ''
    venue_name = p.get('venue') or p.get('target_venue') or ''
    doi = p.get('doi') or ''
    url = p.get('url') or ''

    fields = [
        f'  title = {{{title}}}',
        f'  author = {{{authors}}}',
        f'  year = {{{year}}}',
    ]
    if entry_type == 'article':
        fields.append(f'  journal = {{{venue_name}}}')
    else:
        fields.append(f'  booktitle = {{{venue_name}}}')
    if doi:
        fields.append(f'  doi = {{{doi.replace("https://doi.org/", "")}}}')
    if url:
        fields.append(f'  url = {{{url}}}')

    return '@{}{{{},\n{}}}'.format(entry_type, key, ',\n'.join(fields))


def fetch_url(url, headers=None, timeout=20):
    req = urllib.request.Request(url, headers=headers or {'User-Agent': USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode('utf-8', errors='replace')


def fetch_bibtex_via_doi(doi_url):
    """通过 DOI 获取 BibTeX (Crossref content negotiation)"""
    if not doi_url:
        return None
    doi = doi_url.replace('https://doi.org/', '').replace('http://doi.org/', '').strip()
    if not doi:
        return None

    url = f'https://doi.org/{doi}'
    try:
        bibtex = fetch_url(url, headers={
            'User-Agent': USER_AGENT,
            'Accept': 'application/x-bibtex'
        })
        return bibtex.strip()
    except Exception:
        return None


def fetch_bibtex_via_dblp(url):
    """通过 DBLP URL 获取 BibTeX"""
    if not url or 'dblp.org' not in url:
        return None

    bib_url = url.rstrip('/')
    if not bib_url.endswith('.bib'):
        bib_url = bib_url + '.bib'

    try:
        return fetch_url(bib_url).strip()
    except Exception:
        return None


def enrich_with_bibtex(papers):
    """为每篇论文获取 BibTeX，优先从权威源获取"""
    out = []
    for p in papers:
        bibtex = None
        bibtex_source = None

        doi = p.get('doi') or ''
        url = p.get('url') or ''

        # 优先级 1: DOI -> Crossref
        if doi:
            bibtex = fetch_bibtex_via_doi(doi)
            if bibtex:
                bibtex_source = 'doi/crossref'

        # 优先级 2: DBLP 自动补齐 .bib
        if not bibtex:
            bibtex = fetch_bibtex_via_dblp(url)
            if bibtex:
                bibtex_source = 'dblp'

        # 兜底: 本地生成
        if not bibtex:
            bibtex = local_make_bibtex(p)
            bibtex_source = 'generated'

        item = dict(p)
        item['bibtex'] = bibtex
        item['bibtex_source'] = bibtex_source
        out.append(item)

    return out


def main():
    parser = argparse.ArgumentParser(description='Get BibTeX for papers (prioritizes DOI/Crossref and DBLP over generated)')
    parser.add_argument('--input', required=True, help='input json file')
    parser.add_argument('--output', choices=['json', 'markdown'], default='json')
    args = parser.parse_args()

    papers = load_papers(args.input)
    enriched = enrich_with_bibtex(papers)

    if args.output == 'json':
        print(json.dumps(enriched, ensure_ascii=False, indent=2))
    else:
        lines = []
        for i, p in enumerate(enriched, 1):
            lines.append(f'## {i}. {p.get("title","")}')
            lines.append('')
            lines.append('```bibtex')
            lines.append(p.get('bibtex', ''))
            lines.append('```')
            lines.append('')
        print('\n'.join(lines))


if __name__ == '__main__':
    main()
