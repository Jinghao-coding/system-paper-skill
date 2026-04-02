---
name: system-paper-skill
description: 面向 system infra 相关论文检索与候选 venue 映射的技能。用户提到 system、infra、分布式系统、存储、云计算、体系结构、操作系统、网络系统、系统软件、程序设计语言、middleware、NSDI、OSDI、SOSP、ASPLOS、EuroSys、FAST、SIGCOMM、CoNEXT、TON、TPDS、TOPLAS 等，或要求“找相关论文/推荐会议期刊/按 venue 查询论文/整理 system 方向检索入口”时，务必优先使用本技能。该技能负责维护一份紧相关的会议与期刊白名单及对应查询链接，先将用户问题映射到合适的 system 相关子领域与 venue，再基于附带链接进行论文检索建议或后续自动化检索。
---

# System Paper Skill

## 目标

为 agent 提供一份 **system infra 紧相关** 的会议与期刊知识清单，包含：

1. venue 简称
2. venue 全称
3. CCF 类别（A/B）
4. venue 类型（conference / journal）
5. 子领域
6. 查询链接（优先 DBLP）

该技能适用于：
- 将用户问题路由到合适的 system 相关 venue
- 为后续论文检索 agent 提供白名单入口
- 快速回答“这个方向值得看哪些会/刊”
- 构造 system 方向论文搜索清单

## 使用原则

### 1. 先做领域归类
先把用户需求归到下面一个或多个子领域：
- computer-architecture
- distributed-systems
- storage-systems
- cloud-systems
- network-systems
- systems-software
- programming-languages-and-compilers
- software-engineering-for-systems
- performance-reliability

### 2. 只返回紧相关 venues
默认返回下面白名单中的 **A/B 类 venue**，其中 **系统方向的 B 会和 B 刊必须保留**，不能因为“精简”而省略。
如果用户明确要求扩展，再补充 C 类或更弱相关 venues。

### 3. 输出格式
默认优先输出表格，字段如下：

| type | ccf | area | short_name | full_name | link |
|---|---|---|---|---|---|

如用户要“做成检索配置/skills 数据源”，则优先输出 JSON 或 YAML。

## 推荐输出模板

### 面向用户展示

| type | ccf | area | short_name | full_name | link |
|---|---|---|---|---|---|
| conference | A | distributed-systems | OSDI | USENIX Symposium on Operating Systems Design and Implementation | http://dblp.uni-trier.de/db/conf/osdi/ |

### 面向 agent / 配置输出

```json
{
  "area": "distributed-systems",
  "venues": [
    {
      "type": "conference",
      "ccf": "A",
      "short_name": "OSDI",
      "full_name": "USENIX Symposium on Operating Systems Design and Implementation",
      "link": "http://dblp.uni-trier.de/db/conf/osdi/"
    }
  ]
}
```

## Bundled resources

### data/venues.json
- 结构化 venue 数据源。
- 适合 agent 直接读取。
- 包含 `type`、`ccf`、`source_area`、`area`、`short_name`、`full_name`、`link`。
- **system-core 默认完整保留 A/B 会刊。**

### scripts/build_query_config.py
用于根据用户主题自动生成检索配置。

示例：

```bash
python3 scripts/build_query_config.py --topic "distributed training scheduler" --top-k 12 --format json
python3 scripts/build_query_config.py --topic "数据中心网络 拥塞控制" --top-k 10 --format markdown
```

输出包括：
- selected_areas
- search_phrases
- venues
- grouped_venues

### scripts/build_query_urls.py
用于为 topic 和 venues 生成可直接访问的论文查询网址。

示例：

```bash
python3 scripts/build_query_urls.py --topic "distributed training scheduler" --limit 10 --format json
```

输出包括：
- 全局检索入口：DBLP / Google Scholar / Semantic Scholar / OpenAlex
- 每个 venue 的 venue_link、dblp_search_url、semantic_scholar_url、openalex_url

### scripts/search_papers.py
统一入口脚本。组合 `build_query_config.py` 和 `build_query_urls.py`，直接输出 agent 可消费的论文查询工作流。

示例：

