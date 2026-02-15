# TEP 结晶 — Process Mining 方案

> **TEP v2.0 | Hard | G=1 | 2025-02-16**
> **Target:** 用 pm4py + 流程挖掘替代 LLM 式 Recording/Analysis

---

## 锚定

- pm4py 已有 LLM 集成模块 (PM4Py.LLM)，支持自动流程发现和一致性检查
- "Re-Thinking Process Mining in AI-Based Agents Era" (arXiv 2024) 直接对标我们的场景
- 小事件日志是流程挖掘的已知弱点——精度/泛化指标在少量 trace 下不可靠

---

## Round 1 | Δ=100%

### 🔴 RED

**A — 事件日志太稀疏。** nanobot-auto 每天 1 个 cycle = 1 条 trace。流程挖掘算法（Alpha Miner、Inductive Miner）通常需要数百条 trace 才能发现有意义的模型。30 天 = 30 条 trace，统计上远不够。Conformance Checking 的 fitness/precision 指标在这个量级下不可靠。

**B — 流程太简单。** 当前流程是严格线性的：miner → dev → merge。没有分支、没有并行、没有循环。对这种链式流程做 Process Discovery 没有信息增益——你已经知道流程长什么样了。流程挖掘的价值在于**发现你不知道的实际流程**，但这里实际流程和设计流程完全一致。

**C — Conformance Checking 的前提不满足。** 一致性检查需要两个输入：(1) 参考模型 (2) 事件日志。CONSTITUTION.md 是自然语言规则，不是 Petri Net。将其形式化为 Petri Net 需要手动建模，且很多规则（如"不可修改 CONSTITUTION"）是语义级约束，无法用控制流模型表达。

### 🔵 BLUE

**对 A** — 承认稀疏性问题，但可以**提高事件粒度**来弥补。一个 cycle 不是一条 trace，而是一条**多事件 trace**。如果记录细粒度事件（进入函数、调用 API、创建文件、LLM 推理...），一个 cycle 可能产生 50-200 个事件。30 天 = 30 条 trace × 100 事件 = 3000 个事件点。这对 Inductive Miner 来说够了。

**对 B** — 表面线性，但实际有变体：
- 正常路径: miner → issue → dev → PR → merge ✅
- 失败路径: miner → issue → dev → PR → CI fail → reject ❌
- 空路径: miner → no issue found → skip
- 重试路径: miner → issue → dev → Codex timeout → retry
- 这些**变体间的分布变化**本身就是 P2（分布漂移）的直接度量。

**对 C** — 不需要把整个 CONSTITUTION 形式化。只形式化**控制流约束**部分：
- Article 1（角色分离）→ 可编码为"miner 不出现 code_write 事件"
- Article 5（隔离开发）→ 可编码为"dev 事件只出现在 /tmp 路径"
- 语义约束（如 Article 4 强制输出）→ 保留给 LLM 判断

**混合策略：pm4py 检查可形式化的约束，LLM 检查语义约束。**

---

## Round 2 | Δ=25%

### 🔴 RED

**D — 过度工程风险。** pm4py 是一个重型库——Petri Net、alignment 算法、XES 解析。为了分析一个三步 pipeline 引入这套基础设施，是否值得？直接写一个 Python 脚本统计 "成功/失败/跳过" 的比例就能达成 80% 的分析目标。

**E — 事件定义是隐藏的大工程。** 蓝队说"提高事件粒度"，但谁来定义哪些事件值得记录？在代码中埋点需要修改每个 skill 的实现。这不是引入 pm4py 就自动获得的——这是大量的手动 instrumentation 工作。

### 🔵 BLUE

**对 D** — 如果只是统计成功/失败，确实不需要 pm4py。pm4py 的真正价值在两个场景：
1. **系统复杂度增长后**：当 pipeline 从三步变成十步（加入 K 层、Review 层、事件触发等），手写脚本无法 scale
2. **学术贡献**：用流程挖掘分析自演化 agent 是一个**新颖的交叉研究方向**，本身可发表

**对 E** — 接受。事件定义应从最小集开始：

| 事件 | 来源 | 自动/手动 |
|------|------|----------|
| skill_start / skill_end | agent loop | 自动（已有） |
| issue_created / issue_skipped | log-miner | 需埋点 |
| codex_called / codex_result | auto-dev | 需埋点 |
| pr_created / ci_result / merged / rejected | auto-merge | 需埋点 |

**约 8 个事件类型，6 个埋点。** 工作量可控。

---

## Round 3 | Δ=9% | CRYSTALIZED ✅

### 🔴 RED 最终攻击

**F — 那前一份 TEP 的 Cycle Report 方案怎么办？两个方案冲突吗？**

### 🔵 BLUE 最终防御

不冲突，而是**两层互补**：

| 层 | 工具 | 消费者 | 用途 |
|---|------|--------|------|
| **结构化事件层** | pm4py (XES) | 算法 | 流程发现、一致性检查、性能分析 |
| **叙事层** | Cycle Report (MD) | LLM | 下一 cycle 的上下文、语义级分析 |

事件日志是**机器读的**，Cycle Report 是 **LLM 读的**。两者从同一次执行中产生，格式不同、消费者不同。

但前一份 TEP 的四层分析架构需要修正：

| 原方案 | 修正 |
|--------|------|
| L0: 确定性脚本采集 | → **L0: 事件埋点 + XES 日志** (pm4py 格式) |
| L1: LLM 单 cycle 分析 | → 不变，但输入增加 conformance 报告 |
| L2: 跨 cycle 趋势 | → **pm4py process variant 分布变化** (替代手写趋势脚本) |
| L3: 因果溯源 | → 不变 (仍需 LLM) |

---

## 结晶结论

### 采纳 Process Mining，但分阶段

| Phase | 做什么 | 需要 pm4py？ |
|-------|--------|-------------|
| **Phase 0** | 定义 8 个核心事件 + 埋点 + 输出 XES 日志 | ❌ 只写 XES 文件 |
| **Phase 1** | CONSTITUTION 控制流约束 → Petri Net + conformance checking | ✅ |
| **Phase 2** | Process variant 分布变化 → P2 检测 | ✅ |

### 被杀死的想法 ☠️

| 想法 | 死因 |
|------|------|
| 全部 CONSTITUTION 形式化为 Petri Net | 语义约束无法用控制流模型表达 |
| 替代掉所有 LLM 分析 | 因果溯源 (L3) 和语义约束检查仍需 LLM |
| 立刻引入 pm4py | Phase 0（埋点）是前置依赖，先做埋点 |

### 核心架构修正

```
事件埋点 (XES)──→ pm4py ──→ Conformance Report ──┐
                                                  ├──→ LLM (log-miner)──→ Issues
Cycle Report (MD)─────────────────────────────────┘
```

pm4py 不替代 LLM，而是为 LLM **提供确定性分析结果作为输入**。

---

*TEP v2.0 第四次推演。累计 12 轮对抗。*
