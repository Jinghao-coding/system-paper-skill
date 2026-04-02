# system-paper-skill

一个面向 **system infra 方向论文检索** 的 skills 数据与脚本集合。

## 目录

- `SKILL.md`：技能说明与使用规则
- `README.md`：快速上手与交付说明
- `data/venues.json`：结构化 venue 数据源
- `scripts/build_query_config.py`：根据 topic 生成 venue 推荐与检索配置
- `scripts/build_query_urls.py`：根据 topic + venues 生成各论文站点查询入口
- `scripts/search_papers.py`：统一入口，输出 agent 可直接消费的检索工作流
- `scripts/search_papers.sh`：给非 Python 调用方的 shell 入口

## 数据原则

1. **system-core（计算机体系结构 / 并行与分布计算 / 存储系统）A/B 全量保留**
2. **system 的 B 会和 B 刊必须保留**
3. network 与 softeng-pl 保留和 system infra 紧相关的 A/B venue
4. 链接优先使用 DBLP venue 页，便于后续展开检索

## 快速开始

### 1. 生成 query config

```bash
python3 scripts/build_query_config.py --topic "distributed training scheduler" --top-k 12 --format json
```

### 2. 生成查询 URL

```bash
python3 scripts/build_query_urls.py --topic "distributed training scheduler" --limit 12 --format json
```

### 3. 一步输出完整检索工作流

```bash
python3 scripts/search_papers.py --topic "distributed training scheduler" --top-k 12 --output json
```

### 4. Shell 入口（非 Python 调用方）

```bash
bash scripts/search_papers.sh --topic "distributed training scheduler" --top-k 12 --output json
```

## 输出说明

### build_query_config.py
输出：
- `selected_areas`
- `search_phrases`
- `venues`
- `grouped_venues`

### build_query_urls.py
输出：
- `global_queries`
- `per_venue_queries`

支持的查询目标：
- DBLP
- Google Scholar
- Semantic Scholar
- OpenAlex

### search_papers.py
输出：
- `selected_areas`
- `search_phrases`
- `venues`
- `query_urls`
- `per_venue_queries`
- `workflow`

## 推荐 agent 工作流

1. 调用 `search_papers.py` 获取推荐 venues 和查询入口
2. 优先访问 `per_venue_queries[].venue_link` 或 `dblp_search_url`
3. 如果 DBLP 结果不足，再用 Semantic Scholar / OpenAlex 扩展
4. 对候选论文按 relevance、年份、引用、系统相关性做二次筛选

## 示例

```bash
python3 scripts/search_papers.py --topic "数据中心网络 拥塞控制" --top-k 10 --output markdown
python3 scripts/search_papers.py --topic "kernel runtime compiler optimization" --top-k 15 --output json
```