```bash
python3 scripts/search_papers.py --topic "distributed training scheduler" --top-k 12 --output json
python3 scripts/search_papers.py --topic "数据中心网络 拥塞控制" --top-k 10 --output markdown
```

输出包括：
- selected_areas
- search_phrases
- venues
- query_urls
- per_venue_queries
- workflow

### scripts/search_papers.sh
给非 Python 调用方使用的直接入口。内部转调 `search_papers.py`。

示例：

```bash
bash scripts/search_papers.sh --topic "distributed training scheduler" --top-k 12 --output json
bash scripts/search_papers.sh --topic "数据中心网络 拥塞控制" --top-k 10 --output markdown
```

如果执行环境不方便设置可执行权限，直接用 `bash scripts/search_papers.sh ...` 即可。

下游 agent 应优先访问 venues 中的 `link` 或 `dblp_search_url`，若结果不足，再使用 Semantic Scholar 和 OpenAlex 扩展查询。

## Venue 白名单

### 1. Core systems / architecture / distributed / storage

#### Journals
| type | ccf | area | short_name | full_name | link |
|---|---|---|---|---|---|
| journal | A | systems-software | TOCS | ACM Transactions on Computer Systems | http://dblp.uni-trier.de/db/journals/tocs/ |
| journal | A | storage-systems | TOS | ACM Transactions on Storage | http://dblp.uni-trier.de/db/journals/tos/ |
| journal | A | programming-languages-and-compilers | TCAD | IEEE Transactions on Computer-Aided Design of Integrated Circuits and Systems | http://dblp.uni-trier.de/db/journals/tcad/ |
| journal | A | computer-architecture | TC | IEEE Transactions on Computers | http://dblp.uni-trier.de/db/journals/tc/index.html |
| journal | A | distributed-systems | TPDS | IEEE Transactions on Parallel and Distributed Systems | http://dblp.uni-trier.de/db/journals/tpds/ |
| journal | A | programming-languages-and-compilers | TACO | ACM Transactions on Architecture and Code Optimization | http://dblp.uni-trier.de/db/journals/taco/ |
| journal | B | cloud-systems | TCC | IEEE Transactions on Cloud Computing | https://dblp.uni-trier.de/db/journals/tcc/ |
| journal | B | distributed-systems | JPDC | Journal of Parallel and Distributed Computing | http://dblp.uni-trier.de/db/journals/jpdc/ |
| journal | B | systems-software | JSA | Journal of Systems Architecture: Embedded Software Design | http://dblp.uni-trier.de/db/journals/jsa/ |
| journal | B | distributed-systems | Parallel Computing | Parallel Computing | https://dblp.org/db/journals/pc/index.html |
| journal | B | performance-reliability | Performance Evaluation | Performance Evaluation: An International Journal | https://dblp.org/db/journals/pe/index.html |
| journal | B | systems-software | TECS | ACM Transactions on Embedded Computing Systems | http://dblp.uni-trier.de/db/journals/tecs/ |
| journal | B | programming-languages-and-compilers | TRETS | ACM Transactions on Reconfigurable Technology and Systems | http://dblp.uni-trier.de/db/journals/trets/ |
| journal | B | computer-architecture | TVLSI | IEEE Transactions on Very Large Scale Integration (VLSI) Systems | http://dblp.uni-trier.de/db/journals/tvlsi/ |

