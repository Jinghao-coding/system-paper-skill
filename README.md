# system-paper-skill

A bilingual skill and script toolkit for **systems / infrastructure paper discovery**, venue recommendation, and retrieval workflow generation.

## Directory layout

- `SKILL.md`: skill instructions and usage policy
- `README.md`: quickstart, workflow notes, and open-source guidance
- `data/venues.json`: curated venue dataset
- `scripts/build_query_config.py`: infer areas, build venue ranking, expand search phrases
- `scripts/build_query_urls.py`: generate global and per-venue retrieval URLs
- `scripts/fetch_papers.py`: retrieve and rerank candidate papers from multiple sources
- `scripts/format_citation.py`: format citations
- `scripts/get_bibtex.py`: enrich papers with BibTeX
- `scripts/verify_bibtex.py`: verify BibTeX/citation entries against real papers via DOI or title metadata lookup
- `scripts/search_papers.py`: unified workflow entry point
- `scripts/search_papers.sh`: shell wrapper for non-Python callers

## What changed in round 2

### 1. Better bilingual topic routing
- expanded English and Chinese keyword coverage for AI infra, model serving, inference, observability, cloud native, Kubernetes, containers, orchestration, and reliability
- added venue hints so explicit venue names can help infer areas
- added query rewrites for common system topics such as `ai infra`, `llm serving`, `cloud native`, and `system reliability`

### 2. Stronger venue ranking
- improved area scoring and venue-type preference handling
- preserved system-core A/B coverage while supporting `balanced`, `conference`, and `journal` preference modes
- improved support for “top conference only” and “journal-first survey” requests

### 3. Better retrieval quality
- upgraded `fetch_papers.py` from simple source fallback to a more explicit reranking pipeline
- added venue canonicalization to reduce false mismatches caused by different venue names
- reranking now considers venue match, topic overlap, source quality, recency, and citation signal
- source order is now `DBLP > OpenAlex > Crossref > Semantic Scholar` for cleaner venue alignment

### 4. Better citation and BibTeX outputs
- citation formatting prefers DOI where possible
- BibTeX output includes provenance via `bibtex_source`
- text cleanup removes common HTML and whitespace noise from source metadata
- added external metadata verification so BibTeX/citation entries can be checked against real papers via DOI or title lookup

### 5. Better open-source readiness
- `SKILL.md` is now written in open-source-friendly English
- documentation is more explicit about workflow, outputs, and modular structure
- scripts are organized so users can run the pieces independently or use the end-to-end entry point

## Data principles

1. Keep full A/B coverage for core systems areas whenever practical
2. Keep useful B venues for system work rather than over-pruning to only A venues
3. For adjacent network / PL / software engineering areas, keep venues that are still strongly useful for systems and infra topics
4. Prefer DBLP venue links as stable entry points

## Quickstart

### 1. Build venue recommendations

```bash
python3 scripts/build_query_config.py --topic "distributed training scheduler" --top-k 12 --format json
```

### 2. Force journal-first or conference-first ranking

```bash
python3 scripts/build_query_config.py --topic "system reliability survey" --top-k 12 --type journal --format json
python3 scripts/build_query_config.py --topic "container orchestration for systems research" --top-k 12 --type conference --format markdown
```

### 3. Generate retrieval URLs

```bash
python3 scripts/build_query_urls.py --topic "distributed training scheduler" --limit 12 --format json
```

### 4. Fetch and rerank candidate papers

```bash
python3 scripts/fetch_papers.py --topic "AI infra serving observability" --top-k 10 --per-venue-limit 2 --format json
```

### 5. Run the full workflow

```bash
python3 scripts/search_papers.py --topic "AI infra serving observability" --top-k 10 --per-venue-limit 2 --output json
```

### 6. Shell entry for non-Python callers

```bash
bash scripts/search_papers.sh --topic "数据中心网络 拥塞控制" --top-k 10 --output markdown
```

## Main outputs

### `build_query_config.py`
Returns:
- `selected_areas`
- `preferred_type`
- `search_phrases`
- `venues`
- `grouped_venues`

### `build_query_urls.py`
Returns:
- `global_queries`
- `per_venue_queries`

### `fetch_papers.py`
Returns:
- `selected_areas`
- `preferred_type`
- `venues`
- `papers`
- `debug`

### `search_papers.py`
Returns:
- `selected_areas`
- `preferred_type`
- `search_phrases`
- `venues`
- `query_urls`
- `per_venue_queries`
- `papers`
- `citation_style`
- `workflow`
- `papers[].verification` with existence check, verification method, and matched metadata

## Suggested usage pattern

1. start with `build_query_config.py` when you need venue routing only
2. add `build_query_urls.py` when you want retrieval entry points
3. use `search_papers.py` when you want a complete retrieval package
4. if the fetched papers look semantically weak, present the workflow and venue shortlist rather than overselling noisy candidates

## Open-source packaging suggestions

If you plan to open-source this project, consider adding the following next:

- a top-level `LICENSE`
- a concise `CONTRIBUTING.md`
- a `requirements.txt` or `pyproject.toml` for dependency clarity
- a small `tests/` directory for deterministic checks on routing and ranking
- GitHub Actions or another CI workflow for linting and basic smoke tests

## Example topics

```bash
python3 scripts/search_papers.py --topic "AI infra serving observability" --top-k 10 --output json
python3 scripts/search_papers.py --topic "我在做系统可靠性综述，优先期刊" --top-k 12 --type journal --output markdown
python3 scripts/search_papers.py --topic "cloud native orchestration and container isolation" --top-k 10 --type conference --output json
```
