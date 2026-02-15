# TEP 结晶报告 — Recording & Analysis 深钻

> **TEP v2.0 | Mode: Hard | G=1 (Reality-Anchored)**
> **Date:** 2025-02-16
> **Target:** 自演化系统中"用户数据"的记录方式与分析方法

---

## 现实锚定 $\mathbb{G}=1$

| 领域 | 关键发现 | 来源 |
|------|---------|------|
| Agent 可观测性标准 | OpenTelemetry GenAI Semantic Conventions — 标准化 LLM 调用的 trace/span/metric 采集 | OTel SIG GenAI, 2024-2025 |
| LLM 日志分析 | RCACopilot (Microsoft) — 多模态数据（日志+指标+trace）自动 RCA，准确率 97% | FSE 2024 |
| 结构化推理 | LogReasoner — 赋予 LLM "粗到细"的专家级日志推理框架 | arXiv 2025 |
| 执行轨迹记录与回放 | **AgentRR (Agent Record & Replay)** — 记录 agent 交互 trace → 总结为经验 → 回放指导后续任务 | arXiv 2025 |
| 失败诊断 | AgentRx — 从执行轨迹中定位 agent 关键失败步骤 | arXiv 2026 |
| 生产部署 | IBM LogAn — LLM 日志分析工具，2024 年 5 月上线，节省大量人工 | ICPE 2025 |

---

## Round 1 | $\mathbb{S}=1$ | $\Delta=100\%$ | Status: Diverging

### 🔴 [RED TEAM] 攻击

**攻击向量 A — "记录一切"是一个天真的策略**

> 直觉上，记录越多越好。但这忽略了三个硬约束：
>
> 1. **LLM 上下文窗口有限**：就算你记录了 10MB 的结构化 trace，log-miner 的 LLM 一次也只能处理 ~128K tokens。记录超过分析器消化能力的数据是**浪费**。
> 2. **信噪比 (SNR) 退化**：记录越多，噪声越多。LLM 在高噪声输入中的分析准确率会显著下降。IBM LogAn 的实践证明，**预处理和过滤比原始数据量更重要**。
> 3. **存储与成本**：如果每个 cycle 记录完整的 OTel trace，一年的数据量可能达到 GB 级。对个人项目不现实。
>
> 所以问题不是"记录什么"，而是"**记录的最小充分集是什么？**"

**攻击向量 B — Recording 和 Analysis 不可分离设计**

> 蓝队可能倾向于先设计记录格式，再设计分析方法。但这是错误的。**记录格式必须由分析需求倒推**——否则你会记录一堆分析器用不到的数据。
>
> AgentRR 论文的核心洞见是：记录的目的不是"存档"，而是"回放"——数据的价值由它对未来决策的影响力决定。
>
> 如果你的分析器（log-miner）是一个 LLM，那记录格式就必须是 **LLM-native** 的——即自然语言 + 轻量结构化的混合格式，而非纯机器可解析的 JSON schema。

**攻击向量 C — nanobot-auto 的"用户数据"和传统 observability 的根本差异**

> OpenTelemetry 是为**人类运维工程师**设计的可观测性框架。它的假设是：有一个人类在看 dashboard、查 trace、做判断。
>
> nanobot-auto 的"用户"是 LLM。LLM 不看 dashboard。LLM 读文本。这意味着：
> - Prometheus 格式的时序指标对 LLM 来说不是最优输入
> - Jaeger 式的 span 树状结构对 LLM 来说信息密度过高
> - LLM 更擅长处理**叙事性文本** —— "第 42 次 cycle：log-miner 发现了 3 个 Issue，auto-dev 修复了 2 个，1 个 PR 因 CI 失败被拒绝"
>
> **OTel 是好工具，但直接套用其格式可能适得其反。**

### 🔵 [BLUE TEAM] 防御

**对 A 的防御 — 最小充分记录集 (Minimum Sufficient Record)**

