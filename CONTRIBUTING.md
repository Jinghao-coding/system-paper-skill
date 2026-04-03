# Contributing

Thanks for contributing to `system-paper-skill`.

## Scope

This repository provides a bilingual systems-paper discovery skill plus reusable scripts for:

- venue recommendation
- retrieval workflow generation
- candidate paper fetching and reranking
- citation and BibTeX enrichment

## Development workflow

1. Keep changes modular and script-friendly.
2. Prefer deterministic logic over hidden heuristics where possible.
3. Preserve bilingual support for both Chinese and English prompts.
4. Keep output formats stable for both human-facing Markdown and agent-facing JSON.
5. When changing routing or ranking logic, add or update eval cases.

## Pull request checklist

- explain the user problem being solved
- describe any ranking or routing trade-offs
- update `README.md` and `SKILL.md` if behavior changes
- update `evals.json` for new scenarios
- run smoke tests for both Chinese and English queries

## Suggested local checks

```bash
python3 scripts/build_query_config.py --topic "AI infra serving observability" --top-k 8 --format json
python3 scripts/build_query_config.py --topic "分布式系统 容错 期刊 综述" --top-k 8 --type journal --format json
python3 scripts/search_papers.py --topic "cloud native orchestration and container isolation" --top-k 5 --per-venue-limit 1 --output json
```
