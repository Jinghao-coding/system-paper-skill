#!/usr/bin/env python3
import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

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
    'distribution': ['distributed-systems', 'cloud-systems'],
    'cloud': ['cloud-systems', 'distributed-systems'],
    'cloud native': ['cloud-systems', 'systems-software', 'distributed-systems'],
    'microservice': ['cloud-systems', 'distributed-systems'],
    'microservices': ['cloud-systems', 'distributed-systems'],
    'storage': ['storage-systems'],
    'file system': ['storage-systems', 'systems-software'],
    'filesystem': ['storage-systems', 'systems-software'],
    'network': ['network-systems'],
    'networking': ['network-systems'],
    'datacenter network': ['network-systems', 'distributed-systems'],
    'data center network': ['network-systems', 'distributed-systems'],
    'internet measurement': ['network-systems', 'performance-reliability'],
    'congestion': ['network-systems'],
    'rpc': ['distributed-systems', 'cloud-systems'],
    'scheduler': ['distributed-systems', 'systems-software', 'cloud-systems'],
    'scheduling': ['distributed-systems', 'systems-software', 'cloud-systems'],
    'resource isolation': ['distributed-systems', 'systems-software'],
    'resource management': ['distributed-systems', 'cloud-systems'],
    'multi-tenant': ['cloud-systems', 'distributed-systems'],
    'multitenant': ['cloud-systems', 'distributed-systems'],
    'reliability': ['performance-reliability', 'software-engineering-for-systems'],
    'resilience': ['performance-reliability', 'software-engineering-for-systems'],
    'availability': ['performance-reliability', 'software-engineering-for-systems'],
    'performance': ['performance-reliability', 'computer-architecture', 'distributed-systems'],
    'benchmark': ['performance-reliability'],
    'middleware': ['distributed-systems', 'cloud-systems'],
    'verification': ['software-engineering-for-systems', 'programming-languages-and-compilers'],
    'testing': ['software-engineering-for-systems', 'performance-reliability'],
    'program analysis': ['programming-languages-and-compilers', 'software-engineering-for-systems'],
    'gpu': ['computer-architecture', 'programming-languages-and-compilers', 'cloud-systems'],
    'accelerator': ['computer-architecture'],
    'serving': ['cloud-systems', 'distributed-systems', 'performance-reliability'],
    'serving stack': ['cloud-systems', 'distributed-systems', 'performance-reliability'],
    'online serving': ['cloud-systems', 'distributed-systems', 'performance-reliability'],
    'model serving': ['cloud-systems', 'distributed-systems', 'performance-reliability'],
    'inference': ['cloud-systems', 'distributed-systems', 'performance-reliability'],
    'llm inference': ['cloud-systems', 'distributed-systems', 'performance-reliability'],
    'llm serving': ['cloud-systems', 'distributed-systems', 'performance-reliability'],
    'training': ['distributed-systems', 'cloud-systems'],
    'distributed training': ['distributed-systems', 'cloud-systems'],
    'parameter server': ['distributed-systems', 'cloud-systems'],
    'elasticity': ['cloud-systems', 'distributed-systems'],
    'autoscaling': ['cloud-systems', 'distributed-systems'],
    'auto scaling': ['cloud-systems', 'distributed-systems'],
    'straggler': ['distributed-systems', 'performance-reliability'],
    'observability': ['performance-reliability', 'software-engineering-for-systems', 'cloud-systems'],
    'telemetry': ['performance-reliability', 'software-engineering-for-systems', 'cloud-systems'],
    'monitoring': ['performance-reliability', 'software-engineering-for-systems', 'cloud-systems'],
    'logging': ['performance-reliability', 'software-engineering-for-systems', 'cloud-systems'],
    'tracing': ['performance-reliability', 'software-engineering-for-systems', 'cloud-systems'],
    'tail latency': ['performance-reliability', 'distributed-systems'],
    'throughput': ['performance-reliability', 'distributed-systems'],
    'latency': ['performance-reliability', 'distributed-systems'],
    'container': ['systems-software', 'cloud-systems'],
    'containers': ['systems-software', 'cloud-systems'],
    'container orchestration': ['cloud-systems', 'systems-software', 'distributed-systems'],
    'kubernetes': ['cloud-systems', 'systems-software', 'distributed-systems'],
    'orchestration': ['cloud-systems', 'distributed-systems', 'systems-software'],
    'virtualization': ['systems-software', 'cloud-systems'],
    'virtual machine': ['systems-software', 'cloud-systems'],
    'vm': ['systems-software', 'cloud-systems'],
    'ai infra': ['distributed-systems', 'cloud-systems', 'performance-reliability'],
    'ml systems': ['distributed-systems', 'cloud-systems', 'computer-architecture'],
    'infra': ['distributed-systems', 'systems-software', 'cloud-systems'],
    '微架构': ['computer-architecture'],
    '体系结构': ['computer-architecture'],
    '分布式': ['distributed-systems', 'cloud-systems'],
    '云': ['cloud-systems', 'distributed-systems'],
    '云原生': ['cloud-systems', 'systems-software', 'distributed-systems'],
    '微服务': ['cloud-systems', 'distributed-systems'],
    '存储': ['storage-systems'],
    '文件系统': ['storage-systems', 'systems-software'],
    '网络': ['network-systems'],
    '拥塞控制': ['network-systems'],
    '互联网测量': ['network-systems', 'performance-reliability'],
    '调度': ['distributed-systems', 'systems-software', 'cloud-systems'],
    '资源隔离': ['distributed-systems', 'systems-software'],
    '资源管理': ['distributed-systems', 'cloud-systems'],
    '可靠性': ['performance-reliability', 'software-engineering-for-systems'],
    '韧性': ['performance-reliability', 'software-engineering-for-systems'],
    '系统软件': ['systems-software'],
    '操作系统': ['systems-software'],
    '编译器': ['programming-languages-and-compilers', 'computer-architecture'],
    '程序分析': ['programming-languages-and-compilers', 'software-engineering-for-systems'],
    '中间件': ['distributed-systems', 'cloud-systems'],
    '服务计算': ['cloud-systems'],
    '推理': ['cloud-systems', 'distributed-systems', 'performance-reliability'],
    '训练': ['distributed-systems', 'cloud-systems'],
    '参数服务器': ['distributed-systems', 'cloud-systems'],
    '弹性': ['cloud-systems', 'distributed-systems'],
    '自动扩缩容': ['cloud-systems', 'distributed-systems'],
    '拖尾': ['distributed-systems', 'performance-reliability'],
    '长尾延迟': ['performance-reliability', 'distributed-systems'],
    '可观测性': ['performance-reliability', 'software-engineering-for-systems', 'cloud-systems'],
    '遥测': ['performance-reliability', 'software-engineering-for-systems', 'cloud-systems'],
    '监控': ['performance-reliability', 'software-engineering-for-systems', 'cloud-systems'],
    '链路追踪': ['performance-reliability', 'software-engineering-for-systems', 'cloud-systems'],
    '日志': ['performance-reliability', 'software-engineering-for-systems', 'cloud-systems'],
    '容器': ['systems-software', 'cloud-systems'],
    '编排': ['cloud-systems', 'distributed-systems', 'systems-software'],
    '虚拟化': ['systems-software', 'cloud-systems']
}