> 接受"记录一切是天真的"这个批评。需要定义最小充分集。
>
> 从分析需求倒推——log-miner 需要回答的问题只有三类：
>
> | 问题类型 | 需要的数据 | 记录方式 |
> |---------|----------|---------|
> | **1. 出了什么错？** | 错误日志、异常堆栈、失败的操作 | 结构化错误事件 |
> | **2. 上次做了什么，结果如何？** | 上一 cycle 的决策和产出 | Cycle Summary (叙事性) |
> | **3. 系统整体在变好还是变差？** | 关键指标的变化趋势 | H(t) 快照 (数值型) |
>
> 这三类数据对应三种不同的记录格式，不需要通用的 trace 格式。

**对 B 的防御 — LLM-native 记录格式**

> Red Team 的"分析需求倒推记录格式"完全正确，"LLM-native"这个概念很关键。
>
> 提出一个核心设计原则：**Cycle Report（周期报告）**。
>
> 不是记录原始日志，而是每个 cycle 结束时生成一份**结构化但可读的总结**：
>
> ```markdown
> # Cycle Report — 2025-02-16 Cycle #42
>
> ## What happened
> - log-miner analyzed 847 lines of runtime logs
> - Created 2 Issues: #101 (bug: timeout in feishu channel), #102 (enhancement: add retry logic)
> - Skipped 1 potential issue (duplicate of #98, already fixed)
>
> ## What was done
> - auto-dev picked up #101, delegated to Codex
> - Codex modified `nanobot/channels/feishu.py` (added 30s timeout)
> - PR #55 created, CI passed
>
> ## Outcome
> - auto-merge merged PR #55
> - #101 closed
> - #102 remains open (queued for next cycle)
>
> ## Health Vector Delta
> - error_rate: 2.3/hr → pending (next cycle measurement)
> - fix_success_rate: 1/1 = 100%
> - tokens_consumed: 12,400
> - lead_time: 4.5 hours
>
> ## Knowledge Updated
> - Fix Outcome Log: +1 entry (feishu timeout fix, succeeded)
> - Issue Type Registry: "channel_timeout" count → 3, success_rate → 67%
> ```
>
> 这个格式是 **LLM-native** 的——下一个 cycle 的 log-miner 可以直接读前几份 Cycle Report 作为上下文，无需解析器。

**对 C 的防御 — 双层记录架构**

> 接受 OTel ≠ LLM 最优输入的批评，但完全放弃结构化数据也不对——H(t) 度量需要精确数值。
>
> 提出**双层记录**：
>
> | 层 | 格式 | 消费者 | 用途 |
> |---|------|--------|------|
> | **L1: Cycle Report** | Markdown 叙事 | LLM (log-miner) | 下一 cycle 的上下文输入 |
> | **L2: Metric Snapshots** | JSON 数值 | 脚本 / H(t) 仪表板 | 趋势分析 + 假说验证 |
>
> L1 是 LLM 读的，L2 是代码读的。两者同时生成，互不替代。

---

## Round 2 | $\mathbb{S}=2$ | $\Delta=30\%$ | Status: Converging

### 🔴 [RED TEAM] 攻击

**攻击向量 D — Cycle Report 是谁写的？**

> 蓝队的 Cycle Report 方案无法自洽地回答一个关键问题：**谁负责生成这份报告？**
>
> - 如果是 auto-merge 在合并后生成 → auto-merge 不知道 log-miner 做了什么分析
> - 如果是 log-miner 在下一轮开始时回顾生成 → 这本身就需要分析原始日志，回到了起点
> - 如果是一个新的第四组件 → 又增加了架构复杂度
>
> Cycle Report 看着很美，但**在三元架构下没有自然的生成位置**。

**攻击向量 E — 分析方法的核心问题没有被讨论**

