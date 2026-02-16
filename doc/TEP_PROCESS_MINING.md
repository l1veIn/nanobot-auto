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

**A — 事件日志太稀疏。** ~~nanobot-auto 每天 1 个 cycle = 1 条 trace。~~ **[已被后续熵注入修正]** cycle 频率不固定——可以链式触发、主动触发、被动触发，一天可能有多个 cycle。稀疏性问题**部分消解**，但仍需注意初期数据积累。

**B — 流程太简单。** ~~当前流程是严格线性的：miner → dev → merge。~~ **[已被后续熵注入修正]** 实际流程有多种变体（链式触发、主动跳过 miner、被动紧急响应等），且不同触发方式本身就是不同的 process variant：

**C — Conformance Checking 的前提不满足。** 一致性检查需要两个输入：(1) 参考模型 (2) 事件日志。CONSTITUTION.md 是自然语言规则，不是 Petri Net。将其形式化为 Petri Net 需要手动建模，且很多规则（如"不可修改 CONSTITUTION"）是语义级约束，无法用控制流模型表达。

### 🔵 BLUE

**对 A** — 稀疏性通过两种方式缓解：
1. **可变频率**：链式/主动/被动触发意味着一天可能有多个 cycle
2. **细粒度事件**：每个 cycle 包含数十到上百个工具调用事件

**对 B** — 实际变体丰富：
- Variant 1: cron → miner → dev → merge (日常)
- Variant 2: critical_error → miner → dev → merge (被动触发)
- Variant 3: user_command → dev → merge (主动，跳过 miner)
- Variant 4: merge → miner → dev → merge (链式触发)
- 变体的分布变化本身就是 P2（分布漂移）的直接度量。

**对 C** — 不需要把整个 CONSTITUTION 形式化。只形式化**控制流约束**部分：
- Article 1（角色分离）→ 可编码为"miner 不出现 code_write 事件"
- Article 5（隔离开发）→ 可编码为"dev 事件只出现在 /tmp 路径"
- 语义约束（如 Article 4 强制输出）→ 保留给 LLM 判断

**混合策略：pm4py 检查可形式化的约束，LLM 检查语义约束。**

---

## Round 2 | Δ=25%

### 🔴 RED

**D — 过度工程风险。** pm4py 是一个重型库——Petri Net、alignment 算法、XES 解析。为了分析一个三步 pipeline 引入这套基础设施，是否值得？直接写一个 Python 脚本统计 "成功/失败/跳过" 的比例就能达成 80% 的分析目标。

**E — 事件定义是隐藏的大工程。** 蓝队说"提高事件粒度"，但谁来定义哪些事件值得记录？在代码中埋点需要修改每个 skill 的实现。

### 🔵 BLUE

**对 D** — 如果只是统计成功/失败，确实不需要 pm4py。pm4py 的真正价值在两个场景：
1. **系统复杂度增长后**：当 pipeline 从三步变成十步（加入 K 层、Review 层、事件触发等），手写脚本无法 scale
2. **学术贡献**：用流程挖掘分析自演化 agent 是一个**新颖的交叉研究方向**，本身可发表

**对 E** — **[被后续代码分析彻底解决]** Agent 的所有行为都是工具调用（读文件、写文件、执行命令、API 调用）。`Tool.execute()` 是统一入口，只需在此一处埋点：

```json
{
  "case_id": "cycle_042",
  "activity": "filesystem.read",
  "skill": "auto-dev",
  "timestamp": "2025-02-16T00:30:15Z",
  "args_summary": "{path: /tmp/fix/loop.py}",
  "success": true,
  "duration_ms": 150
}
```

**实现成本：~20 行代码改 `loop.py` 一个文件，零工具实现改动。** auto-dev 大量读写文件的行为自动被捕获，工具故障→dev 失败的因果链自动可追踪。

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
| **Phase 0** | Tool.execute() 埋点 + 输出 XES 事件日志 | ❌ 只写 XES 文件 |
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