AREA_TO_QUERY_TERMS = {
    'computer-architecture': ['computer architecture', 'microarchitecture', 'accelerator', 'compiler optimization'],
    'distributed-systems': ['distributed systems', 'cluster scheduling', 'resource management', 'fault tolerance'],
    'storage-systems': ['storage systems', 'file system', 'io stack', 'data persistence'],
    'cloud-systems': ['cloud computing', 'cloud native systems', 'service infrastructure', 'resource scheduling'],
    'network-systems': ['network systems', 'datacenter network', 'congestion control', 'internet measurement'],
    'systems-software': ['operating systems', 'runtime system', 'kernel', 'virtualization'],
    'programming-languages-and-compilers': ['compiler', 'program analysis', 'runtime optimization', 'code generation'],
    'software-engineering-for-systems': ['software engineering', 'system reliability', 'software maintenance', 'testing and verification'],
    'performance-reliability': ['performance analysis', 'benchmarking', 'reliability engineering', 'latency optimization'],
}

VENUE_HINTS = {
    'osdi': ['distributed-systems', 'systems-software'],
    'sosp': ['distributed-systems', 'systems-software'],
    'eurosys': ['distributed-systems', 'systems-software', 'cloud-systems'],
    'nsdi': ['network-systems', 'distributed-systems'],
    'socc': ['cloud-systems', 'distributed-systems'],
    'fast': ['storage-systems', 'systems-software'],
    'sigcomm': ['network-systems'],
    'conext': ['network-systems'],
    'imc': ['network-systems', 'performance-reliability'],
    'asplos': ['computer-architecture', 'systems-software', 'programming-languages-and-compilers'],
    'pldi': ['programming-languages-and-compilers'],
    'popl': ['programming-languages-and-compilers'],
    'cgo': ['programming-languages-and-compilers', 'computer-architecture'],
    'pact': ['computer-architecture', 'programming-languages-and-compilers'],
    'atc': ['systems-software', 'distributed-systems'],
    'usenix atc': ['systems-software', 'distributed-systems'],
    'middleware': ['distributed-systems', 'cloud-systems'],
    'hotos': ['systems-software', 'distributed-systems'],
    'isca': ['computer-architecture'],
    'micro': ['computer-architecture'],
    'hpca': ['computer-architecture'],
    'ton': ['network-systems'],
    'tpds': ['distributed-systems'],
    'toplas': ['programming-languages-and-compilers'],
}

