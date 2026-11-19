# 插件包

本目录包含两个可安装的 Claude Code 插件：

| 插件 | 版本 | 内容 |
|---|---|---|
| `pm-skills` | 2.14.6 | 9 个项目管理 skill + 编排器 agent + Atlassian MCP |
| `product-skills` | 2.14.11 | 14 个产品 skill + 编排器 agent + discovery hook |

## 安装

在仓库根目录运行：

```powershell
.\install-plugins.ps1
```

或手动执行：

```powershell
claude plugin marketplace add .\plugins
claude plugin install pm-skills@gov-skill-bundle -y
claude plugin install product-skills@gov-skill-bundle -y
```

安装后重启 Claude Code。

## 说明

- 来源与许可证见仓库根目录 `THIRD_PARTY_NOTICES.md`
- `pm-skills` 自带 Atlassian Remote MCP；首次使用 Jira/Confluence 需要 OAuth 授权
- 插件脚本大部分为标准库；部分需要 `pandas`、`pyarrow`
- 插件中的命令、agent 和 MCP 配置会随插件一起加载