> 蓝队花了大量篇幅讨论 Recording，但几乎没有触及 Analysis。Recording 只是输入；Analysis 才是价值产出。
>
> 核心分析问题：log-miner 今天只做一件事——读日志 → 输出 Issues。但真正有价值的分析应该包括：
> 1. **趋势识别**：不只是"今天有什么错"，而是"过去一周同类错误在增加还是减少"
> 2. **因果推断**：不只是"错误 A 出现了"，而是"错误 A 可能是因为 cycle #40 的修改引入的"
> 3. **优先级排序**：哪个问题影响最大？哪个最容易修？
>
> 目前 log-miner 的 LLM prompt 承担了全部分析责任，但没有给它足够的**分析工具**。

### 🔵 [BLUE TEAM] 防御

**对 D 的防御 — Cycle Report 的生成方式**

> Red Team 的追问暴露了一个设计缝隙。解决方案：
>
> **每个组件在执行完毕后追加自己的段落到 Cycle Report。** 不需要第四组件。
>
> ```
> Cycle Report 生成流程:
>
> 1. log-miner 执行完 → 写入 "What was observed" + "Issues created"
> 2. auto-dev 执行完 → 追加 "What was done" + "PR details"
> 3. auto-merge 执行完 → 追加 "Outcome" + "Health Vector Delta"
>    → Cycle Report 闭合
> ```
>
> 每个组件只写自己知道的部分。Report 是一个**累积文档**，不是一次性生成的。
>
> 实现方式：一个简单的 append-only markdown 文件。每个 skill 在结束时调用 `append_cycle_report(section, content)`。

**对 E 的防御 — 分层分析架构**

> 接受"Analysis 被忽视"的批评。提出分层分析设计：
>
> | 分析层 | 输入 | 输出 | 实现方式 |
> |--------|------|------|---------|
> | **L0: 数据采集** | 原始日志 + 运行时指标 | L2 Metric Snapshots | 脚本（非 LLM） |
> | **L1: 单 Cycle 分析** | 当前日志 + 前 N 份 Cycle Reports | Issues（结构化） | LLM (log-miner) |
> | **L2: 跨 Cycle 趋势** | Metric Snapshots 时序 + Issue Type Registry | 趋势报告 + 优先级 | 脚本算趋势 + LLM 解读 |
> | **L3: 因果溯源** | Cycle Reports + Git history + PR 记录 | "Issue X 可能因 PR #Y 引入" | LLM（需要 Git 上下文） |
>
> **关键设计决策：L0 不用 LLM。**
>
> 数据采集必须是确定性的脚本——LLM 做数据采集会引入噪声（幻觉、遗漏）。LLM 只在 L1-L3 做**解读**，不做**采集**。
>
> 这与 RCACopilot 的架构一致：先用确定性工具采集多模态数据，再用 LLM 做根因推断。
>
> **L3（因果溯源）是最有研究价值的层**——"这个新 bug 是不是系统自己上次改出来的？"直接关联 OCLSE P1（观测-修改耦合）。但 L3 也是最难的，应放在后期实现。

---

## Round 3 | $\mathbb{S}=3$ | $\Delta=8\%$ | Status: CRYSTALIZED ✅

### 🔴 [RED TEAM] 最终攻击

**攻击向量 F — 上下文窗口管理是隐藏的核心难题**

> 最后一个问题：随着 cycle 数增加，Cycle Reports 会越来越多。log-miner 不能每次都把所有历史 Report 塞进 prompt。你需要一个**上下文窗口管理策略**：
> - 哪些历史 Report 被纳入当前 cycle 的上下文？
> - 纳入多少份？
> - 如何压缩旧的 Report？
>
> 这不是小问题——上下文选择策略直接决定 log-miner 能"看到"多远的历史，进而决定它能做多深的趋势分析和因果推断。

### 🔵 [BLUE TEAM] 最终防御