#### Conferences
| type | ccf | area | short_name | full_name | link |
|---|---|---|---|---|---|
| conference | A | distributed-systems | PPoPP | ACM SIGPLAN Symposium on Principles & Practice of Parallel Programming | http://dblp.uni-trier.de/db/conf/ppopp/ |
| conference | A | storage-systems | FAST | USENIX Conference on File and Storage Technologies | http://dblp.uni-trier.de/db/conf/fast/ |
| conference | A | computer-architecture | DAC | Design Automation Conference | https://dblp.uni-trier.de/db/conf/dac/ |
| conference | A | computer-architecture | HPCA | IEEE International Symposium on High Performance Computer Architecture | http://dblp.uni-trier.de/db/conf/hpca/ |
| conference | A | computer-architecture | MICRO | IEEE/ACM International Symposium on Microarchitecture | https://dblp.uni-trier.de/db/conf/micro/index.html |
| conference | A | distributed-systems | SC | International Conference for High Performance Computing, Networking, Storage, and Analysis | http://dblp.uni-trier.de/db/conf/sc/ |
| conference | A | systems-software | ASPLOS | International Conference on Architectural Support for Programming Languages and Operating Systems | http://dblp.uni-trier.de/db/conf/asplos/ |
| conference | A | computer-architecture | ISCA | International Symposium on Computer Architecture | http://dblp.uni-trier.de/db/conf/isca/ |
| conference | A | systems-software | ACM SIGOPS ATC | ACM SIGOPS Annual Technical Conference（原 USENIX ATC） | http://dblp.uni-trier.de/db/conf/usenix/index.html |
| conference | A | distributed-systems | EuroSys | European Conference on Computer Systems | http://dblp.uni-trier.de/db/conf/eurosys/ |
| conference | A | distributed-systems | HPDC | The International ACM Symposium on High-Performance Parallel and Distributed Computing | http://dblp.uni-trier.de/db/conf/hpdc/ |
| conference | B | cloud-systems | SoCC | ACM Symposium on Cloud Computing | http://dblp.uni-trier.de/db/conf/cloud/ |
| conference | B | distributed-systems | SPAA | ACM Symposium on Parallelism in Algorithms and Architectures | http://dblp.uni-trier.de/db/conf/spaa/ |
| conference | B | distributed-systems | PODC | ACM Symposium on Principles of Distributed Computing | http://dblp.uni-trier.de/db/conf/podc/ |
| conference | B | computer-architecture | FPGA | ACM/SIGDA International Symposium on Field-Programmable Gate Arrays | http://dblp.uni-trier.de/db/conf/fpga/ |
| conference | B | programming-languages-and-compilers | CGO | The International Symposium on Code Generation and Optimization | http://dblp.uni-trier.de/db/conf/cgo/ |
| conference | B | computer-architecture | DATE | Design, Automation & Test in Europe | http://dblp.uni-trier.de/db/conf/date/ |
| conference | B | computer-architecture | Hot Chips | Hot Chips: A Symposium on High Performance Chips | https://dblp.org/db/conf/hotchips/index.html |
| conference | B | distributed-systems | CLUSTER | IEEE International Conference on Cluster Computing | https://dblp.uni-trier.de/db/conf/cluster/ |
| conference | B | computer-architecture | ICCD | International Conference on Computer Design | http://dblp.uni-trier.de/db/conf/iccd/ |
| conference | B | computer-architecture | ICCAD | International Conference on Computer-Aided Design | http://dblp.uni-trier.de/db/conf/iccad/ |
| conference | B | distributed-systems | ICDCS | IEEE International Conference on Distributed Computing Systems | http://dblp.uni-trier.de/db/conf/icdcs/ |
| conference | B | programming-languages-and-compilers | CODES+ISSS | International Conference on Hardware/Software Co-design and System Synthesis | https://dblp.uni-trier.de/db/conf/codesisss/index.html |
| conference | B | computer-architecture | HiPEAC | International Conference on High Performance and Embedded Architectures and Compilers | http://dblp.uni-trier.de/db/conf/hipeac/ |
| conference | B | performance-reliability | SIGMETRICS | International Conference on Measurement and Modeling of Computer Systems | http://dblp.uni-trier.de/db/conf/sigmetrics/ |
| conference | B | programming-languages-and-compilers | PACT | International Conference on Parallel Architectures and Compilation Techniques | http://dblp.uni-trier.de/db/conf/IEEEpact/ |
| conference | B | distributed-systems | ICPP | International Conference on Parallel Processing | http://dblp.uni-trier.de/db/conf/icpp/ |
| conference | B | distributed-systems | ICS | International Conference on Supercomputing | http://dblp.uni-trier.de/db/conf/ics/ |
| conference | B | systems-software | VEE | International Conference on Virtual Execution Environments | http://dblp.uni-trier.de/db/conf/vee/ |
| conference | B | distributed-systems | IPDPS | IEEE International Parallel & Distributed Processing Symposium | http://dblp.uni-trier.de/db/conf/ipps/ |
| conference | B | performance-reliability | Performance | International Symposium on Computer Performance, Modeling, Measurements and Evaluation | http://dblp.uni-trier.de/db/conf/performance/ |
| conference | B | systems-software | LISA | Large Installation System Administration Conference | http://dblp.uni-trier.de/db/conf/lisa/ |
| conference | B | storage-systems | MSST | Mass Storage Systems and Technologies | http://dblp.uni-trier.de/db/conf/mss/ |
| conference | B | systems-software | RTAS | IEEE Real-Time and Embedded Technology and Applications Symposium | http://dblp.uni-trier.de/db/conf/rtas/ |
| conference | B | distributed-systems | Euro-Par | European Conference on Parallel and Distributed Computing | http://dblp.uni-trier.de/db/conf/europar/ |