QUERY_REWRITES = {
    'ai infra': ['ml systems', 'distributed training', 'serving systems'],
    'llm serving': ['model serving', 'online serving', 'latency optimization'],
    'inference infra': ['model serving', 'resource management', 'latency optimization'],
    'observability': ['monitoring', 'tracing', 'telemetry'],
    'cloud native': ['container orchestration', 'microservices', 'kubernetes'],
    'system reliability': ['fault tolerance', 'reliability engineering', 'software reliability'],
}


def load_venues():
    with open(VENUES_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)['venues']


def normalize_query(query: str) -> str:
    q = query.lower().strip()
    q = re.sub(r'[_\-/]+', ' ', q)
    q = re.sub(r'\s+', ' ', q)
    return q


def unique_keep_order(items):
    seen = set()
    out = []
    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


def infer_areas(query: str):
    q = normalize_query(query)
    matched = []
    for key, areas in KEYWORD_TO_AREAS.items():
        if key in q:
            matched.extend(areas)
    for key, areas in VENUE_HINTS.items():
        if key in q:
            matched.extend(areas)
    if not matched:
        return ['distributed-systems', 'systems-software']
    return unique_keep_order(matched)


def detect_prefer_type(query: str) -> str:
    q = normalize_query(query)
    journal_terms = ['journal', 'journals', 'survey', 'review paper', '期刊', '综述', '综述论文']
    conf_terms = ['conference', 'conferences', 'top conference', '顶会', '会议']
    has_journal = any(t in q for t in journal_terms)
    has_conf = any(t in q for t in conf_terms)
    if has_journal and not has_conf:
        return 'journal'
    if has_conf and not has_journal:
        return 'conference'
    return 'balanced'


def build_queries(topic, selected_areas):
    q = normalize_query(topic)
    phrases = []
    for key, rewrites in QUERY_REWRITES.items():
        if key in q:
            phrases.extend(rewrites)
    for area in selected_areas:
        phrases.extend(AREA_TO_QUERY_TERMS.get(area, []))
    ordered = []
    for p in [topic] + phrases:
        if p and p not in ordered:
            ordered.append(p)
    return ordered[:12]


def score_venue(v, areas, query, prefer_type='balanced'):
    score = 0
    q = normalize_query(query)
    if v['area'] in areas:
        score += 6
    if v['ccf'] == 'A':
        score += 3
    elif v['ccf'] == 'B':
        score += 2
    if v['source_area'] == 'system-core':
        score += 2
    name_blob = f"{v['short_name']} {v['full_name']} {v['area']} {v['source_area']}".lower()
    for token in q.split():
        if len(token) >= 3 and token in name_blob:
            score += 1
    if prefer_type == 'conference' and v['type'] == 'conference':
        score += 3
    elif prefer_type == 'journal' and v['type'] == 'journal':
        score += 3
    if any(t in q for t in ['survey', 'review', 'review paper', '综述', '期刊']) and v['type'] == 'journal':
        score += 2
    if any(t in q for t in ['conference', 'top conference', '顶会', '会议']) and v['type'] == 'conference':
        score += 2
    return score


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
    parser.add_argument('--type', choices=['balanced', 'conference', 'journal'], default=None, help='optional preferred venue type')
    args = parser.parse_args()

    venues = load_venues()
    areas = infer_areas(args.topic)
    prefer_type = args.type or detect_prefer_type(args.topic)
    ranked = sorted(venues, key=lambda v: score_venue(v, areas, args.topic, prefer_type=prefer_type), reverse=True)
    selected = ranked[:args.top_k]
    search_phrases = build_queries(args.topic, areas)

    output = {
        'topic': args.topic,
        'selected_areas': areas,
        'preferred_type': prefer_type,
        'search_phrases': search_phrases,
        'venues': selected,
        'grouped_venues': group_by_area(selected),
        'usage': {
            'notes': [
                'Prefer the venue link as the DBLP entry point for paper expansion.',
                'Combine topic, search_phrases, and venue name for broader retrieval.',
                'Increase --top-k or traverse data/venues.json for higher recall.',
                'Use --type journal or --type conference when the user has a clear venue preference.'
            ]
        }
    }

    if args.format == 'json':
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        print(f'# Query config for: {args.topic}\n')
        print(f'- preferred_type: {prefer_type}')
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
