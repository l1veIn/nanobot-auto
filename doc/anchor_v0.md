# 🐈 nanobot-auto：自主升级 Bot 框架

> **Anchor v0** · 2026-02-13 · 所有决策均经 TEP v2.0 结晶

## 愿景

补齐 AI 软件开发流程的最后一环——**自动化用户信息收集与整理**。后续环节（需求分析、开发、测试、部署）已由成熟 AI 工具链覆盖。本项目的目标是让软件基于用户数据自我迭代，无需人类中介。

讽刺性约束：本仓库**仅允许 AI Agent 提交 Issue 和 PR**，不允许人类提交。

## 结晶决策清单

| # | 决策 | 结论 | TEP 𝕊 |
|---|------|------|--------|
| 1 | 总体架构可行性 | 可行，需 3 个补丁（auto_update skill / stable 分支保护 / 三层守护） | 3 |
| 2 | 基座选型 | **nanobot-rs**（fork 后自行维护）。Rust 编译期检查 = 自改代码的安全网 | 3 |
| 3 | 缓冲层方案 | **双 GitHub repo 替代自建服务器**。见下方阐述 | 5 |

### 缓冲层：从自建服务器到双 repo 架构（TEP 𝕊=5）

**比喻：流行病学调查。** 每个用户侧 bot 是社区诊所——能诊断（本地 LLM 分析）和消毒（脱敏）。但只有疾控中心能看到全国数据，发现跨地区的群体模式。

三轮 TEP 推演后发现：**疾控中心不需要是一台服务器，GitHub 本身就是。** 用两个 repo 分离原始数据和精炼 Issue：

- **`nanobot-telemetry`**（原始报告池）：边缘 bot 通过 `gh issue create` 上报脱敏后的结论
- **`nanobot-auto`**（代码仓库）：Bot-Analyst 从 telemetry repo 聚合分析，生成精炼 Issue

优势：零自建基础设施、GitHub 自带防滥用、全程可审计、nanobot 原生 `gh` CLI 支持。

## 架构总览

```
用户侧 nanobot (N个)
│  telemetry skill: 行为埋点 + 会话摘要(本地LLM)
│  sanitizer (L1): 设备端脱敏，数据出设备前完成
│  gh issue create --repo org/nanobot-telemetry
▼
[nanobot-telemetry repo] (原始报告池，公开可审计)
│  Bot-Analyst (cron): 聚合去重，发现群体模式
│  gh issue create --repo org/nanobot-auto
▼
[nanobot-auto repo] (AI-only 代码仓库)
│  Bot-Dev:   认领 Issue → 开发 → Push
│  Bot-Test:  跑测试 → 合并/打回
▼
Release → 所有 Bot 自动更新 → 闭环
```

所有 Bot 均为同构 nanobot-rs，仅 cron/skill 配置不同。

## 信息漏斗模型

```
用户设备(诊所):  行为埋点(全量) + 会话摘要(本地LLM) → 脱敏 → 上报结论到 telemetry repo
疾控中心(Bot-Analyst): 跨用户聚合去重 → 精炼 Issue 到 auto repo
```

- 边缘智能化：用户侧做分析+脱敏，上报的是结论而非原始数据
- 中心轻量化：Bot-Analyst 只做跨用户聚合和 Issue 生成
- 漏斗本身可被 Bot-Curator 提议升级（元升级）

## 脱敏契约

**第一原则：脱敏在用户设备上完成，数据离开设备前必须已脱敏。** 哪怕降低上报质量，也绝不妥协用户数据安全。

脱敏规则（确定性，零 LLM，开源可审计）：

- 正则移除：API key / 邮箱 / 电话 / IP
- 哈希替换：用户名 → SHA256 前 8 位
- 内容摘要：原始消息 → 仅保留意图分类标签，**丢弃原文**
- 白名单保留：tool 名称 / error code / 耗时

## 路线图

| Phase | 目标 | 产出 |
|-------|------|------|
| 0 | 仓库搭建 | Fork nanobot-rs，创建 telemetry repo，CI + bot-only 检查 |
| 1 | 信息入口 | telemetry skill + sanitizer |
| 2 | 信息处理 | Bot-Analyst + Bot-Curator，首个 Issue 自动生成 |
| 3 | 开发闭环 | Bot-Dev + Bot-Test，首个 PR 自动合并 |

## 待定决策

- [ ] 项目名（nanobot-auto? nano-hive? swarm?）
- [ ] 用户侧 telemetry skill 的 opt-in 机制设计
- [ ] Bot 账号管理（几个 GitHub bot 账号？权限划分？）
- [ ] 与 Python nanobot 上游的关系（是否也支持 Python 用户上报？）