### 2. Network systems

#### Journals
| type | ccf | area | short_name | full_name | link |
|---|---|---|---|---|---|
| journal | A | network-systems | JSAC | IEEE Journal on Selected Areas in Communications | http://dblp.uni-trier.de/db/journals/jsac/ |
| journal | A | network-systems | TMC | IEEE Transactions on Mobile Computing | http://dblp.uni-trier.de/db/journals/tmc/ |
| journal | A | network-systems | TON | IEEE/ACM Transactions on Networking | http://dblp.uni-trier.de/db/journals/ton/ |
| journal | B | network-systems | TOIT | ACM Transactions on Internet Technology | http://dblp.uni-trier.de/db/journals/toit/ |
| journal | B | network-systems | TOSN | ACM Transactions on Sensor Networks | http://dblp.uni-trier.de/db/journals/tosn/ |
| journal | B | network-systems | CN | Computer Networks | http://dblp.uni-trier.de/db/journals/cn/ |
| journal | B | network-systems | TCOM | IEEE Transactions on Communications | http://dblp.uni-trier.de/db/journals/tcom/ |
| journal | B | network-systems | TWC | IEEE Transactions on Wireless Communications | http://dblp.uni-trier.de/db/journals/twc/ |

#### Conferences
| type | ccf | area | short_name | full_name | link |
|---|---|---|---|---|---|
| conference | A | network-systems | SIGCOMM | ACM International Conference on Applications, Technologies, Architectures, and Protocols for Computer Communication | http://dblp.uni-trier.de/db/conf/sigcomm/index.html |
| conference | A | network-systems | MobiCom | ACM International Conference on Mobile Computing and Networking | http://dblp.uni-trier.de/db/conf/mobicom/ |
| conference | A | network-systems | INFOCOM | IEEE International Conference on Computer Communications | http://dblp.uni-trier.de/db/conf/infocom/ |
| conference | A | network-systems | NSDI | Symposium on Network System Design and Implementation | http://dblp.uni-trier.de/db/conf/nsdi/ |
| conference | B | network-systems | CoNEXT | ACM International Conference on Emerging Networking Experiments and Technologies | http://dblp.uni-trier.de/db/conf/conext/ |
| conference | B | network-systems | SenSys | ACM Conference on Embedded Networked Sensor Systems | http://dblp.uni-trier.de/db/conf/sensys/ |
| conference | B | network-systems | SECON | IEEE International Conference on Sensing, Communication, and Networking | http://dblp.uni-trier.de/db/conf/secon/ |
| conference | B | network-systems | IPSN | International Conference on Information Processing in Sensor Networks | http://dblp.uni-trier.de/db/conf/ipsn/ |
| conference | B | network-systems | MobiSys | ACM International Conference on Mobile Systems, Applications, and Services | http://dblp.uni-trier.de/db/conf/mobisys/ |
| conference | B | network-systems | ICNP | IEEE International Conference on Network Protocols | http://dblp.uni-trier.de/db/conf/icnp/ |
| conference | B | network-systems | MobiHoc | Symposium on Theory, Algorithmic Foundations, and Protocol Design for Mobile Networks and Mobile Computing | http://dblp.uni-trier.de/db/conf/mobihoc/ |
| conference | B | network-systems | NOSSDAV | International Workshop on Network and Operating System Support for Digital Audio and Video | http://dblp.uni-trier.de/db/conf/nossdav/ |
| conference | B | network-systems | IWQoS | IEEE/ACM International Workshop on Quality of Service | http://dblp.uni-trier.de/db/conf/iwqos/ |
| conference | B | network-systems | IMC | Internet Measurement Conference | http://dblp.uni-trier.de/db/conf/imc/ |

