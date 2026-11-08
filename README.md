# Loon 分流规则备份

个人独立备份仓库，不与上游做强制镜像。备份与同步历史从 2026-11-08 开始。

## 订阅

[Apple AI.lsr 稳定 Raw 地址](https://raw.githubusercontent.com/Flora-air/loon-rules-backup/main/Apple%20AI.lsr)

在 Loon 的远程规则中使用上述地址，策略选择你自己的 Apple AI 代理策略。

## 来源与范围

2026-11-08 修正：`Apple AI.lsr` 以用户提供的八条 `DOMAIN-SUFFIX` 规则为固定基线，保存于 sources.json 的 pinned_rules。用户提供的截图将其描述为原文件内容；本仓库未独立核实该缓存来源，不声称恢复了原仓库历史。

每日继续检查 [angribot/rules 的 AppleIntelligence.lsr](https://github.com/angribot/rules/blob/main/AppleIntelligence.lsr)：先独立校验下载内容，再合并新增域名。同域名始终保留基线的 DOMAIN-SUFFIX，不会被上游的 DOMAIN 缩窄。即使上游只包含五条，八条基线也不会丢失。上游下载或校验失败时保留整个最后可用文件。

上游规则 Copyright (C) 2024 Civi，采用 GNU AGPL v3 或更新版本，完整许可见 LICENSE。本仓库脚本亦采用 AGPL-3.0-or-later。订阅文件是合并后的派生版本，已在 2026-11-08 修改。

.lsr 远程规则文件只含规则行和注释；用户粘贴的 `[Rule]` 是配置节标题，不写入远程规则文件。

只同步 sources.json 明确列出的文件。其他原订阅尚未提供，因此没有随意替换其内容；新增规则需指定并核对来源及对应校验器。

## 每日同步与保留策略

- 每天 UTC 01:23（新加坡/北京时间 09:23）由 GitHub Actions 运行；也支持 Actions 页面手动 Run workflow。GitHub 调度可能延迟。
- HTTPS 下载完整内容后检查 UTF-8、文件大小、逐行规则语法、至少 5 条不同规则及 3 条必备 Apple Relay 规则。
- 规则数比本地下降超过 20% 时拒绝更新，需人工审查。
- 404、删库、网络失败、空内容、错误页面或校验失败：保留现有文件的全部字节，不删除、不清空。下载成功但校验失败也不会覆盖。
- 校验全部通过才原子替换对应文件。正常 Git 提交保留每次历史，不 force-push、不 reset、不同步上游删除。
- sync-status.json 记录最后一次检查时间、来源、状态和文件 SHA-256；失败会使 Actions 显示失败，便于发现。
- SHA-256 用于记录版本，不等于上游真实性签名；语法校验不能保证 Apple AI 服务一定可用。

每日写入检查记录形成可追溯活动。仍应留意 GitHub 对公共仓库长期不活跃时停用定时工作流的限制；若 Actions 显示 disabled，应重新启用。

## 检查与回滚

[工作流与运行记录](https://github.com/Flora-air/loon-rules-backup/actions/workflows/sync.yml)

查看 sync-status.json 的 checked_at 与状态。需要回滚时，在 Git 历史中找到最后可用内容，恢复文件并创建一个新提交；无需删除历史。若上游持续失效，保留当前规则，人工核对新来源后再修改 sources.json。

本地验证：`python3 -m unittest discover -s scripts -p 'test_*.py' -v`。
测试包含 404/删库、超时、空内容、HTML、编码损坏、错误语法、必备规则丢失、显著截断，以及正常更新。
