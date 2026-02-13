# nanobot MVP：单 Bot 自循环（Python 版）

> 本文是项目的初始锚点，描述最小可行闭环。Agent 应以此为唯一指导完成 MVP。

## 目标

一个 Python nanobot 实例通过 3 个 cron 任务实现每日自动迭代：

```
20:00 分析日志 → 提 Issue
02:00 认领 Issue → 开发 → 提 PR
08:00 审核 PR → 合并 → 自更新
```

## 项目来源

本仓库即 [HKUDS/nanobot](https://github.com/HKUDS/nanobot)（Python 版）。

## 需要创建的 3 个 Skill

skill 是纯 Markdown 指令文件，放在 `nanobot/skills/` 目录下，不需要修改 Python 源码。Bot 通过 `exec` tool 调用 `gh` CLI 和 `git` 命令完成操作。

### 1. `nanobot/skills/log-miner/SKILL.md`

**职责：** 分析自身日志，发现问题，提交 Issue。

指导 bot 执行以下步骤：
1. 用 `exec` 扫描 `~/.nanobot/sessions/` 下近 24h 的 `.jsonl` 日志
2. 用 `grep` 统计 error / failed / timeout / traceback 等关键词
3. 如有异常，用 LLM 分析模式并总结为结构化问题描述
4. 用 `exec("gh issue create --repo HKUDS/nanobot --title '...' --body '...' --label 'auto-report'")` 提交
5. 如无异常，不创建 Issue（避免噪音）

SKILL.md 的 frontmatter：
```yaml
---
name: log-miner
description: "Analyze recent nanobot logs, detect errors and anomalies, and create GitHub issues for problems found."
---
```

### 2. `nanobot/skills/auto-dev/SKILL.md`

**职责：** 认领一个 Issue，修改代码，提交 PR。

指导 bot 执行以下步骤：
1. `exec("gh issue list --repo HKUDS/nanobot --label auto-report --state open --json number,title,body --limit 1")` 获取 Issue
2. LLM 分析 Issue 内容 → 制定修复方案
3. `exec("git checkout -b fix/issue-N")` 创建分支
4. 用 `read_file` / `write_file` / `exec` 修改代码
5. `exec("python -m py_compile <modified_file>")` 语法检查 ← **Python 安全网**
6. 如果存在测试：`exec("python -m pytest tests/ -x --tb=short")` 跑测试
7. `exec("git add -A && git commit -m 'fix: ...' && git push origin fix/issue-N")`
8. `exec("gh pr create --repo HKUDS/nanobot --title 'fix: ...' --body 'Closes #N'")`

SKILL.md 的 frontmatter：
```yaml
---
name: auto-dev
description: "Pick an open auto-report issue, develop a fix, verify with py_compile and pytest, and create a pull request."
---
```

### 3. `nanobot/skills/auto-merge/SKILL.md`

**职责：** 审核 PR，CI 通过则合并并自更新。

指导 bot 执行以下步骤：
1. `exec("gh pr list --repo HKUDS/nanobot --state open --json number,title --limit 5")` 获取 PR 列表
2. 对每个 PR：`exec("gh pr checks N --repo HKUDS/nanobot")` 检查 CI 状态
3. CI 全绿 → `exec("gh pr merge N --squash --delete-branch")`
4. CI 红 → `exec("gh pr close N --comment 'CI failed'")`
5. 合并后 → `exec("git pull origin main && pip install -e .")` 拉取并重装（自更新）

SKILL.md 的 frontmatter：
```yaml
---
name: auto-merge
description: "Review open PRs, merge if CI passes, close if CI fails, then self-update."
---
```

## Cron 配置

启动 bot 后，通过对话设置 3 个定时任务：

```
cron(action="add", message="Run log-miner: analyze recent logs and create issues for any problems found", cron_expr="0 20 * * *")

cron(action="add", message="Run auto-dev: check open issues with label auto-report, pick one, develop a fix, and create a PR", cron_expr="0 2 * * *")

cron(action="add", message="Run auto-merge: check open PRs, merge if CI passes, close if CI fails, then pip install -e . to self-update", cron_expr="0 8 * * *")
```

## CI 配置

需要一个最小的 GitHub Actions 配置 `.github/workflows/ci.yml`：

```yaml
name: CI
on: [pull_request]
jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -e .
      - run: python -m py_compile nanobot/agent/loop.py
      - run: python -m pytest tests/ -x --tb=short || true
```

## 验证方式

手动逐步触发（不等 cron）：

1. 对 bot 说 "Run log-miner..." → 检查 GitHub 出现 Issue
2. 对 bot 说 "Run auto-dev..." → 检查 GitHub 出现 PR
3. 等 CI 跑完
4. 对 bot 说 "Run auto-merge..." → 检查 PR 被合并

## 约束

- MVP 阶段只有 **1 个 bot 实例**
- 不引入 telemetry/脱敏/多用户，那是后续阶段的事
- bot 需要通过 `gh auth login` 获得 GitHub 访问权限
- 与 Rust 版 MVP 平行对比，验证哪个迭代效果更好