### 3. Software engineering / system software / PL

#### Journals
| type | ccf | area | short_name | full_name | link |
|---|---|---|---|---|---|
| journal | A | programming-languages-and-compilers | TOPLAS | ACM Transactions on Programming Languages and Systems | http://dblp.uni-trier.de/db/journals/toplas/ |
| journal | A | software-engineering-for-systems | TOSEM | ACM Transactions on Software Engineering and Methodology | http://dblp.uni-trier.de/db/journals/tosem/ |
| journal | A | software-engineering-for-systems | TSE | IEEE Transactions on Software Engineering | http://dblp.uni-trier.de/db/journals/tse/ |
| journal | A | cloud-systems | TSC | IEEE Transactions on Services Computing | http://dblp.uni-trier.de/db/journals/tsc/ |
| journal | B | software-engineering-for-systems | ASE | Automated Software Engineering | http://dblp.uni-trier.de/db/journals/ase/ |
| journal | B | software-engineering-for-systems | ESE | Empirical Software Engineering | http://dblp.uni-trier.de/db/journals/ese/ |
| journal | B | software-engineering-for-systems | IST | Information and Software Technology | http://dblp.uni-trier.de/db/journals/infsof/index.html |
| journal | B | systems-software | JSS | Journal of Systems and Software | http://dblp.uni-trier.de/db/journals/jss/ |
| journal | B | programming-languages-and-compilers | SCP | Science of Computer Programming | http://dblp.uni-trier.de/db/journals/scp/ |
| journal | B | software-engineering-for-systems | SoSyM | Software and Systems Modeling | http://dblp.uni-trier.de/db/journals/sosym/ |
| journal | B | performance-reliability | STVR | Software Testing, Verification and Reliability | http://dblp.uni-trier.de/db/journals/stvr/index.html |
| journal | B | systems-software | SPE | Software: Practice and Experience | http://dblp.uni-trier.de/db/journals/spe/ |

#### Conferences
| type | ccf | area | short_name | full_name | link |
|---|---|---|---|---|---|
| conference | A | programming-languages-and-compilers | PLDI | ACM SIGPLAN Conference on Programming Language Design and Implementation | http://dblp.uni-trier.de/db/conf/pldi/ |
| conference | A | programming-languages-and-compilers | POPL | ACM SIGPLAN-SIGACT Symposium on Principles of Programming Languages | http://dblp.uni-trier.de/db/conf/popl/ |
| conference | A | software-engineering-for-systems | FSE | ACM International Conference on the Foundations of Software Engineering | http://dblp.uni-trier.de/db/conf/sigsoft/ |
| conference | A | systems-software | SOSP | ACM Symposium on Operating Systems Principles | http://dblp.uni-trier.de/db/conf/sosp/ |
| conference | A | programming-languages-and-compilers | OOPSLA | Conference on Object-Oriented Programming Systems, Languages, and Applications | http://dblp.uni-trier.de/db/conf/oopsla/ |
| conference | A | software-engineering-for-systems | ASE | International Conference on Automated Software Engineering | http://dblp.uni-trier.de/db/conf/kbse/ |
| conference | A | software-engineering-for-systems | ICSE | International Conference on Software Engineering | http://dblp.uni-trier.de/db/conf/icse/ |
| conference | A | performance-reliability | ISSTA | International Symposium on Software Testing and Analysis | http://dblp.uni-trier.de/db/conf/issta/ |
| conference | A | systems-software | OSDI | USENIX Symposium on Operating Systems Design and Implementation | http://dblp.uni-trier.de/db/conf/osdi/ |
| conference | A | software-engineering-for-systems | FM | International Symposium on Formal Methods | http://dblp.uni-trier.de/db/conf/fm/ |
| conference | B | programming-languages-and-compilers | ICFP | ACM SIGPLAN International Conference on Functional Programming | http://dblp.uni-trier.de/db/conf/icfp/ |
| conference | B | programming-languages-and-compilers | LCTES | Languages, Compilers and Tools for Embedded Systems | http://dblp.uni-trier.de/db/conf/lctrts/ |
| conference | B | cloud-systems | ICSOC | International Conference on Service Oriented Computing | http://dblp.uni-trier.de/db/conf/icsoc/ |
| conference | B | software-engineering-for-systems | SANER | IEEE International Conference on Software Analysis, Evolution, and Reengineering | http://dblp.uni-trier.de/db/conf/wcre/ |
| conference | B | software-engineering-for-systems | ICSME | International Conference on Software Maintenance and Evolution | http://dblp.uni-trier.de/db/conf/icsm/ |
| conference | B | cloud-systems | ICWS | IEEE International Conference on Web Services | http://dblp.uni-trier.de/db/conf/icws/ |
| conference | B | distributed-systems | Middleware | International Middleware Conference | http://dblp.uni-trier.de/db/conf/middleware/ |
| conference | B | programming-languages-and-compilers | SAS | International Static Analysis Symposium | http://dblp.uni-trier.de/db/conf/sas/ |
| conference | B | software-engineering-for-systems | ESEM | International Symposium on Empirical Software Engineering and Measurement | http://dblp.uni-trier.de/db/conf/esem/ |
| conference | B | performance-reliability | ISSRE | IEEE International Symposium on Software Reliability Engineering | http://dblp.uni-trier.de/db/conf/issre/ |
| conference | B | systems-software | HotOS | USENIX Workshop on Hot Topics in Operating Systems | http://dblp.uni-trier.de/db/conf/hotos/ |
| conference | B | programming-languages-and-compilers | CC | International Conference on Compiler Construction | https://dblp.uni-trier.de/db/conf/cc/index.html |

