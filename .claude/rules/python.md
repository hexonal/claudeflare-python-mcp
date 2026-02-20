---
paths:
  - "**/*.py"
  - "**/pyproject.toml"
  - "**/requirements*.txt"
  - "**/.python-version"
---

# Python 开发规范

## ⚠️ Skill 选择指南

| 任务类型 | 调用 Skill |
|---------|-----------|
| 创建/修改 MCP 工具函数 | `Skill(python-development)` |
| 创建/修改 Handler/处理器 | `Skill(python-development)` |
| 修改 pyproject.toml | `Skill(python-development)` |
| 其他 Python 代码 | `Skill(python-development)` |

⚠️ **编码前必须根据任务类型调用对应 Skill！**
❌ 跳过 = 代码审查不通过

## 强制规则
- 函数 ≤ 50 行，文件 ≤ 500 行
- Python 3.13，无需 `from __future__ import annotations`，类型别名用 `type X = ...`
- 所有函数必须有类型注解（`mypy --strict` 通过），禁止 `Any`、`Optional`、`List`、`Dict`（用原生语法替代）
- 注释独立成行，禁止行尾注释
- 公共函数必须有 docstring（中英双语）

## 包管理
- 使用 `uv` / `uvx` 作为包管理器
- 依赖声明在 `pyproject.toml`，不使用 `requirements.txt`
- 开发依赖放在 `[project.optional-dependencies]` 的 `dev` 组

## 代码质量
```bash
# 格式化（行长 100）
black --line-length 100 .
isort .

# 类型检查（严格模式）
mypy --strict .

# 运行测试
pytest
```

## FastMCP 工具规范
- 所有工具函数使用 `async def` + `@mcp.tool()` 装饰器
- 返回类型统一为 `str`（JSON 字符串）
- 响应格式：`{"status": "success"|"error", "message": "...", "data": [...]}`
- SDK 调用逻辑集中在 Handler 类，工具函数只做编排
