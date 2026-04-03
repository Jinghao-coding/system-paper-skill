#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import json
import re


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


def fmt_authors(authors):
    """格式化作者列表为可读字符串"""
    if not authors:
        return ''
    
    # 标准化所有作者为字符串
    names = [normalize_author(a) for a in authors]
    names = [n for n in names if n]
    
    if not names:
        return ''
    if len(names) == 1:
        return names[0]
    if len(names) == 2:
        return f'{names[0]} and {names[1]}'
    return ', '.join(names[:-1]) + f', and {names[-1]}'


def clean_text(text):
    if not text:
        return ''
    text = re.sub(r'<[^>]+>', ' ', str(text))
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def ieee(p):
    authors = fmt_authors(p.get('authors', []))
    title = clean_text(p.get('title'))
    venue = clean_text(p.get('venue') or p.get('target_venue') or '')
    year = p.get('year') or ''
    url = p.get('url') or ''
    doi = p.get('doi') or ''
    parts = []
    if authors:
        parts.append(f'{authors},')
    if title:
        parts.append(f'"{title},"')
    if venue:
        parts.append(venue + ',')
    if year:
        parts.append(str(year) + '.')
    if doi:
        parts.append(doi)
    elif url:
        parts.append(url)
    return ' '.join(parts).strip()


def apa(p):
    authors = fmt_authors(p.get('authors', []))
    title = clean_text(p.get('title'))
    venue = clean_text(p.get('venue') or p.get('target_venue') or '')
    year = p.get('year') or 'n.d.'
    url = p.get('url') or ''
    doi = p.get('doi') or ''
    text = ''
    if authors:
        text += f'{authors} '
    text += f'({year}). {title}. '
    if venue:
        text += f'{venue}. '
    if doi:
        text += doi
    elif url:
        text += url
    return text.strip()


def plain(p):
    title = clean_text(p.get('title'))
    authors = fmt_authors(p.get('authors', []))
    venue = clean_text(p.get('venue') or p.get('target_venue') or '')
    year = p.get('year') or ''
    source = p.get('source') or ''
    return f'{title} | {authors} | {venue} | {year} | {source}'.strip(' |')


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
