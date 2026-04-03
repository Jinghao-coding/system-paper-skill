---
name: system-paper-skill
description: Bilingual skill for system and infrastructure paper discovery, venue recommendation, and retrieval workflow generation. Use this skill whenever the user asks for system/infra/ml-systems/network-systems related papers, wants recommended conferences or journals, asks for venue-based search entry points, needs a paper search workflow, or wants an agent-consumable venue list or JSON/YAML dataset. Trigger for both Chinese and English requests mentioning operating systems, distributed systems, cloud systems, storage, networks, systems software, reliability, observability, compilers/runtime, AI infra, model serving, inference, Kubernetes, OSDI, SOSP, NSDI, ASPLOS, EuroSys, FAST, SIGCOMM, TPDS, TOPLAS, and similar venue or topic cues.
---

# System Paper Skill

## Purpose

Use this skill to build a reliable retrieval workflow for **system and infrastructure papers**. The skill is designed for both direct user-facing answers and downstream agent/tool chains.

The skill helps with four recurring jobs:

1. map a user topic to one or more system-related subareas
2. recommend tightly related A/B venues
3. generate retrieval entry points for DBLP / Scholar / Semantic Scholar / OpenAlex
4. fetch and rerank candidate papers with citations and BibTeX

## Supported scenarios

Use this skill when the user asks for any of the following in **Chinese or English**:

- papers on operating systems, distributed systems, cloud systems, storage, system software, compilers/runtime, network systems, observability, performance, or reliability
- recommended conferences or journals for a systems topic
- a venue whitelist or venue dataset for an agent or workflow
- venue-based retrieval entry points
- a structured paper search workflow for system / infra / AI infra / ML systems
- conference-only or journal-only recommendations

Typical trigger phrases include:

- “find system papers about …”
- “推荐 system 方向会议和期刊”
- “AI infra / serving / inference / observability papers”
- “only top systems conferences”
- “journal-first systems survey venues”
- “整理成 JSON 数据源”

## Core design principles

### 1. Route first, retrieve second

Do not jump straight to a generic web search. First infer the most likely subareas, then rank venues, then construct retrieval entry points. This improves relevance and makes the result easier to audit.

### 2. Keep venue recommendations tight

Prefer the curated A/B venue whitelist bundled with the skill. The point is not to return every adjacent venue, but to give the user a strong starting set for system-focused retrieval.

### 3. Preserve system B venues

For system-core topics, keep useful B conferences and journals instead of collapsing everything into a tiny A-only list. In practice, many system subtopics need this coverage.

### 4. Respect venue-type preference

If the user clearly prefers journals, surveys, or review-style reading, bias toward journals. If the user explicitly asks for conferences, top venues, or top systems conferences, bias toward conferences.

### 5. Support bilingual usage

The skill should work for both English and Chinese prompts, including mixed-language topic descriptions.

## Area taxonomy

Map the user request into one or more of these areas:

- `computer-architecture`
- `distributed-systems`
- `storage-systems`
- `cloud-systems`
- `network-systems`
- `systems-software`
- `programming-languages-and-compilers`
- `software-engineering-for-systems`
- `performance-reliability`

## Output strategy

### For user-facing answers

Prefer a Markdown table such as:

| type | ccf | area | short_name | full_name | link |
|---|---|---|---|---|---|

### For agent-facing outputs

Prefer JSON or YAML. Include fields that are stable and easy to reuse downstream.

Recommended minimal JSON shape:

```json
{
  "topic": "distributed training scheduler",
  "selected_areas": ["distributed-systems", "cloud-systems"],
  "preferred_type": "balanced",
  "venues": [
    {
      "type": "conference",
      "ccf": "A",
      "area": "distributed-systems",
      "short_name": "OSDI",
      "full_name": "USENIX Symposium on Operating Systems Design and Implementation",
      "link": "http://dblp.uni-trier.de/db/conf/osdi/"
    }
  ]
}
```

## Working method

### Step 1: infer areas and venue preference

Use topic terms, bilingual keywords, and venue hints to infer areas. If the user signals “journal / survey / 期刊 / 综述”, prefer journals. If they signal “conference / 顶会 / 会议”, prefer conferences.

### Step 2: rank venues from the bundled whitelist

Use the curated venue list in `data/venues.json`. Keep recommendations tightly scoped to the inferred areas.

### Step 3: generate retrieval entry points

Construct global and per-venue entry points using:

- DBLP
- Google Scholar
- Semantic Scholar
- OpenAlex

DBLP is usually the cleanest starting point for venue-oriented retrieval.

### Step 4: fetch and rerank papers when needed

If the task is not just venue recommendation but actual paper retrieval, use the retrieval scripts to fetch candidate papers and rerank them using:

- venue match
- topic overlap
- source quality
- recency
- citation signal

### Step 5: verify references when BibTeX or citations are returned

If the workflow returns BibTeX or formatted citations, also verify whether the referenced paper appears to exist in external metadata.

Prefer DOI-based verification first. If no DOI is available, fall back to title-based lookup. Surface verification status explicitly instead of silently assuming the reference is valid.

### Step 6: return a structured workflow

When the user wants something actionable, include:

- selected areas
- ranked venues
- search phrases
- query URLs
- candidate papers if fetched
- citations / BibTeX if available

## Bundled resources

### `data/venues.json`

Structured venue inventory. This is the main curated dataset and should be treated as the source of truth for venue records.

Fields include:

- `type`
- `ccf`
- `source_area`
- `area`
- `short_name`
- `full_name`
- `link`

### `scripts/build_query_config.py`

Builds a venue recommendation configuration from a topic.

Useful when you need:

- area inference
- venue ranking
- search phrase expansion
- conference/journal preference handling

### `scripts/build_query_urls.py`

Builds global and per-venue retrieval URLs.

### `scripts/fetch_papers.py`

Fetches candidate papers from multiple sources and reranks them.

Current source order:

1. DBLP
2. OpenAlex
3. Crossref
4. Semantic Scholar

The script prefers cleaner venue metadata first, then broadens recall.

### `scripts/format_citation.py`

Formats citation strings in IEEE / APA / plain styles.

### `scripts/get_bibtex.py`

Enriches papers with BibTeX, preferring DOI / DBLP data when available and falling back to local generation.

### `scripts/verify_bibtex.py`

Validates whether generated or fetched BibTeX / citation records correspond to real papers.

Use DOI-first verification when a DOI is present. Otherwise use title-based metadata lookup. Surface whether the reference appears to exist, how it was verified, and which external metadata record matched best.

### `scripts/search_papers.py`

Unified entry point for the end-to-end workflow.

Use this when the user wants the full package rather than a single step.

## Practical guidance

### If the user wants venue recommendation only

Run `build_query_config.py` and respond with venues plus search phrases.

### If the user wants retrieval entry points

Run `build_query_config.py` and `build_query_urls.py`.

### If the user wants actual candidate papers

Run `search_papers.py`, or run `fetch_papers.py` plus citation/BibTeX enrichment.

### If results look semantically weak

Prefer explaining the limitation and giving the retrieval workflow, rather than pretending the current candidate list is authoritative.

## Open-source readiness notes

This skill is suitable for open source because:

- the core logic is deterministic and script-based
- the venue data is explicit and inspectable
- the workflow is modular and reusable
- the output supports both human and machine consumers

When preparing an open-source release, keep documentation bilingual where practical, avoid product-specific assumptions, and make scripts executable in a standard Python 3 environment.