> 提出**滑动窗口 + 摘要压缩**策略：
>
> ```
> log-miner 上下文构成:
>
> ┌─────────────────────────────────────────┐
> │ [固定] System Prompt + CONSTITUTION     │
> ├─────────────────────────────────────────┤
> │ [固定] Issue Type Registry (摘要)       │  ← K 层常驻
> ├─────────────────────────────────────────┤
> │ [最新] 最近 3 份完整 Cycle Reports      │  ← 滑动窗口
> ├─────────────────────────────────────────┤
> │ [压缩] 过去 30 天的 Cycle 摘要 (每份1行) │  ← 压缩层
> ├─────────────────────────────────────────┤
> │ [当前] 今天的原始日志                    │  ← 本轮输入
> └─────────────────────────────────────────┘
> ```
>
> - **最近 3 份**：提供短期记忆（"昨天修了什么，结果怎样"）
> - **30 天摘要**：提供长期趋势（"过去一个月同类问题出现了 7 次"）
> - **Issue Type Registry**：提供聚合统计（"channel_timeout 修复成功率 67%"）
>
> 压缩策略：每份 Cycle Report 在 30 天后被 LLM 压缩为 1 行摘要。这是一个 **离线批处理**，不占用 cycle 时间。
>
> Token 估算：
> - System + Constitution: ~2K tokens
> - Issue Type Registry: ~500 tokens
> - 3 Cycle Reports × ~800 tokens: ~2.4K tokens
> - 30-day summaries × ~50 tokens: ~1.5K tokens
> - Raw logs (当前): ~4K tokens (截断)
> - **总计: ~10K tokens** — 远在 128K 上下文窗口之内

---

# 📜 结晶结论

**$\mathbb{S}=3$ | $\Delta=8\%$ | Status: CRYSTALIZED ✅ | $\mathbb{G}=1$ ✅**

## 1. Recording — 双层记录

| 层 | 名称 | 格式 | 消费者 | 生成方式 |
|---|------|------|--------|---------|
| **L1** | Cycle Report | Markdown 叙事 | LLM | 三组件各自追加 |
| **L2** | Metric Snapshot | JSON 数值 | 脚本 | 确定性采集 |

**Cycle Report 是核心创新点**——一种 LLM-native 的 Agent 执行记录格式，替代传统 OTel trace。

## 2. Analysis — 四层分析

| 层 | 名称 | 输入 | 输出 | 用 LLM？ | 优先级 |
|---|------|------|------|---------|--------|
| **L0** | 数据采集 | 原始日志 + 运行时 | Metric Snapshots | ❌ 脚本 | M0 |
| **L1** | 单 Cycle 分析 | 日志 + 近期 Reports | Issues | ✅ | M1 |
| **L2** | 跨 Cycle 趋势 | Metrics 时序 | 趋势报告 | ✅ 辅助 | M3+ |
| **L3** | 因果溯源 | Reports + Git diff | 因果链 | ✅ | M5+ |

**关键原则：L0 永远不用 LLM。数据采集必须是确定性的。**

## 3. 上下文窗口管理

```
滑动窗口: 最近 3 份完整 Cycle Report
压缩层: 30 天内的 1 行摘要
常驻层: Issue Type Registry
总预算: ~10K tokens
```

## 4. 被推演杀死的想法 ☠️

| 原方案 | 死因 |
|--------|------|
| 直接套用 OpenTelemetry trace 格式 | LLM 不是人类运维，OTel 格式对 LLM 信息密度不优 |
| 记录一切原始数据 | 超出 LLM 上下文窗口，SNR 退化，存储成本不可控 |
| Cycle Report 由单一组件一次性生成 | 三元架构下无信息完整的生成位置 → 改为累积追加 |
| 全部分析交给 LLM | 数据采集 (L0) 必须确定性，LLM 幻觉会污染基础数据 |

## 5. 对 Roadmap 的影响

| 原里程碑 | 调整 |
|---------|------|
| M0 (可观测性) | → 拆分为 M0a (L0 脚本采集 + L2 Metric Snapshot) 和 M0b (L1 Cycle Report 格式 + 追加机制) |
| M1 (Knowledge) | 不变，但 K 的数据来源从"手动设计"变为"从 Cycle Report 自动提取" |
| M3 (基线实验) | 数据来源从"原始日志"变为"Cycle Reports + Metric Snapshots" |

---

*TEP v2.0 结晶。第三次推演。累计 9 轮对抗。*
