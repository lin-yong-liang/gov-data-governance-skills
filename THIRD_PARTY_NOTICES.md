# 第三方内容与许可证

本仓库包含多个来源的内容。除本仓库原创部分（MIT）外，其余内容遵循各自许可证。

## 1. Anthropic 官方 skills

- 来源：https://github.com/anthropics/skills
- 收录内容：`docx`、`pdf`、`pptx`、`xlsx`、`doc-coauthoring`、`skill-creator`、`mcp-builder`、`internal-comms`
- 许可证：Apache License 2.0
- 许可证全文：`third_party/anthropic-skills-LICENSE.txt`
- 版权与第三方声明：见上游仓库的 `THIRD_PARTY_NOTICES.md`
- 修改说明：本仓库未修改其内容，仅为整合安装而复制。

## 2. Alireza Rezvani / claude-skills

- 来源：https://github.com/alirezarezvani/claude-skills
- 收录内容：`plugins/pm-skills`、`plugins/product-skills`
- 许可证：MIT
- 许可证全文：`third_party/alirezarezvani-claude-skills-LICENSE`
- 版权：Copyright (c) Alireza Rezvani
- 修改说明：未修改；仅移除了 `.codex` 镜像目录以减小体积。

## 3. ComposioHQ / awesome-claude-skills

- 来源：https://github.com/ComposioHQ/awesome-claude-skills
- 收录内容：`file-organizer`、`changelog-generator`、`content-research-writer`、`connect-apps`、`meeting-insights-analyzer`
- 许可证：**上游仓库未提供 LICENSE 文件**。本仓库按仓库所有者要求收录，未声明对这些内容享有版权。
- 如权利人对收录有异议，请提出，我们会立即移除。
- 说明：`internal-comms` 采用 Apache 2.0，许可证见该 skill 目录下的 `LICENSE.txt`。

## 4. nimrodfisher / data-analytics-skills

- 来源：https://github.com/nimrodfisher/data-analytics-skills
- 收录内容：`gov-data-quality-audit`、`gov-data-catalog-entry`、`gov-metric-reconciliation` 的模板与脚本结构改编
- 许可证：MIT
- 许可证全文：见各 skill 目录下的 `LICENSE`

## 本仓库原创内容

- 许可证：MIT（见根目录 `LICENSE`）
- 范围：8 个政务数据治理 skill 的原创部分，以及 README、安装脚本、第三方整理说明等。
