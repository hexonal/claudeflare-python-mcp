# 全局规则

## 核心规范
- 方法行数 ≤ 50 行
- 方法参数 ≤ 4 个
- 注释独立成行，禁止行尾注释

## MCP 工具

| 工具 | 用途 | 使用场景 |
|------|------|---------|
| context7 | 官方文档查询 | 查询 FastMCP、Cloudflare SDK 等官方文档 |
| deepwiki | 技术知识查询 | 查询开源库、技术方案 |
| sequential-thinking | 复杂问题分析 | 架构设计、调试、多步骤分析 |
| git-config | Git 用户信息 | 自动填充 @author |
| mcp-datetime | 时间戳生成 | 自动填充 @date |

## Skill 触发规则

⚠️ **编码前必须根据文件类型调用对应 Skill！**

各语言的 Skill 选择指南：
- **Python**: 见 `python.md` 的 Skill 选择指南（自动触发 `python-development`）
- **Git 操作**: 需用户说出触发词，见 `git.md`

❌ 跳过 Skill = 代码审查不通过