## 使用建议

### 按问题映射 venue
- 用户问操作系统、内核、资源调度、文件系统、runtime：优先 OSDI、SOSP、ASPLOS、EuroSys、FAST、TOCS、TOS、JSS、SPE。
- 用户问分布式系统、云平台、大规模训练/服务基础设施：优先 OSDI、EuroSys、NSDI、SoCC、Middleware、TPDS、TCC、JPDC。
- 用户问体系结构、编译优化、GPU/加速器、系统性能：优先 ISCA、MICRO、HPCA、ASPLOS、CGO、PACT、PLDI、TC、TACO、TOPLAS。
- 用户问网络系统、数据中心网络、流量调度、互联网测量：优先 NSDI、SIGCOMM、INFOCOM、CoNEXT、IMC、TON、TOIT、CN。
- 用户问系统工程、可靠性、软件演化、系统实现经验：优先 ICSE、FSE、TSE、JSS、SPE、ISSRE、SANER、ICSME。

### 输出时的注意事项
1. 如果用户要“查论文”，先返回 5-15 个最相关 venue，但**当用户要求完整 system 名单时，必须保留系统方向全部 A/B 类会刊，尤其是 B 会和 B 刊。**
2. 如果用户要“做检索配置”，输出结构化 JSON，保留 link 字段。
3. 如果用户问题跨多个 area，可分组输出；如果是生成 skills 数据源，则输出全量相关分组，不要为了简短删掉 system B 类。
4. 默认不输出与 system 相关性较弱的 C 类 venues，除非用户明确要求扩展。

## 数据完整性要求

- **系统主方向（计算机体系结构 / 并行与分布计算 / 存储系统）中的 A 类和 B 类会议、期刊都必须保留。**
- 不能只保留顶会顶刊，也不能因为“相关性筛选”删除 B 类系统 venue。
- 当技能作为 agent 的论文检索入口时，system 主方向默认输出应覆盖：
  - A 类期刊
  - B 类期刊
  - A 类会议
  - B 类会议
- 网络、软工等方向可以做“紧相关”筛选，但 system 主方向应默认全保留 A/B。

## 数据来源说明
本技能中的 venue 清单来自用户提供的《CCF 推荐国际学术会议和期刊目录（2026年3月更新）》中以下章节的人工筛选汇总：
- 计算机体系结构 / 并行与分布计算 / 存储系统
- 计算机网络
- 软件工程 / 系统软件 / 程序设计语言

并额外按 system infra 检索场景做了“紧相关”筛选与重组。
