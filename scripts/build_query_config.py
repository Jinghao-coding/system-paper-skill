#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from collections import defaultdict

BASE = Path(__file__).resolve().parent.parent
VENUES_PATH = BASE / 'data' / 'venues.json'

KEYWORD_TO_AREAS = {
    'os': ['systems-software', 'distributed-systems'],
    'kernel': ['systems-software'],
    'runtime': ['systems-software', 'programming-languages-and-compilers'],
    'compiler': ['programming-languages-and-compilers', 'computer-architecture'],
    'compilers': ['programming-languages-and-compilers', 'computer-architecture'],
    'pl': ['programming-languages-and-compilers'],
    'programming language': ['programming-languages-and-compilers'],
    'distributed': ['distributed-systems', 'cloud-systems'],
    'cloud': ['cloud-systems', 'distributed-systems'],
    'storage': ['storage-systems'],
    'file system': ['storage-systems', 'systems-software'],
    'filesystem': ['storage-systems', 'systems-software'],
    'network': ['network-systems'],
    'datacenter network': ['network-systems', 'distributed-systems'],
    'internet measurement': ['network-systems', 'performance-reliability'],
    'congestion': ['network-systems'],
    'rpc': ['distributed-systems', 'cloud-systems'],
    'scheduler': ['distributed-systems', 'systems-software', 'cloud-systems'],
    'scheduling': ['distributed-systems', 'systems-software', 'cloud-systems'],
    'resource isolation': ['distributed-systems', 'systems-software'],
    'multi-tenant': ['cloud-systems', 'distributed-systems'],
    'reliability': ['performance-reliability', 'software-engineering-for-systems'],
    'performance': ['performance-reliability', 'computer-architecture', 'distributed-systems'],
    'benchmark': ['performance-reliability'],
    'middleware': ['distributed-systems', 'cloud-systems'],
    'verification': ['software-engineering-for-systems', 'programming-languages-and-compilers'],
    'testing': ['software-engineering-for-systems', 'performance-reliability'],
    'program analysis': ['programming-languages-and-compilers', 'software-engineering-for-systems'],
    'gpu': ['computer-architecture', 'programming-languages-and-compilers'],
    'accelerator': ['computer-architecture'],
    '微架构': ['computer-architecture'],
    '体系结构': ['computer-architecture'],
    '分布式': ['distributed-systems', 'cloud-systems'],
    '云': ['cloud-systems', 'distributed-systems'],
    '存储': ['storage-systems'],
    '文件系统': ['storage-systems', 'systems-software'],
    '网络': ['network-systems'],
    '拥塞控制': ['network-systems'],
    '互联网测量': ['network-systems', 'performance-reliability'],
    '调度': ['distributed-systems', 'systems-software', 'cloud-systems'],
    '资源隔离': ['distributed-systems', 'systems-software'],
    '可靠性': ['performance-reliability', 'software-engineering-for-systems'],
    '系统软件': ['systems-software'],
    '操作系统': ['systems-software'],
    '编译器': ['programming-languages-and-compilers', 'computer-architecture'],
    '程序分析': ['programming-languages-and-compilers', 'software-engineering-for-systems'],
    '中间件': ['distributed-systems', 'cloud-systems'],
    '服务计算': ['cloud-systems'],
}

AREA_TO_QUERY_TERMS = {
    'computer-architecture': ['computer architecture', 'microarchitecture', 'accelerator', 'compiler optimization'],
    'distributed-systems': ['distributed systems', 'cluster scheduling', 'resource management', 'fault tolerance'],
    'storage-systems': ['storage systems', 'file system', 'io stack', 'data persistence'],
    'cloud-systems': ['cloud computing', 'multi-tenant systems', 'service infrastructure', 'resource scheduling'],
    'network-systems': ['network systems', 'datacenter network', 'congestion control', 'internet measurement'],
    'systems-software': ['operating systems', 'runtime system', 'kernel', 'virtualization'],
    'programming-languages-and-compilers': ['compiler', 'program analysis', 'runtime optimization', 'code generation'],
    'software-engineering-for-systems': ['software engineering', 'system reliability', 'software maintenance', 'testing and verification'],
    'performance-reliability': ['performance analysis', 'benchmarking', 'reliability engineering', 'latency optimization'],
}


def load_venues():
    with open(VENUES_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)['venues']


def infer_areas(query: str):
    q = query.lower()
    matched = []
    for key, areas in KEYWORD_TO_AREAS.items():
        if key in q:
            matched.extend(areas)
    if not matched:
        return ['distributed-systems', 'systems-software']
    seen = []
    for area in matched:
        if area not in seen:
            seen.append(area)
    return seen


def score_venue(v, areas, query):
    score = 0
    if v['area'] in areas:
        score += 5
    if v['ccf'] == 'A':
        score += 3
    elif v['ccf'] == 'B':
        score += 2
    if v['source_area'] == 'system-core':
        score += 2
    q = query.lower()
    name_blob = f"{v['short_name']} {v['full_name']} {v['area']} {v['source_area']}".lower()
    for token in q.split():
        if len(token) >= 3 and token in name_blob:
            score += 1
    return score


def build_queries(topic, selected_areas):
    phrases = []
    for area in selected_areas:
        phrases.extend(AREA_TO_QUERY_TERMS.get(area, []))
    ordered = []
    for p in [topic] + phrases:
        if p and p not in ordered:
            ordered.append(p)
    return ordered[:8]


def group_by_area(venues):
    grouped = defaultdict(list)
    for v in venues:
        grouped[v['area']].append(v)
    return dict(grouped)


def main():
    parser = argparse.ArgumentParser(description='Build paper query config for system-related venues')
    parser.add_argument('--topic', required=True, help='research topic or natural language query')
    parser.add_argument('--top-k', type=int, default=15, help='number of venues to keep')
    parser.add_argument('--format', choices=['json', 'markdown'], default='json')
    args = parser.parse_args()

    venues = load_venues()
    areas = infer_areas(args.topic)
    ranked = sorted(venues, key=lambda v: score_venue(v, areas, args.topic), reverse=True)
    selected = ranked[:args.top_k]
    search_phrases = build_queries(args.topic, areas)

    output = {
        'topic': args.topic,
        'selected_areas': areas,
        'search_phrases': search_phrases,
        'venues': selected,
        'grouped_venues': group_by_area(selected),
        'usage': {
            'notes': [
                '优先访问 venues 中的 link 作为 DBLP 检索入口',
                '可将 topic 与 search_phrases 组合，再结合 venue 名称进行站内或外部检索',
                '如果需要更全结果，可提高 --top-k 或直接遍历 data/venues.json'
            ]
        }
    }

    if args.format == 'json':
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        print(f"# Query config for: {args.topic}\n")
        print('## Selected areas')
        for area in areas:
            print(f'- {area}')
        print('\n## Search phrases')
        for phrase in search_phrases:
            print(f'- {phrase}')
        print('\n## Venues')
        print('| type | ccf | area | short_name | full_name | link |')
        print('|---|---|---|---|---|---|')
        for v in selected:
            print(f"| {v['type']} | {v['ccf']} | {v['area']} | {v['short_name']} | {v['full_name']} | {v['link']} |")


if __name__ == '__main__':
    main()
